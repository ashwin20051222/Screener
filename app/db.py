"""DuckDB access layer: connection factory, schema init, idempotent upserts."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterable

import duckdb

from app import config
from app.config import settings

log = logging.getLogger(__name__)


def connect(*, read_only: bool = False, retries: int = 4, delay: float = 0.35) -> duckdb.DuckDBPyConnection:
    """Open the screener DB.

    DuckDB allows a single process to hold the file; while `sync_daily`/`sync_weekly`
    owns it, other processes momentarily cannot attach. Retry briefly for the tiny
    windows between sync steps; callers that still fail should degrade gracefully
    (see app.main which renders 'sync in progress' badges instead of crashing).
    """
    db_path = config.data_path(settings()["data"]["db_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    last_exc: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            return duckdb.connect(str(db_path), read_only=read_only)
        except duckdb.IOException as exc:  # file locked by an active sync process
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    schema_sql_path = Path(__file__).with_name("schema.sql")
    con.execute(schema_sql_path.read_text(encoding="utf-8"))
    # Forward-compatible idempotent column migrations for existing DB files
    for col_def in (
        "shares_outstanding BIGINT",
        "shares_source VARCHAR",
        "shares_as_of DATE",
        "sector VARCHAR",
        "sub_sector VARCHAR",
        "industry VARCHAR",
        "financial_template VARCHAR DEFAULT 'industrials'",
        "is_financial_institution BOOLEAN DEFAULT FALSE",
    ):
        con.execute(f"ALTER TABLE ref_security ADD COLUMN IF NOT EXISTS {col_def}")
    for col_def in ("filing_url VARCHAR", "filing_date DATE", "parser_version VARCHAR"):
        con.execute(f"ALTER TABLE fin_annual ADD COLUMN IF NOT EXISTS {col_def}")
        con.execute(f"ALTER TABLE fin_quarterly ADD COLUMN IF NOT EXISTS {col_def}")
    con.execute("ALTER TABLE screener_snapshot_meta ADD COLUMN IF NOT EXISTS version BIGINT DEFAULT 1")
    # Clean legacy bug where 3M/6M/9M quarterly filings were inserted into fin_annual
    try:
        con.execute("DELETE FROM fin_annual WHERE period_months IS NOT NULL AND period_months < 10")
    except Exception:
        pass


def _q(name: str) -> str:
    """Quote an identifier (works with lowercase schema identifiers incl. reserved words)."""
    return '"' + name.replace('"', '""') + '"'


def _target_column_types(con: duckdb.DuckDBPyConnection, table: str,
                         cols: list[str]) -> dict[str, str]:
    """Map col -> DuckDB type of the TARGET table (staging must match its types)."""
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?",
        [table],
    ).fetchall()
    types = {c.lower(): t for c, t in rows}
    return {c: types[c.lower()] for c in cols if c.lower() in types}


def _create_stage(con: duckdb.DuckDBPyConnection, cols: list[str], types: dict[str, str]) -> None:
    """TEMP TABLE `stage` pre-typed to the target's column types (all rows NULL)."""
    select = ", ".join(
        f"NULL::{types[c]} AS {_q(c)}" if c in types else f"NULL::VARCHAR AS {_q(c)}"
        for c in cols
    )
    con.execute(f"CREATE OR REPLACE TEMP TABLE stage AS SELECT {select} WHERE 1 = 0")


def _apply_stage(con: duckdb.DuckDBPyConnection, table: str, keys: list[str],
                 return_count: int) -> int:
    """DELETE target keys present in stage, INSERT stage rows; one transaction, then drop."""
    key_sql = ", ".join(_q(k) for k in keys)
    con.execute("BEGIN TRANSACTION")
    try:
        con.execute(
            f"DELETE FROM {table} WHERE ({key_sql}) IN (SELECT {key_sql} FROM stage)"
        )
        insert_cols = ", ".join(_q(c) for c in _stage_cols(con))
        con.execute(f"INSERT INTO {table} ({insert_cols}) SELECT {insert_cols} FROM stage")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.execute("DROP TABLE IF EXISTS stage")
    return return_count


def _stage_cols(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'stage' ORDER BY ordinal_position").fetchall()]


def upsert_rows(
    con: duckdb.DuckDBPyConnection,
    table: str,
    rows: Iterable[dict],
    keys: list[str],
) -> int:
    """Idempotent upsert (row dicts). Rows with PK values already present replace old rows.

    Implementation: temp `stage` table typed to the target -> DELETE target WHERE pk IN stage
    -> INSERT SELECT. One transaction: a failure leaves the target untouched.
    """
    rows = [dict(r) for r in rows]
    if not rows:
        log.info("upsert_rows(%s): nothing to write", table)
        return 0
    cols = list(dict.fromkeys(k for r in rows for k in r.keys()))
    types = _target_column_types(con, table, cols)
    _create_stage(con, cols, types)
    placeholders = ", ".join(["?"] * len(cols))
    con.executemany(
        f"INSERT INTO stage ({', '.join(_q(c) for c in cols)}) VALUES ({placeholders})",
        [[r.get(c) for c in cols] for r in rows],
    )
    return _apply_stage(con, table, keys, len(rows))


def merge_rows(
    con: duckdb.DuckDBPyConnection,
    table: str,
    rows: Iterable[dict],
    keys: list[str],
    *,
    preserve_existing: set[str] | None = None,
) -> int:
    """Non-destructive upsert: merges non-NULL incoming values without wiping existing columns.

    Ideal for `ref_security` when secondary feeds (BSE bhavcopy, ETF list, SME list)
    supply partial columns by ISIN/security_id without overwriting `nse_symbol`,
    `shares_outstanding`, `sector`, `fno_eligible`, or `is_etf`.
    """
    raw_rows = [dict(r) for r in rows]
    if not raw_rows:
        log.info("merge_rows(%s): nothing to write", table)
        return 0

    # Deduplicate batch in memory by composite key, merging non-None fields cleanly
    dedup: dict[tuple, dict] = {}
    for r in raw_rows:
        k_tup = tuple(r.get(k) for k in keys)
        if any(x is None for x in k_tup):
            continue
        cur = dedup.get(k_tup)
        if cur is None:
            dedup[k_tup] = dict(r)
        else:
            for col, val in r.items():
                if val is not None:
                    cur[col] = val
    merged_list = list(dedup.values())
    if not merged_list:
        return 0

    cols = list(dict.fromkeys(c for r in merged_list for c in r.keys()))
    types = _target_column_types(con, table, cols)
    _create_stage(con, cols, types)
    placeholders = ", ".join(["?"] * len(cols))
    con.executemany(
        f"INSERT INTO stage ({', '.join(_q(c) for c in cols)}) VALUES ({placeholders})",
        [[r.get(c) for c in cols] for r in merged_list],
    )

    preserve = preserve_existing or set()
    non_key_cols = [c for c in cols if c not in keys]
    target_all_cols = {
        r[0].lower()
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]
        ).fetchall()
    }
    join_sql = " AND ".join(f"tgt.{_q(k)} = src.{_q(k)}" for k in keys)
    set_parts = []
    for c in non_key_cols:
        qc = _q(c)
        if c in preserve:
            set_parts.append(f"{qc} = COALESCE(tgt.{qc}, src.{qc})")
        else:
            set_parts.append(f"{qc} = COALESCE(src.{qc}, tgt.{qc})")
    if "updated_at" in target_all_cols and "updated_at" not in non_key_cols:
        set_parts.append("updated_at = current_timestamp")

    col_list_sql = ", ".join(_q(c) for c in cols)
    src_col_list_sql = ", ".join(f"src.{_q(c)}" for c in cols)
    con.execute("BEGIN TRANSACTION")
    try:
        if set_parts:
            con.execute(
                f"UPDATE {table} AS tgt SET {', '.join(set_parts)} FROM stage AS src WHERE {join_sql}"
            )
        con.execute(
            f"""
            INSERT INTO {table} ({col_list_sql})
            SELECT {src_col_list_sql}
            FROM stage AS src
            WHERE NOT EXISTS (SELECT 1 FROM {table} AS tgt WHERE {join_sql})
            """
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.execute("DROP TABLE IF EXISTS stage")
    return len(merged_list)


def upsert_df(
    con: duckdb.DuckDBPyConnection,
    table: str,
    df,
    keys: list[str],
) -> int:
    """Idempotent upsert for a pandas DataFrame (NaN/NaT normalized to NULL, types cast)."""
    import pandas as pd

    if df is None or len(df) == 0:
        log.info("upsert_df(%s): nothing to write", table)
        return 0
    df = df.astype(object).where(pd.notna(df), None)
    cols = list(df.columns)
    types = _target_column_types(con, table, cols)
    select = ", ".join(
        f"CAST({_q(c)} AS {types[c]}) AS {_q(c)}" if c in types else _q(c)
        for c in cols
    )
    con.register("stage_df", df)
    try:
        con.execute(f"CREATE OR REPLACE TEMP TABLE stage AS SELECT {select} FROM stage_df")
    finally:
        con.unregister("stage_df")
    return _apply_stage(con, table, keys, len(df))


def mark_progress(con: duckdb.DuckDBPyConnection, job: str, item_key: str, status: str, message: str = "") -> None:
    """Idempotently records checkpoint state for resumable long-running jobs."""
    from datetime import datetime
    upsert_rows(
        con,
        "ingest_progress",
        [{
            "job": job,
            "item_key": str(item_key),
            "status": status,
            "message": (message or "")[:400],
            "updated_at": datetime.now(),
        }],
        keys=["job", "item_key"],
    )


def get_progress_keys(con: duckdb.DuckDBPyConnection, job: str, statuses: tuple[str, ...] = ("ok", "holiday", "skip")) -> set[str]:
    """Returns set of item_keys already completed for a resumable job."""
    try:
        placeholders = ", ".join(["?"] * len(statuses))
        rows = con.execute(
            f"SELECT item_key FROM ingest_progress WHERE job = ? AND status IN ({placeholders})",
            [job, *statuses],
        ).fetchall()
        return {str(r[0]) for r in rows}
    except Exception:
        return set()
