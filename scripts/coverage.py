#!/usr/bin/env python3
"""Measure honest per-filter coverage & missing-symbol diagnostics across all 255 filters.

Outputs:
- `docs/DATA_COVERAGE.md` (universe, feed, eligibility-aware per-filter percentages, sector distribution)
- `docs/DATA_MISSING_SYMBOLS.md` (exact missing symbols per domain, last progress status & remediation)
- JSON coverage summary used by `GET /api/coverage` and the Add Filters UI status pills.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.registry.capabilities import load_registry_filters  # noqa: E402
from app.query.snapshot import load_snapshot_from_db  # noqa: E402


def _pct(count: int, total: int) -> float:
    return round((count / total) * 100.0, 1) if total > 0 else 0.0


def _is_row_financial(row: Dict[str, Any], fin_flags: Dict[str, bool]) -> bool:
    sym = str(row.get("nse_symbol") or "")
    if sym in fin_flags:
        return fin_flags[sym]
    prov = row.get("_provenance") or {}
    if prov.get("financial_template") in {"banks", "insurers"}:
        return True
    return str(row.get("sector") or "") == "Financials"


def _row_is_eligible(row: Dict[str, Any], fdef: Dict[str, Any], fin_flags: Dict[str, bool]) -> bool:
    inst_types = set(fdef.get("instrument_types") or ["equity"])
    is_etf = bool(row.get("is_etf"))
    is_fno = bool(row.get("fno_eligible"))

    if inst_types == {"etf"}:
        if not is_etf:
            return False
    elif inst_types == {"fno_equity"}:
        if not is_fno or is_etf:
            return False
    elif inst_types == {"equity"}:
        if is_etf:
            return False
    # {"equity", "etf"} includes both

    sec_scope = str(fdef.get("applicable_sectors") or "all")
    if sec_scope == "financial_only" and not _is_row_financial(row, fin_flags):
        return False
    if sec_scope == "non_financial_only" and _is_row_financial(row, fin_flags):
        return False
    return True


def _load_runtime_meta(con=None) -> Dict[str, Any]:
    """Reads financial institution flags, active/latest data_jobs, inbox flags, and px days cleanly."""
    meta: Dict[str, Any] = {
        "fin_flags": {},
        "jobs_by_sync": {},
        "blocked_feeds": set(),
        "max_px_days": 0,
        "ter_count": 0,
        "mibor_count": 0,
    }
    own = con is None
    try:
        if own:
            from app import config
            import duckdb

            db_p = config.data_path(config.settings()["data"]["db_path"])
            if not db_p.exists():
                return meta
            try:
                con = duckdb.connect(str(db_p), read_only=True)
            except Exception:
                from app import db
                con = db.connect()

        for sym, is_fi in con.execute(
            "SELECT nse_symbol, COALESCE(is_financial_institution, FALSE) FROM ref_security WHERE nse_symbol IS NOT NULL"
        ).fetchall():
            meta["fin_flags"][sym] = bool(is_fi)

        px_days_row = con.execute(
            "SELECT COALESCE(MAX(cnt), 0) FROM (SELECT COUNT(DISTINCT date) AS cnt FROM px_daily WHERE source != 'NSE-INDEX' GROUP BY symbol)"
        ).fetchone()
        meta["max_px_days"] = int(px_days_row[0] or 0) if px_days_row else 0

        try:
            meta["ter_count"] = int(
                con.execute("SELECT COUNT(*) FROM etf_meta WHERE expense_ratio IS NOT NULL").fetchone()[0] or 0
            )
            meta["mibor_count"] = int(con.execute("SELECT COUNT(*) FROM ref_fbil_mibor").fetchone()[0] or 0)
        except Exception:
            pass

        try:
            job_rows = con.execute(
                """
                SELECT job_id, sync_job, filter_ids_json, universe, status, processed, total,
                       progress_pct, message, error, snapshot_version, updated_at
                FROM data_jobs
                ORDER BY updated_at DESC
                LIMIT 50
                """
            ).fetchall()
            for r in job_rows:
                s_job = r[1]
                cur = meta["jobs_by_sync"].get(s_job)
                if cur is None or (r[4] in ("queued", "running") and cur["status"] not in ("queued", "running")):
                    import json as _json
                    fids_j = _json.loads(r[2]) if r[2] else []
                    meta["jobs_by_sync"][s_job] = {
                        "job_id": r[0],
                        "sync_job": s_job,
                        "filter_ids": fids_j,
                        "status": r[4],
                        "processed": int(r[5] or 0),
                        "total": int(r[6] or 0),
                        "progress_pct": float(r[7] or 0.0),
                        "message": r[8],
                        "error": r[9],
                        "snapshot_version": r[10],
                    }
        except Exception:
            pass
    except Exception:
        pass
    finally:
        if own and con is not None:
            con.close()
    return meta


def compute_coverage_report(
    dataset: Dict[str, Any] | None = None,
    *,
    universe: Optional[str] = None,
    con=None,
) -> Dict[str, Any]:
    """Computes per-filter non-null & eligible coverage against a market dataset dict."""
    filters = load_registry_filters()

    if dataset is None:
        dataset = load_snapshot_from_db(con=con)

    all_rows: List[Dict[str, Any]] = dataset.get("rows") or []
    universes: Dict[str, List[str]] = dataset.get("universes") or {}
    nifty100_syms = set(universes.get("NIFTY100") or [])
    nifty100_rows = [r for r in all_rows if (r.get("nse_symbol") or "") in nifty100_syms]

    if universe and universe.strip().upper() != "ALL":
        slugs = [s.strip().upper() for s in universe.split(",") if s.strip()]
        target_syms: set[str] = set()
        for sl in slugs:
            target_syms.update(universes.get(sl) or [])
        target_rows = [r for r in all_rows if (r.get("nse_symbol") or "") in target_syms]
        universe_label = ",".join(slugs)
    else:
        target_rows = all_rows
        universe_label = "ALL"

    rt = _load_runtime_meta(con=con)
    fin_flags = rt["fin_flags"]
    max_px_days = max(rt["max_px_days"], int((dataset.get("as_of") or {}).get("max_px_days") or 0))
    jobs_by_sync = rt["jobs_by_sync"]

    n_all = len(all_rows)
    n_100 = len(nifty100_rows)
    n_target = len(target_rows)

    entries: List[Dict[str, Any]] = []
    by_feed: Dict[str, Dict[str, int]] = {}
    by_id: Dict[str, Dict[str, Any]] = {}

    for fid, fdef in filters.items():
        cnt_all = sum(1 for r in all_rows if r.get(fid) is not None)
        cnt_100 = sum(1 for r in nifty100_rows if r.get(fid) is not None)
        elig_rows = [r for r in target_rows if _row_is_eligible(r, fdef, fin_flags)]
        cnt_elig = len(elig_rows)
        cnt_pop = sum(1 for r in elig_rows if r.get(fid) is not None)

        feed = str(fdef.get("feeds") or "unavailable")
        sync_job = str(fdef.get("sync_job") or "unavailable")
        min_hist = int(fdef.get("min_history_days") or 0)
        job_info = jobs_by_sync.get(sync_job)

        by_feed.setdefault(feed, {"filters": 0, "populated_any": 0})
        by_feed[feed]["filters"] += 1
        if cnt_all > 0:
            by_feed[feed]["populated_any"] += 1

        # Determine honest UI status pill
        status_reason = ""
        is_job_for_this = bool(
            job_info and (fid in (job_info.get("filter_ids") or []) or cnt_pop < cnt_elig)
        )
        if feed == "unavailable" or sync_job == "unavailable":
            ui_status = "unavailable"
            status_reason = str(fdef.get("primary_source") or "Requires licensed analyst consensus vendor")
        elif n_target > 0 and cnt_elig == 0:
            ui_status = "not_applicable"
            inst = ", ".join(fdef.get("instrument_types") or [])
            sec_scope = fdef.get("applicable_sectors")
            status_reason = f"Applies only to {inst}" + (f" ({sec_scope})" if sec_scope != "all" else "")
        elif cnt_elig > 0 and cnt_pop == cnt_elig:
            ui_status = "available"
            status_reason = f"{cnt_pop}/{cnt_elig} eligible populated"
        elif job_info and job_info["status"] in ("queued", "running") and is_job_for_this:
            ui_status = job_info["status"]
            status_reason = job_info.get("message") or "Synchronizing in background..."
        elif job_info and job_info["status"] == "blocked" and is_job_for_this:
            ui_status = "blocked"
            status_reason = job_info.get("error") or "Exchange host rate-limited (HTTP 403/429); retry later or use data/inbox/"
        elif min_hist > 1 and max_px_days < min_hist:
            ui_status = "insufficient_history"
            status_reason = f"Requires {min_hist} trading days; DB currently has {max_px_days} days"
        elif fid == "expense_ratio" and cnt_pop == 0 and rt["ter_count"] == 0:
            ui_status = "manual_required"
            status_reason = "Drop AMFI Monthly TER CSV (TER_*.csv) into data/inbox/ and run Rebuild"
        elif cnt_pop > 0:
            ui_status = "partial"
            status_reason = f"{cnt_pop}/{cnt_elig} eligible populated"
        else:
            ui_status = "awaiting_sync"
            status_reason = f"0/{cnt_elig} populated; check filter or sync {fdef.get('primary_source')}"

        entry = {
            "id": fid,
            "name": str(fdef.get("name") or fid),
            "category": str(fdef.get("category") or ""),
            "availability": str(fdef.get("availability") or ""),
            "feeds": feed,
            "sync_job": sync_job,
            "instrument_types": list(fdef.get("instrument_types") or ["equity"]),
            "applicable_sectors": str(fdef.get("applicable_sectors") or "all"),
            "primary_source": str(fdef.get("primary_source") or ""),
            "refresh_cadence": str(fdef.get("refresh_cadence") or ""),
            "freshness_sla": str(fdef.get("freshness_sla") or ""),
            "lookback_periods": str(fdef.get("lookback_periods") or ""),
            "min_history_days": min_hist,
            "all_non_null": cnt_all,
            "all_pct": _pct(cnt_all, n_all),
            "nifty100_non_null": cnt_100,
            "nifty100_pct": _pct(cnt_100, n_100),
            "eligible_count": cnt_elig,
            "populated_count": cnt_pop,
            "coverage_pct": _pct(cnt_pop, cnt_elig),
            "status": ui_status,
            "status_reason": status_reason,
            "active_job": job_info if (job_info and job_info["status"] in ("queued", "running", "blocked")) else None,
        }
        entries.append(entry)
        by_id[fid] = entry

    by_sector: Dict[str, Dict[str, int]] = {}
    for r in all_rows:
        sec = str(r.get("sector") or "Unclassified")
        by_sector.setdefault(sec, {"all": 0, "nifty100": 0})
        by_sector[sec]["all"] += 1
    for r in nifty100_rows:
        sec = str(r.get("sector") or "Unclassified")
        by_sector.setdefault(sec, {"all": 0, "nifty100": 0})
        by_sector[sec]["nifty100"] += 1

    unmapped_industries: List[Dict[str, Any]] = []
    try:
        from app import config as _cfg
        import duckdb as _ddb
        db_p = _cfg.data_path(_cfg.settings()["data"]["db_path"])
        if db_p.exists():
            _con = _ddb.connect(str(db_p), read_only=True)
            try:
                from ingest.master_enrichment import get_unmapped_industries
                unmapped_industries = get_unmapped_industries(_con)
            finally:
                _con.close()
    except Exception:
        pass

    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "synced": bool(dataset.get("synced")),
        "universe": universe_label,
        "universe_rows": n_target,
        "total_rows": n_all,
        "nifty100_rows": n_100,
        "max_px_days": max_px_days,
        "snapshot_version": dataset.get("version"),
        "universes": {k: len(v) for k, v in sorted(universes.items())},
        "by_feed": dict(sorted(by_feed.items())),
        "by_sector": dict(sorted(by_sector.items(), key=lambda kv: (-kv[1]["all"], kv[0]))),
        "unmapped_industries": unmapped_industries,
        "filters": entries,
        "by_id": by_id,
    }


def compute_missing_symbols_report(con=None) -> Dict[str, Any]:
    """Inspects DuckDB tables and classifies missing symbols + failure causes honestly."""
    from app import config, db
    import duckdb

    own = con is None
    if own:
        db_p = config.data_path(config.settings()["data"]["db_path"])
        if not db_p.exists():
            return {"generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "sections": []}
        try:
            con = duckdb.connect(str(db_p), read_only=True)
        except Exception:
            con = db.connect()

    try:
        sections: Dict[str, List[Dict[str, Any]]] = {}

        # Latest progress checkpoint failures per symbol
        prog_fail: Dict[tuple[str, str], str] = {}
        try:
            for job, key, status, msg in con.execute(
                "SELECT job, item_key, status, COALESCE(message, '') FROM ingest_progress WHERE status != 'ok'"
            ).fetchall():
                prog_fail[(str(job), str(key))] = f"{status}: {msg}"
        except Exception:
            pass

        # 1. NIFTY 100 missing Ind-AS annual financials
        n100_syms = [
            r[0]
            for r in con.execute(
                "SELECT DISTINCT symbol FROM ref_index_constituent WHERE index_name = 'NIFTY100' ORDER BY symbol"
            ).fetchall()
        ]
        have_ann = {
            r[0]
            for r in con.execute(
                "SELECT DISTINCT symbol FROM fin_annual WHERE period_months IS NULL OR period_months >= 10"
            ).fetchall()
        }
        have_shp = {
            r[0]
            for r in con.execute("SELECT DISTINCT symbol FROM ownership_quarterly").fetchall()
        }

        sections["nifty100_missing_annual_xbrl"] = [
            {
                "symbol": s,
                "reason": prog_fail.get(("quarterly", s)) or prog_fail.get(("quarterly_fin", s)) or "Not yet synced / no annual Ind-AS filing ingested",
                "remediation": "Trigger filter check on any Valuation/Financial filter or run `make sync-quarterly UNIVERSE=nifty100`",
            }
            for s in n100_syms
            if s not in have_ann
        ]

        sections["nifty100_missing_shp"] = [
            {
                "symbol": s,
                "reason": prog_fail.get(("quarterly", s)) or prog_fail.get(("quarterly_shp", s)) or "Shareholding Pattern XBRL not yet synced",
                "remediation": "Trigger any Ownership filter or run `make sync-shp UNIVERSE=nifty100`",
            }
            for s in n100_syms
            if s not in have_shp
        ]

        # 2. Listed equities missing shares_outstanding
        miss_sh = con.execute(
            """
            SELECT nse_symbol
            FROM ref_security
            WHERE listing_status = 'listed' AND COALESCE(is_etf, FALSE) = FALSE
              AND (shares_outstanding IS NULL OR shares_outstanding <= 0)
            ORDER BY nse_symbol
            LIMIT 250
            """
        ).fetchall()
        sections["equities_missing_shares_outstanding"] = [
            {
                "symbol": r[0],
                "reason": "Neither NSE PR MCAP nor Ind-AS/SHP XBRL supplied shares_outstanding yet",
                "remediation": "Run `make sync-daily` (PR MCAP) or quarterly XBRL sync",
            }
            for r in miss_sh
            if r[0]
        ]

        # 3. F&O eligible missing latest fno_daily
        max_fo_dt = con.execute("SELECT MAX(date) FROM fno_daily").fetchone()[0]
        fno_miss = con.execute(
            """
            SELECT r.nse_symbol
            FROM ref_security r
            WHERE COALESCE(r.fno_eligible, FALSE) = TRUE
              AND r.nse_symbol NOT IN (SELECT DISTINCT underlying FROM fno_daily WHERE date = ?)
            ORDER BY r.nse_symbol
            """,
            [max_fo_dt] if max_fo_dt else [datetime(1900, 1, 1).date()],
        ).fetchall()
        sections["fno_missing_daily_contracts"] = [
            {
                "symbol": r[0],
                "reason": f"Missing F&O UDiFF rows as of {max_fo_dt or 'never synced'}",
                "remediation": "Run `make sync-daily` or check F&O filter",
            }
            for r in fno_miss
            if r[0]
        ]

        # 4. ETFs missing TER / Tracking Error
        etf_miss = con.execute(
            """
            SELECT r.nse_symbol, m.scheme_code, m.expense_ratio, m.tracking_error
            FROM ref_security r
            LEFT JOIN etf_meta m ON r.nse_symbol = m.symbol
            WHERE COALESCE(r.is_etf, FALSE) = TRUE
              AND (m.expense_ratio IS NULL OR m.tracking_error IS NULL)
            ORDER BY r.nse_symbol
            LIMIT 200
            """
        ).fetchall()
        sections["etfs_missing_ter_or_tracking_error"] = [
            {
                "symbol": sym,
                "reason": (
                    f"Missing {'TER' if ter is None else ''}{' & ' if (ter is None and te is None) else ''}{'Tracking Error (<20 matched AMFI NAV days)' if te is None else ''}"
                ),
                "remediation": "Place AMFI Monthly TER CSV in data/inbox/TER_*.csv and build >= 20d NAV + NIFTY50 history",
            }
            for sym, _sc, ter, te in etf_miss
            if sym
        ]

        return {
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "nifty100_count": len(n100_syms),
            "sections": sections,
        }
    finally:
        if own and con is not None:
            con.close()


def render_missing_symbols_markdown(diag: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# DATA_MISSING_SYMBOLS.md — Missing Symbols & Remediation Log",
        "",
        f"> **Generated:** `{diag['generated_at']}`",
        "> Honest classification of symbols without data per domain, cause, and legitimate remediation.",
        "",
    ]
    sections: Dict[str, List[Dict[str, Any]]] = diag.get("sections") or {}
    titles = {
        "nifty100_missing_annual_xbrl": "1. NIFTY 100 Missing Ind-AS Annual XBRL",
        "nifty100_missing_shp": "2. NIFTY 100 Missing Shareholding Pattern XBRL",
        "equities_missing_shares_outstanding": "3. Listed Equities Missing Shares Outstanding (First 250)",
        "fno_missing_daily_contracts": "4. F&O Eligible Symbols Missing Latest Derivatives Snapshot",
        "etfs_missing_ter_or_tracking_error": "5. Listed ETFs Missing Expense Ratio (TER) or Tracking Error",
    }
    for key, title in titles.items():
        items = sections.get(key) or []
        lines.extend([f"## {title} (`{len(items)}`)", ""])
        if not items:
            lines.append("_None missing._\n")
            continue
        lines.append("| Symbol | Cause | Remediation |")
        lines.append("|---|---|---|")
        for it in items[:150]:
            lines.append(f"| `{it['symbol']}` | {it['reason']} | {it['remediation']} |")
        if len(items) > 150:
            lines.append(f"| ... | `{len(items) - 150}` additional symbols omitted | See DB query |")
        lines.append("")
    return "\n".join(lines)


def render_markdown(report: Dict[str, Any]) -> str:
    """Formats the coverage report as Markdown for docs/DATA_COVERAGE.md."""
    lines: List[str] = [
        "# DATA_COVERAGE.md — Live Database Filter Coverage",
        "",
        f"> **Generated:** `{report['generated_at']}`",
        f"> **Database Synced:** `{report['synced']}` | **All Listed Rows:** `{report['total_rows']}` | **NIFTY100 Rows:** `{report['nifty100_rows']}` | **Max Price History:** `{report.get('max_px_days', 0)}` trading days",
        f"> **Registry Filters Checked:** `{len(report['filters'])}`",
        "",
        "## 1. Index Universes Loaded",
        "",
    ]
    if report["universes"]:
        lines.append("| Index Slug | Member Count |")
        lines.append("|---|---|")
        for idx_name, cnt in report["universes"].items():
            lines.append(f"| `{idx_name}` | {cnt} |")
    else:
        lines.append("_No index universes loaded yet (`ref_index_constituent` is empty). Run `make sync-weekly`._")

    lines.extend([
        "",
        "## 2. Coverage Summary by Feeding Job (`feeds`)",
        "",
        "| Feeds Job | Filter Count | Filters With >= 1 Value |",
        "|---|---|---|",
    ])
    for feed, stats in report["by_feed"].items():
        lines.append(f"| `{feed}` | {stats['filters']} | {stats['populated_any']} |")

    lines.extend([
        "",
        "## 3. Per-Filter Non-Null & Eligible Coverage",
        "",
        "| Filter ID | Name | Category | Status | Feeds | Eligible (`ALL`) | All Non-Null | Eligible % | NIFTY100 Non-Null | NIFTY100 % |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for e in report["filters"]:
        lines.append(
            f"| `{e['id']}` | {e['name']} | {e['category']} | `{e['status']}` | `{e['feeds']}` | "
            f"{e['eligible_count']} | {e['all_non_null']} | {e['coverage_pct']:.1f}% | {e['nifty100_non_null']} | {e['nifty100_pct']:.1f}% |"
        )
    lines.extend([
        "",
        "## 4. Sector Distribution & Unmapped Industry Log",
        "",
        "| UI Sector | All Rows | NIFTY100 Rows |",
        "|---|---|---|",
    ])
    for sec, counts in (report.get("by_sector") or {}).items():
        lines.append(f"| {sec} | {counts['all']} | {counts['nifty100']} |")

    unmapped = report.get("unmapped_industries") or []
    lines.extend(["", "### Unmapped Official Exchange Industries", ""])
    if unmapped:
        lines.append("| Official Industry Label | Security Count |")
        lines.append("|---|---|")
        for u in unmapped:
            lines.append(f"| `{u['industry']}` | {u['count']} |")
    else:
        lines.append("_All official exchange industry labels present in DB are mapped cleanly in `config/sector_map.yaml`._")
    lines.append("")
    return "\n".join(lines)


def write_coverage_and_missing_reports(con=None) -> Dict[str, Any]:
    """Helper called after sync/rebuild jobs to regenerate both Markdown diagnostics."""
    rep = compute_coverage_report(con=con)
    miss = compute_missing_symbols_report(con=con)
    cov_path = ROOT / "docs" / "DATA_COVERAGE.md"
    miss_path = ROOT / "docs" / "DATA_MISSING_SYMBOLS.md"
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    cov_path.write_text(render_markdown(rep), encoding="utf-8")
    miss_path.write_text(render_missing_symbols_markdown(miss), encoding="utf-8")
    return {"coverage": rep, "missing": miss}


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Measure per-filter data coverage in DuckDB.")
    parser.add_argument("--out", default=str(ROOT / "docs" / "DATA_COVERAGE.md"), help="Markdown output path")
    parser.add_argument("--missing-out", default=str(ROOT / "docs" / "DATA_MISSING_SYMBOLS.md"), help="Missing symbols Markdown path")
    parser.add_argument("--no-write", action="store_true", help="Print summary only without writing Markdown files")
    args = parser.parse_args(argv)

    rep = compute_coverage_report()
    md = render_markdown(rep)
    miss = compute_missing_symbols_report()
    miss_md = render_missing_symbols_markdown(miss)
    if not args.no_write:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md, encoding="utf-8")
        mp = Path(args.missing_out)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(miss_md, encoding="utf-8")

    try:
        print(f"Synced: {rep['synced']} | All rows: {rep['total_rows']} | NIFTY100 rows: {rep['nifty100_rows']} | Max px days: {rep.get('max_px_days', 0)}")
        print(f"{'Filter ID':38s} {'Status':20s} {'Feeds':11s} {'All':>12s} {'NIFTY100':>12s}")
        print("-" * 97)
        for e in rep["filters"]:
            all_col = f"{e['all_non_null']} ({e['coverage_pct']:.1f}%)"
            n100_col = f"{e['nifty100_non_null']} ({e['nifty100_pct']:.1f}%)"
            print(f"{e['id']:38s} {e['status']:20s} {e['feeds']:11s} {all_col:>12s} {n100_col:>12s}")
        if not args.no_write:
            print(f"\nSaved coverage report to {args.out}")
            print(f"Saved missing symbols report to {args.missing_out}")
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
