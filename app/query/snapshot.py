"""Precomputed full-market screener snapshot builder and fast reader.

Stores fully-enriched security rows (market cap, returns, technicals, F&O metrics,
ownership, fundamentals, sector/sub-sector benchmarks, Quant Special scores) inside
`screener_snapshot` + `screener_snapshot_meta` so `GET /api/screener/dataset`
never runs per-request analytics queries.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import threading
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import duckdb

from app import config, db
from app.query.db_store import load_market_dataset_from_db

log = logging.getLogger(__name__)

_SNAPSHOT_BUILD_LOCK = threading.Lock()

CORE_IDENTITY_FIELDS = frozenset({
    "security_id",
    "nse_symbol",
    "bse_code",
    "isin",
    "name",
    "sector",
    "sub_sector",
    "industry",
    "amfi_category",
    "amfi_avg_mcap_crs",
    "fno_eligible",
    "is_etf",
    "_provenance",
})


def _sanitize(val: Any) -> Any:
    """Recursively converts NaN/Inf/Decimal/date into strict RFC-8259 JSON values."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return None if (math.isnan(val) or math.isinf(val)) else val
    if isinstance(val, Decimal):
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, dict):
        return {str(k): _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(x) for x in val]
    return val


def _json_dumps_strict(obj: Any) -> str:
    return json.dumps(_sanitize(obj), allow_nan=False, separators=(",", ":"), default=str)


def _unsynced_payload() -> Dict[str, Any]:
    return {
        "synced": False,
        "as_of": {},
        "universes": {},
        "rows": [],
        "row_count": 0,
        "total_market_count": 0,
        "etag": None,
        "version": 0,
        "snapshot_built_at": None,
    }


def _sidecar_path():
    return config.data_path("cache/screener_snapshot_latest.json")


def _slice_dataset(
    all_rows: List[Dict[str, Any]],
    universes: Dict[str, List[str]],
    as_of: Dict[str, Any],
    base_etag: str,
    snap_version: int,
    built_at: str,
    total_row_count: int,
    universe: Optional[str],
    fields: Optional[str],
) -> Dict[str, Any]:
    requested_slugs = [s.strip().upper() for s in (universe or "").split(",") if s.strip()]
    out_rows = all_rows
    if requested_slugs and "ALL" not in requested_slugs:
        sym_set: set[str] = set()
        for slug in requested_slugs:
            sym_set.update(universes.get(slug) or [])
        out_rows = [r for r in all_rows if (r.get("nse_symbol") or "") in sym_set]

    requested_fields: Optional[set[str]] = None
    if fields and fields.strip():
        fset = {f.strip() for f in fields.split(",") if f.strip()}
        if fset:
            requested_fields = CORE_IDENTITY_FIELDS | fset
            out_rows = [{k: v for k, v in r.items() if k in requested_fields} for r in out_rows]

    if requested_slugs or requested_fields is not None:
        q_hash = hashlib.sha1(
            f"{','.join(sorted(requested_slugs))}|{','.join(sorted(requested_fields or []))}".encode("utf-8")
        ).hexdigest()[:10]
        etag = f'"{base_etag}-{q_hash}"'
    else:
        etag = f'"{base_etag}"'

    return {
        "synced": True,
        "as_of": as_of,
        "universes": universes,
        "rows": out_rows,
        "row_count": len(out_rows),
        "total_market_count": int(total_row_count),
        "etag": etag,
        "version": int(snap_version or 1),
        "snapshot_built_at": built_at,
    }


def _load_sidecar_snapshot(*, universe: Optional[str] = None, fields: Optional[str] = None) -> Dict[str, Any]:
    try:
        p = _sidecar_path()
        if not p.exists():
            return _unsynced_payload()
        doc = json.loads(p.read_text(encoding="utf-8"))
        if not doc.get("synced") or not doc.get("rows"):
            return _unsynced_payload()
        return _slice_dataset(
            doc["rows"],
            doc.get("universes") or {},
            doc.get("as_of") or {},
            str(doc.get("base_etag") or "sidecar"),
            int(doc.get("version") or 1),
            str(doc.get("snapshot_built_at") or ""),
            int(doc.get("total_market_count") or len(doc["rows"])),
            universe,
            fields,
        )
    except Exception:
        return _unsynced_payload()


def build_screener_snapshot(con=None) -> Dict[str, Any]:
    """Computes full market dataset in bulk and materializes it into `screener_snapshot` atomically."""
    with _SNAPSHOT_BUILD_LOCK:
        own = con is None
        con = con or db.connect()
        db.init_schema(con)
        try:
            ds = load_market_dataset_from_db(con)
            rows = ds.get("rows") or []
            universes = ds.get("universes") or {}
            as_of = ds.get("as_of") or {}
            synced = bool(ds.get("synced"))
            built_at = datetime.now(timezone.utc).replace(tzinfo=None)

            hasher = hashlib.sha256()
            hasher.update(_json_dumps_strict(as_of).encode("utf-8"))
            hasher.update(_json_dumps_strict(universes).encode("utf-8"))

            records: List[tuple] = []
            for idx, row in enumerate(rows):
                prov = row.get("_provenance")
                metrics_only = {k: v for k, v in row.items() if k != "_provenance"}
                m_json = _json_dumps_strict(metrics_only)
                p_json = _json_dumps_strict(prov) if prov is not None else None
                sec_id = str(row.get("security_id") or row.get("nse_symbol") or row.get("isin") or f"row_{idx}")
                nse_sym = row.get("nse_symbol")
                hasher.update(sec_id.encode("utf-8"))
                hasher.update(m_json.encode("utf-8"))
                records.append((sec_id, nse_sym, m_json, p_json, built_at))

            etag = hasher.hexdigest()[:24]
            u_json = _json_dumps_strict(universes)
            a_json = _json_dumps_strict(as_of)

            prev_v_row = con.execute("SELECT version FROM screener_snapshot_meta WHERE id = 'latest' LIMIT 1").fetchone()
            next_version = int((prev_v_row[0] or 0) + 1) if prev_v_row else 1

            con.execute("BEGIN TRANSACTION")
            try:
                con.execute("DELETE FROM screener_snapshot")
                if records:
                    con.executemany(
                        """
                        INSERT INTO screener_snapshot (security_id, nse_symbol, metrics_json, provenance_json, built_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        records,
                    )
                con.execute(
                    """
                    INSERT OR REPLACE INTO screener_snapshot_meta
                        (id, synced, row_count, etag, universes_json, as_of_json, version, built_at)
                    VALUES ('latest', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [synced, len(records), etag, u_json, a_json, next_version, built_at],
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise

            # Atomic sidecar JSON so UI remains served cleanly even while an external CLI sync locks DuckDB
            try:
                sp = _sidecar_path()
                sp.parent.mkdir(parents=True, exist_ok=True)
                tmp_sp = sp.with_suffix(".tmp")
                sidecar_doc = {
                    "synced": synced,
                    "as_of": as_of,
                    "universes": universes,
                    "base_etag": etag,
                    "version": next_version,
                    "total_market_count": len(records),
                    "snapshot_built_at": built_at.isoformat(),
                    "rows": rows,
                }
                tmp_sp.write_text(_json_dumps_strict(sidecar_doc), encoding="utf-8")
                os.replace(tmp_sp, sp)
            except Exception:
                pass

            return {
                "status": "ok",
                "synced": synced,
                "row_count": len(records),
                "etag": etag,
                "version": next_version,
                "built_at": built_at.isoformat(),
            }
        finally:
            if own:
                con.close()


def load_snapshot_from_db(
    con=None,
    *,
    universe: Optional[str] = None,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    """Reads precomputed dataset from `screener_snapshot` with optional universe/field slicing."""
    own = con is None
    if own:
        db_rel = config.settings()["data"]["db_path"]
        db_path = config.data_path(db_rel)
        if not db_path.exists():
            return _unsynced_payload()
        try:
            con = duckdb.connect(str(db_path), read_only=True)
        except duckdb.ConnectionException:
            # In single-process server mode while a background job writes RW, reuse RW connection cleanly
            try:
                con = db.connect(retries=5, delay=0.2)
            except Exception:
                return _load_sidecar_snapshot(universe=universe, fields=fields)
        except duckdb.IOException:
            return _load_sidecar_snapshot(universe=universe, fields=fields)

    try:
        try:
            meta = con.execute(
                """
                SELECT synced, row_count, etag, universes_json, as_of_json, COALESCE(version, 1), built_at
                FROM screener_snapshot_meta
                WHERE id = 'latest'
                LIMIT 1
                """
            ).fetchone()
        except duckdb.CatalogException:
            meta = None

        # Self-heal once cleanly if ref_security was populated directly without build_screener_snapshot()
        if meta is None:
            try:
                sec_cnt = int(con.execute("SELECT COUNT(*) FROM ref_security").fetchone()[0])
            except Exception:
                sec_cnt = 0
            if sec_cnt == 0:
                return _unsynced_payload()
            if own:
                con.close()
                con = None
                try:
                    rw = db.connect()
                    try:
                        build_screener_snapshot(rw)
                    finally:
                        rw.close()
                    con = duckdb.connect(str(db_path), read_only=True)
                except duckdb.IOException:
                    return _unsynced_payload()
            else:
                db.init_schema(con)
                build_screener_snapshot(con)
            meta = con.execute(
                """
                SELECT synced, row_count, etag, universes_json, as_of_json, COALESCE(version, 1), built_at
                FROM screener_snapshot_meta
                WHERE id = 'latest'
                LIMIT 1
                """
            ).fetchone()
            if meta is None:
                return _unsynced_payload()

        synced, total_row_count, base_etag, u_json, a_json, snap_version, built_at = meta
        if not synced or int(total_row_count) == 0:
            return _unsynced_payload()

        universes: Dict[str, List[str]] = json.loads(u_json) if u_json else {}
        as_of: Dict[str, Any] = json.loads(a_json) if a_json else {}

        # Optional comma-separated universe filter pushed cleanly to SQL
        requested_slugs = [s.strip().upper() for s in (universe or "").split(",") if s.strip()]
        symbol_filter: Optional[List[str]] = None
        if requested_slugs and "ALL" not in requested_slugs:
            sym_set: set[str] = set()
            for slug in requested_slugs:
                sym_set.update(universes.get(slug) or [])
            symbol_filter = sorted(sym_set)
            if not symbol_filter:
                sub_tag = hashlib.sha1(f"{base_etag}:{universe}:{fields}".encode("utf-8")).hexdigest()[:12]
                return {
                    "synced": True,
                    "as_of": as_of,
                    "universes": universes,
                    "rows": [],
                    "row_count": 0,
                    "total_market_count": int(total_row_count),
                    "etag": f'"{base_etag}-{sub_tag}"',
                    "version": int(snap_version or 1),
                    "snapshot_built_at": str(built_at),
                }

        if symbol_filter is not None:
            placeholders = ",".join("?" for _ in symbol_filter)
            raw_rows = con.execute(
                f"SELECT metrics_json, provenance_json FROM screener_snapshot WHERE nse_symbol IN ({placeholders})",
                symbol_filter,
            ).fetchall()
        else:
            raw_rows = con.execute("SELECT metrics_json, provenance_json FROM screener_snapshot").fetchall()

        requested_fields: Optional[set[str]] = None
        if fields and fields.strip():
            fset = {f.strip() for f in fields.split(",") if f.strip()}
            if fset:
                requested_fields = CORE_IDENTITY_FIELDS | fset

        out_rows: List[Dict[str, Any]] = []
        loads = json.loads
        for m_json, p_json in raw_rows:
            row = loads(m_json)
            if p_json:
                row["_provenance"] = loads(p_json)
            if requested_fields is not None:
                row = {k: v for k, v in row.items() if k in requested_fields}
            out_rows.append(row)

        if requested_slugs or requested_fields is not None:
            q_hash = hashlib.sha1(f"{','.join(sorted(requested_slugs))}|{','.join(sorted(requested_fields or []))}".encode("utf-8")).hexdigest()[:10]
            etag = f'"{base_etag}-{q_hash}"'
        else:
            etag = f'"{base_etag}"'

        return {
            "synced": True,
            "as_of": as_of,
            "universes": universes,
            "rows": out_rows,
            "row_count": len(out_rows),
            "total_market_count": int(total_row_count),
            "etag": etag,
            "version": int(snap_version or 1),
            "snapshot_built_at": str(built_at),
        }
    except duckdb.IOException:
        return _unsynced_payload()
    finally:
        if own and con is not None:
            con.close()
