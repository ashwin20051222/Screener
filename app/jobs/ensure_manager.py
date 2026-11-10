"""On-demand filter dependency planner, single-flight job worker, and auto-recompute engine.

When a user selects a filter in Add Filters:
1. Checks registry capability metadata & current DB/snapshot coverage.
2. Immediately computes derived values if raw tables already hold sufficient data
   (technical indicators from px_daily, F&O metrics from fno_daily, snapshot rebuild).
3. Queues/deduplicates a persistent background sync job in `data_jobs` (using a
   single-threaded executor so DuckDB write locks never collide), honoring polite
   exchange rate limits (`>= 5s` NSE interval) and stopping cleanly on 403/429.
4. Atomically rebuilds `screener_snapshot` (bumping `version` & `etag`) on finish so
   the UI auto-refreshes table values without removing/re-adding the filter.
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app import db
from app.query.snapshot import build_screener_snapshot
from app.registry.capabilities import load_registry_filters
from scripts.coverage import compute_coverage_report, write_coverage_and_missing_reports

log = logging.getLogger(__name__)


class _DaemonWorker:
    """Single-flight daemon background queue so jobs never collide on DuckDB locks or hang exit."""

    def __init__(self) -> None:
        self._q: "queue.Queue[tuple[Any, tuple[Any, ...], dict[str, Any]]]" = queue.Queue()
        self._started = False
        self._lock = threading.Lock()

    def _run_loop(self) -> None:
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except Exception:
                log.exception("Daemon worker item failed")
            finally:
                self._q.task_done()

    def submit(self, fn, *args, **kwargs) -> None:
        with self._lock:
            if not self._started:
                t = threading.Thread(target=self._run_loop, name="screener-ensure", daemon=True)
                t.start()
                self._started = True
        self._q.put((fn, args, kwargs))


_EXECUTOR = _DaemonWorker()
_PLAN_LOCK = threading.Lock()


def _upsert_job(con, row: Dict[str, Any]) -> None:
    db.upsert_rows(con, "data_jobs", [row], keys=["job_id"])


def get_job(job_id: str, con=None) -> Optional[Dict[str, Any]]:
    own = con is None
    con = con or db.connect()
    try:
        db.init_schema(con)
        r = con.execute(
            """
            SELECT job_id, sync_job, filter_ids_json, universe, status, processed, total,
                   progress_pct, message, error, snapshot_version, started_at, updated_at, finished_at
            FROM data_jobs
            WHERE job_id = ?
            """,
            [job_id],
        ).fetchone()
        if not r:
            return None
        return {
            "job_id": r[0],
            "sync_job": r[1],
            "filter_ids": json.loads(r[2]) if r[2] else [],
            "universe": r[3],
            "status": r[4],
            "processed": int(r[5] or 0),
            "total": int(r[6] or 0),
            "progress_pct": float(r[7] or 0.0),
            "message": r[8],
            "error": r[9],
            "snapshot_version": int(r[10]) if r[10] is not None else None,
            "started_at": r[11].isoformat() if r[11] else None,
            "updated_at": r[12].isoformat() if r[12] else None,
            "finished_at": r[13].isoformat() if r[13] else None,
        }
    finally:
        if own:
            con.close()


def list_jobs(con=None, limit: int = 20) -> List[Dict[str, Any]]:
    own = con is None
    con = con or db.connect()
    try:
        db.init_schema(con)
        rows = con.execute(
            """
            SELECT job_id, sync_job, filter_ids_json, universe, status, processed, total,
                   progress_pct, message, error, snapshot_version, started_at, updated_at, finished_at
            FROM data_jobs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            [max(1, limit)],
        ).fetchall()
        return [
            {
                "job_id": r[0],
                "sync_job": r[1],
                "filter_ids": json.loads(r[2]) if r[2] else [],
                "universe": r[3],
                "status": r[4],
                "processed": int(r[5] or 0),
                "total": int(r[6] or 0),
                "progress_pct": float(r[7] or 0.0),
                "message": r[8],
                "error": r[9],
                "snapshot_version": int(r[10]) if r[10] is not None else None,
                "started_at": r[11].isoformat() if r[11] else None,
                "updated_at": r[12].isoformat() if r[12] else None,
                "finished_at": r[13].isoformat() if r[13] else None,
            }
            for r in rows
        ]
    finally:
        if own:
            con.close()


def _try_instant_derived_recompute(con, requested_jobs: set[str]) -> bool:
    """Checks if raw data already sits in DB without materialized derived columns; computes immediately."""
    changed = False
    try:
        if requested_jobs & {"history_backfill", "technicals"}:
            px_max = con.execute("SELECT MAX(date) FROM px_daily WHERE source != 'NSE-INDEX'").fetchone()[0]
            tech_max = con.execute("SELECT MAX(date) FROM tech_daily").fetchone()[0]
            if px_max and (tech_max is None or tech_max < px_max):
                from ingest.technicals_job import run_technicals_job
                run_technicals_job(con, incremental=True)
                changed = True

        if requested_jobs & {"fno_daily", "manual_mibor"}:
            fo_max = con.execute("SELECT MAX(date) FROM fno_daily WHERE source = 'NSE'").fetchone()[0]
            fm_max = con.execute("SELECT MAX(date) FROM fno_metrics_daily").fetchone()[0]
            if fo_max and (fm_max is None or fm_max < fo_max):
                from ingest.fno_metrics import compute_fno_metrics_for_date
                compute_fno_metrics_for_date(con, fo_max)
                changed = True

        if "xbrl_financials" in requested_jobs:
            fin_cnt = int(
                con.execute(
                    "SELECT COUNT(*) FROM fin_annual WHERE (period_months IS NOT NULL AND period_months < 10) OR parser_version IS NULL"
                ).fetchone()[0] or 0
            )
            if fin_cnt > 0:
                from ingest.financials import reingest_cached_xbrl_files
                reingest_cached_xbrl_files(con)
                changed = True

        if "amfi_etf" in requested_jobs:
            etf_nav_cnt = int(con.execute("SELECT COUNT(*) FROM etf_nav_daily").fetchone()[0] or 0)
            if etf_nav_cnt > 0:
                from ingest.etf import sync_etf_tracking_errors
                res_te = sync_etf_tracking_errors(con)
                if int(res_te.get("updated", 0)) > 0:
                    changed = True

        if changed:
            build_screener_snapshot(con)
    except Exception as exc:
        log.warning("Instant derived recompute warning: %s", exc)
    return changed


def _execute_sync_job(
    job_id: str,
    sync_job: str,
    filter_ids: List[str],
    universe: Optional[str],
    min_hist_needed: int,
) -> None:
    """Runs inside single-threaded background executor and persists progress cleanly in DuckDB."""
    con = db.connect()
    db.init_schema(con)
    started_at = datetime.now()
    target_u = "nifty100"
    if universe and universe.strip().upper() not in ("", "ALL"):
        target_u = universe.split(",")[0].strip().lower()

    def _progress(proc: int, tot: int, msg: str) -> None:
        pct = round((proc / tot) * 100.0, 1) if tot > 0 else 0.0
        _upsert_job(con, {
            "job_id": job_id,
            "sync_job": sync_job,
            "filter_ids_json": json.dumps(filter_ids),
            "universe": universe or "ALL",
            "status": "running",
            "processed": int(proc),
            "total": int(tot),
            "progress_pct": pct,
            "message": msg[:350],
            "error": None,
            "snapshot_version": None,
            "started_at": started_at,
            "updated_at": datetime.now(),
            "finished_at": None,
        })

    _progress(0, 1, f"Starting {sync_job} sync...")

    final_status = "completed"
    final_msg = "Completed"
    final_err = None
    snap_ver = None
    proc_cnt = 1
    tot_cnt = 1

    try:
        from ingest import sources as src_mod
        from ingest import nse as nse_mod

        if sync_job == "weekly_master":
            res = src_mod.run_weekly(con)
            final_msg = f"Masters refreshed (eq/sme/etf/fno/amfi)"
        elif sync_job == "daily_bhav":
            res = src_mod.run_daily(con)
            final_msg = "Daily CM/F&O bhavcopy & PR MCAP synced"
        elif sync_job in ("history_backfill", "technicals"):
            from ingest.backfill import backfill_prices
            need = max(35, min_hist_needed or 255)
            # Cap single interactive network burst cleanly so requests stay polite & responsive
            res = backfill_prices(
                con,
                trading_days=need,
                fo_days=0,
                resume=True,
                sync_actions=False,
                run_technicals=True,
                max_network_fetches=25,
                progress_cb=_progress,
            )
            proc_cnt = int(res.get("cm_days_ready") or 0)
            tot_cnt = need
            if res.get("blocked"):
                final_status = "blocked"
                final_err = "NSE returned 403/429 during history backfill. Retry later or place CM bhavcopy ZIPs in data/inbox/."
                final_msg = final_err
            elif res.get("budget_reached") and proc_cnt < tot_cnt:
                final_status = "partial"
                final_msg = f"Backfilled batch ({proc_cnt}/{tot_cnt} trading days in DB); click Retry to continue resumable history"
            else:
                final_msg = f"History ready ({proc_cnt} days synced) and technicals computed"
        elif sync_job == "xbrl_financials":
            from ingest.financials import reingest_cached_xbrl_files
            reingest_cached_xbrl_files(con)
            res = src_mod.run_quarterly(
                con,
                universe=target_u,
                max_symbols=12,
                resume=True,
                include_shp=False,
                include_fin=True,
                progress_cb=_progress,
            )
            proc_cnt = int(res.get("fin_synced") or 0) + int(res.get("skipped_resume") or 0)
            tot_cnt = max(1, proc_cnt)
            if res.get("blocked"):
                final_status = "blocked"
                final_err = "NSE returned 403/429 during Ind-AS XBRL fetch. Place XBRL XMLs in data/inbox/ or retry later."
                final_msg = final_err
            else:
                final_msg = f"Ind-AS XBRL batch completed ({res.get('fin_synced', 0)} symbols fetched, {res.get('skipped_resume', 0)} already synced)"
        elif sync_job == "shp_ownership":
            res = src_mod.run_quarterly(
                con,
                universe=target_u,
                max_symbols=12,
                resume=True,
                include_shp=True,
                include_fin=False,
                progress_cb=_progress,
            )
            proc_cnt = int(res.get("shp_synced") or 0) + int(res.get("skipped_resume") or 0)
            tot_cnt = max(1, proc_cnt)
            if res.get("blocked"):
                final_status = "blocked"
                final_err = "NSE returned 403/429 during SHP XBRL fetch. Place SHP XMLs in data/inbox/ or retry later."
                final_msg = final_err
            else:
                final_msg = f"SHP batch completed ({res.get('shp_synced', 0)} symbols fetched)"
        elif sync_job == "deals_insider":
            from ingest import ownership as own_mod
            d_res = own_mod.sync_bulk_block_deals(con)
            i_res = own_mod.sync_insider_trades(con, days_back=180)
            if "blocked" in (d_res.get("status"), i_res.get("status")):
                final_status = "blocked"
                final_err = "NSE returned 403/429 for Deals/PIT disclosures."
                final_msg = final_err
            else:
                final_msg = f"Deals ({d_res.get('rows', 0)}) & PIT insider ({i_res.get('rows', 0)}) synced"
        elif sync_job == "fno_daily":
            nse_mod.sync_fno_lots(con)
            from ingest.backfill import backfill_prices
            fo_res = backfill_prices(con, trading_days=1, fo_days=5, sync_actions=False, run_technicals=False)
            from ingest.fno_metrics import compute_fno_metrics_for_date
            fm = compute_fno_metrics_for_date(con)
            if fo_res.get("blocked"):
                final_status = "blocked"
                final_err = "NSE returned 403/429 on F&O Bhavcopy fetch."
                final_msg = final_err
            else:
                final_msg = f"F&O metrics ready ({fm.get('symbols', 0)} F&O stocks)"
        elif sync_job == "amfi_etf":
            nse_mod.sync_etf_master(con)
            from ingest.etf import sync_amfi_nav, sync_etf_tracking_errors
            nav_res = sync_amfi_nav(con)
            te_res = sync_etf_tracking_errors(con)
            final_msg = f"ETF master + AMFI NAV ({nav_res.get('rows', 0)}) + TE updated ({te_res.get('updated', 0)})"
        elif sync_job == "manual_mibor":
            from ingest import fbil as fbil_mod
            from ingest.fno_metrics import compute_fno_metrics_for_date
            fb = fbil_mod.sync_manual_rate(con)
            fm = compute_fno_metrics_for_date(con)
            final_msg = f"MIBOR ({fb.get('status', 'ok')}) + F&O fair value ({fm.get('symbols', 0)} F&O stocks)"

        snap = build_screener_snapshot(con)
        snap_ver = snap.get("version")
        try:
            write_coverage_and_missing_reports(con)
        except Exception:
            pass
    except Exception as exc:
        log.exception("Background ensure job %s (%s) failed", job_id, sync_job)
        final_status = "error"
        final_err = f"{type(exc).__name__}: {exc}"
        final_msg = final_err
    finally:
        pct = 100.0 if final_status in ("completed", "partial") and proc_cnt >= tot_cnt else (
            round((proc_cnt / tot_cnt) * 100.0, 1) if tot_cnt > 0 else 0.0
        )
        _upsert_job(con, {
            "job_id": job_id,
            "sync_job": sync_job,
            "filter_ids_json": json.dumps(filter_ids),
            "universe": universe or "ALL",
            "status": final_status,
            "processed": proc_cnt,
            "total": tot_cnt,
            "progress_pct": pct,
            "message": final_msg[:350],
            "error": final_err[:350] if final_err else None,
            "snapshot_version": snap_ver,
            "started_at": started_at,
            "updated_at": datetime.now(),
            "finished_at": datetime.now(),
        })
        con.close()


def ensure_filters(
    filter_ids: List[str],
    *,
    universe: Optional[str] = None,
    wait: bool = False,
) -> Dict[str, Any]:
    """Evaluates filter readiness and guarantees immediate compute OR background sync job."""
    reg = load_registry_filters()
    clean_ids = list(dict.fromkeys(fid.strip() for fid in filter_ids if fid and fid.strip()))

    with _PLAN_LOCK:
        con = db.connect()
        try:
            db.init_schema(con)
            needed_jobs = {str(reg[fid]["sync_job"]) for fid in clean_ids if fid in reg}
            recomputed = _try_instant_derived_recompute(con, needed_jobs)
            cov = compute_coverage_report(universe=universe, con=con)
            cov_by_id = cov["by_id"]

            results: List[Dict[str, Any]] = []
            jobs_to_run: Dict[str, List[str]] = {}
            max_hist_by_job: Dict[str, int] = {}

            for fid in clean_ids:
                if fid not in reg:
                    results.append({"filter_id": fid, "state": "unknown", "reason": "Not in registry"})
                    continue
                entry = cov_by_id.get(fid, {})
                ui_status = entry.get("status") or "awaiting_sync"
                sync_job = entry.get("sync_job") or "unavailable"
                min_h = int(entry.get("min_history_days") or 0)

                if ui_status in ("unavailable", "not_applicable", "available"):
                    results.append({
                        "filter_id": fid,
                        "state": ui_status,
                        "eligible_count": entry.get("eligible_count", 0),
                        "populated_count": entry.get("populated_count", 0),
                        "reason": entry.get("status_reason", ""),
                        "job_id": None,
                    })
                    continue

                if fid == "expense_ratio" and ui_status == "manual_required":
                    results.append({
                        "filter_id": fid,
                        "state": "manual_required",
                        "eligible_count": entry.get("eligible_count", 0),
                        "populated_count": entry.get("populated_count", 0),
                        "reason": entry.get("status_reason", ""),
                        "job_id": None,
                    })
                    continue

                jobs_to_run.setdefault(sync_job, []).append(fid)
                max_hist_by_job[sync_job] = max(max_hist_by_job.get(sync_job, 0), min_h)

            created_or_active_jobs: List[Dict[str, Any]] = []
            job_id_by_sync: Dict[str, str] = {}

            for sync_job, fids_for_job in jobs_to_run.items():
                if sync_job == "unavailable":
                    continue
                existing = con.execute(
                    """
                    SELECT job_id
                    FROM data_jobs
                    WHERE sync_job = ?
                      AND COALESCE(universe, 'ALL') = ?
                      AND status IN ('queued', 'running')
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    [sync_job, universe or "ALL"],
                ).fetchone()
                if existing:
                    jid = existing[0]
                    job_obj = get_job(jid, con=con)
                    if job_obj:
                        created_or_active_jobs.append(job_obj)
                    job_id_by_sync[sync_job] = jid
                    continue

                jid = f"job_{sync_job}_{uuid.uuid4().hex[:10]}"
                now_ts = datetime.now()
                job_row = {
                    "job_id": jid,
                    "sync_job": sync_job,
                    "filter_ids_json": json.dumps(fids_for_job),
                    "universe": universe or "ALL",
                    "status": "queued",
                    "processed": 0,
                    "total": 1,
                    "progress_pct": 0.0,
                    "message": f"Queued {sync_job} sync for {', '.join(fids_for_job[:4])}",
                    "error": None,
                    "snapshot_version": cov.get("snapshot_version"),
                    "started_at": now_ts,
                    "updated_at": now_ts,
                    "finished_at": None,
                }
                _upsert_job(con, job_row)
                job_id_by_sync[sync_job] = jid
                job_obj = get_job(jid, con=con)
                if job_obj:
                    created_or_active_jobs.append(job_obj)

                # Submit to background executor (unless synchronous wait mode requested by tests)
                if not wait:
                    _EXECUTOR.submit(
                        _execute_sync_job,
                        jid,
                        sync_job,
                        fids_for_job,
                        universe,
                        max_hist_by_job.get(sync_job, 0),
                    )

            for sync_job, fids_for_job in jobs_to_run.items():
                jid = job_id_by_sync.get(sync_job)
                for fid in fids_for_job:
                    entry = cov_by_id.get(fid, {})
                    results.append({
                        "filter_id": fid,
                        "state": "queued" if jid else entry.get("status", "awaiting_sync"),
                        "sync_job": sync_job,
                        "eligible_count": entry.get("eligible_count", 0),
                        "populated_count": entry.get("populated_count", 0),
                        "reason": entry.get("status_reason", ""),
                        "job_id": jid,
                    })
        finally:
            con.close()

    if wait and created_or_active_jobs:
        for job_obj in created_or_active_jobs:
            if job_obj["status"] == "queued":
                _execute_sync_job(
                    job_obj["job_id"],
                    job_obj["sync_job"],
                    job_obj["filter_ids"],
                    universe,
                    max_hist_by_job.get(job_obj["sync_job"], 0),
                )
        updated_jobs = [get_job(j["job_id"]) for j in created_or_active_jobs]
        cov = compute_coverage_report(universe=universe)
        return {
            "filters": results,
            "jobs": [j for j in updated_jobs if j],
            "recomputed": recomputed,
            "snapshot_version": cov.get("snapshot_version"),
        }

    return {
        "filters": results,
        "jobs": created_or_active_jobs,
        "recomputed": recomputed,
        "snapshot_version": cov.get("snapshot_version"),
    }


def rebuild_all() -> Dict[str, Any]:
    """Recomputes derived tables (technicals, F&O metrics, ETF TE, cached XBRLs) and rebuilds snapshot atomically."""
    con = db.connect()
    try:
        db.init_schema(con)
        from ingest.financials import reingest_cached_xbrl_files
        from ingest.fno_metrics import compute_fno_metrics_for_date
        from ingest.technicals_job import run_technicals_job
        from ingest.etf import sync_etf_tracking_errors

        reingest_cached_xbrl_files(con)
        tech_res = run_technicals_job(con, incremental=True)
        fno_res = compute_fno_metrics_for_date(con)
        te_res = sync_etf_tracking_errors(con)
        snap = build_screener_snapshot(con)
        write_coverage_and_missing_reports(con)
        return {
            "status": "ok",
            "snapshot": snap,
            "technicals": tech_res,
            "fno_metrics": fno_res,
            "etf_tracking_error": te_res,
        }
    finally:
        con.close()
