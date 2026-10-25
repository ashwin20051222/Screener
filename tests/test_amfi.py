"""AMFI categorisation parsing + period resolution tests (synthetic workbook, read_only mode).

The live file (AverageMarketCapitalization30Jun2026.xlsx, 582 KB, verified 2026-10-25) lists
half-yearly average market caps with ISIN, rank and Large/Mid/Small classification. Our parser
sniffs the header row, so the fixture keeps the same spirit without pinning exact live columns.
"""
from __future__ import annotations

import io
from datetime import date

import openpyxl

from app import db
from ingest import amfi as amfi_mod


def _xlsx_bytes(rows: list[list]) -> bytes:
    buf = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for r in rows:
        ws.append(r)
    wb.save(buf)
    return buf.getvalue()


def _ingest(con, payload: bytes, period: date | None) -> dict:
    return amfi_mod.categorisation_from_bytes(con, payload, period)


def test_parse_period_from_url_variants():
    assert amfi_mod.parse_period_from_url(
        "https://portal.amfiindia.com/spages/AverageMarketCapitalization30Jun2026.xlsx"
    ) == date(2026, 6, 30)
    assert amfi_mod.parse_period_from_url(
        "https://portal.amfiindia.com/spages/AverageMarketCapitalization31Dec2025.xlsx"
    ) == date(2025, 12, 31)
    assert amfi_mod.parse_period_from_url("no-match.xlsx") is None


def test_resolve_latest_xlsx_chooses_newest_link(monkeypatch):
    class FakeResult:
        status = 200
        bytes = (
            "<html><a href='https://portal.amfiindia.com/spages/AverageMarketCapitalization31Dec2024.xlsx'>Dec</a>"
            "<a href='https://portal.amfiindia.com/spages/AverageMarketCapitalization30Jun2026.xlsx'>Jun</a></html>"
        ).encode()

        def ok(self):
            return True

    monkeypatch.setattr(amfi_mod.http, "fetch", lambda *a, **k: FakeResult())
    url = amfi_mod.resolve_latest_xlsx()
    assert url and url.endswith("AverageMarketCapitalization30Jun2026.xlsx")


def test_categorisation_from_bytes_full_flow(tmp_path):
    import duckdb

    con = duckdb.connect(str(tmp_path / "a.duckdb"))
    db.init_schema(con)

    payload = _xlsx_bytes([
        ["Sl. No.", "ISIN", "Name of the company", "Symbol",
         "Average Market Capitalization (Rs Cr)", "Rank", "Classification"],
        [1, "INE002A01018", "RELIANCE INDUSTRIES LTD", "RELIANCE", 2009430.5, 1, "Large"],
        [2, "INE155A01022", "INFY", "INFY", 575000.2, 10, "Large"],
        [3, "INE548A01028", "A MIDE CAP CO", "MIDCO", 70000.0, 150, "Mid"],
        [4, "INE031X01021", "A SMALL CO", "SMOL", 42.0, 890, "Small"],
        [5, "", "blank ISIN row is skipped", "", None, None, None],
    ])
    res = _ingest(con, payload, date(2026, 6, 30))
    assert res["status"] == "ok"
    assert res["rows"] == 4, res

    got = {r[0]: r for r in con.execute(
        "SELECT isin, rank, classification, avg_mcap_crs, as_of_date "
        "FROM ref_amfi_classification").fetchall()}
    assert got["INE002A01018"][1] == 1 and got["INE002A01018"][2] == "Large"
    assert abs(got["INE002A01018"][3] - 2009430.5) < 0.01
    assert got["INE548A01028"][2] == "Mid"
    assert got["INE031X01021"][2] == "Small"
    assert str(got["INE002A01018"][4]) == "2026-06-30"
    con.close()


def test_synch_from_bytes_filename_hint_sets_period(tmp_path):
    import duckdb

    con = duckdb.connect(str(tmp_path / "b.duckdb"))
    db.init_schema(con)
    payload = _xlsx_bytes([
        ["ISIN", "Rank", "Classification"],
        ["INE002A01018", 1, "Large"],
    ])
    res = amfi_mod.sync_categorisation_from_bytes(
        con, payload, "AverageMarketCapitalization30Jun2026.xlsx")
    assert res["status"] == "ok"
    assert res["period"] == "2026-06-30"

    # missing period -> fail cleanly with instructions; nothing undated is ever stored
    res2 = amfi_mod.sync_categorisation_from_bytes(con, payload, "no-hint.xlsx")
    assert res2["status"] == "fail"
    assert "period" in res2["message"].lower()
    assert con.execute("SELECT count(*) FROM ref_amfi_classification").fetchone()[0] == 1
    con.close()


def test_header_not_found_fails_cleanly(tmp_path):
    import duckdb

    con = duckdb.connect(str(tmp_path / "c.duckdb"))
    db.init_schema(con)
    payload = _xlsx_bytes([["col a", "col b"], [1, 2], [3, 4]])
    res = _ingest(con, payload, date(2026, 6, 30))  # valid period -> parser reaches header search
    assert res["status"] == "fail"
    assert "header" in res["message"].lower()
    con.close()
