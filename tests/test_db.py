"""DuckDB schema + idempotent upsert tests (run against a throwaway DB file, never the real one)."""
from __future__ import annotations

import duckdb
import pytest

from app import db


@pytest.fixture()
def con(tmp_path):
    c = duckdb.connect(str(tmp_path / "test.duckdb"))
    db.init_schema(c)
    yield c
    c.close()


def test_init_schema_creates_all_step2_tables(con):
    have = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables").fetchall()}
    for t in ("ref_security", "ref_index_constituent", "ref_amfi_classification",
              "ref_fno_lot", "ref_fbil_mibor", "px_daily", "fno_daily",
              "corp_action", "raw_files", "ingest_status"):
        assert t in have, f"missing table {t}"


def test_init_schema_is_idempotent(con):
    db.init_schema(con)  # IF NOT EXISTS everywhere -> second call is a no-op
    n = con.execute("SELECT count(*) FROM px_daily").fetchone()[0]
    assert n == 0


def test_upsert_rows_insert_once_and_reinsert_is_idempotent(con):
    rows = [
        {"source": "NSE", "date": __import__("datetime").date(2026, 10, 23),
         "symbol": "20MICRONS", "isin": "INE144J01027", "series": "EQ",
         "open": 178.25, "close": 174.94, "volume": 184221,
         "turnover_rs": 31991242.29, "wap": 173.66},
        {"source": "NSE", "date": __import__("datetime").date(2026, 10, 23),
         "symbol": "RELIANCE", "isin": "INE002A01018", "series": "EQ",
         "close": 2750.0, "volume": 900000, "turnover_rs": 2.5e9},
    ]
    keys = ["source", "symbol", "date", "series"]
    assert db.upsert_rows(con, "px_daily", rows, keys) == 2
    assert db.upsert_rows(con, "px_daily", rows, keys) == 2  # same PKs -> replace, not duplicate
    assert con.execute("SELECT count(*) FROM px_daily").fetchone()[0] == 2
    # re-upsert with a CHANGED value must overwrite the stored row
    rows2 = [dict(rows[0], close=999.0)]
    db.upsert_rows(con, "px_daily", rows2, keys)
    got = con.execute(
        "SELECT close FROM px_daily WHERE symbol='20MICRONS'").fetchone()[0]
    assert got == 999.0


# Note on the fno_daily composite PK (DuckDB PK columns are implicitly NOT NULL):
#   futures store option_type as '' (they have none); parse_udiff produces NULL there, so
#   ingest/nse.py::fo_bhav_from_bytes normalizes to '' before upsert.

def test_upsert_df_normalizes_nan_and_is_idempotent(con):
    import pandas as pd

    df = pd.DataFrame({
        "source": ["NSE", "NSE"],
        "date": [pd.Timestamp("2026-10-23"), pd.Timestamp("2026-10-23")],
        "underlying": ["AAA", "BBB"],
        "expiry": [pd.Timestamp("2026-11-27"), pd.Timestamp("2026-10-27")],
        "instrument": ["STF", "STO"],
        "option_type": ["", "PE"],  # futures carry '' in the PK column (never NULL)
        "strike": [0.0, 425.0],
        "close": [271.45, float("nan")],  # NaN in a non-PK column -> NULL, never 0/garbage
    })
    n = db.upsert_df(con, "fno_daily", df,
                     keys=["source", "underlying", "expiry", "instrument",
                           "option_type", "strike", "date"])
    assert n == 2
    assert db.upsert_df(con, "fno_daily", df,
                        keys=["source", "underlying", "expiry", "instrument",
                              "option_type", "strike", "date"]) == 2
    assert con.execute("SELECT count(*) FROM fno_daily").fetchone()[0] == 2
    null_close = con.execute(
        "SELECT count(*) FROM fno_daily WHERE close IS NULL").fetchone()[0]
    assert null_close == 1  # NaN became NULL (idempotent through the re-upsert)


def test_upsert_rows_empty_input_is_noop(con):
    assert db.upsert_rows(con, "px_daily", [], keys=["source", "symbol", "date", "series"]) == 0
    assert con.execute("SELECT count(*) FROM px_daily").fetchone()[0] == 0


def test_status_report_shapes_snapshot(con):
    from datetime import date

    db.upsert_rows(con, "ingest_status", [{
        "id": "daily::2026-10-25", "job": "daily", "run_date": date(2026, 10, 25),
        "status": "ok", "rows": 3730, "message": "ok",
    }], keys=["id"])
    from ingest import sources

    rep = sources.status_report(con)
    assert rep["recent_jobs"][0]["job"] == "daily"
    assert rep["recent_jobs"][0]["status"] == "ok"
    assert rep["securities"]["total"] == 0  # empty DB reports zeros, never fabricated data
