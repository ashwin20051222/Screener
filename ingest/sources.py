"""Source orchestrator: daily + weekly jobs; every run writes ingest_status (traceability)."""
from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

from app import db
from app.config import data_path, settings
from ingest import amfi as amfi_mod
from ingest import bse as bse_mod
from ingest import fbil as fbil_mod
from ingest import nse as nse_mod
from ingest.inbox import process_inbox

log = logging.getLogger(__name__)


def _mark(con, job: str, run_date: date, status: str, rows: int = 0, message: str = "",
          started_at: float = 0.0):
    db.upsert_rows(con, "ingest_status", [{
        "id": f"{job}::{run_date}",
        "job": job,
        "run_date": run_date,
        "status": status,
        "rows": rows,
        "message": message[:500],
        "started_at": datetime.fromtimestamp(started_at) if started_at else None,
        "finished_at": datetime.now(),
    }], keys=["id"])


def _latest_stored_px_date(con, source: str) -> date | None:
    r = con.execute("SELECT max(date) FROM px_daily WHERE source = ?", [source]).fetchone()
    return r[0] if r and r[0] else None


def run_daily(con=None) -> dict:
    """Daily EOD job: previous published bhavcopies (walk back until fresh), NSE corp actions."""
    t0 = time.time()
    own = con is None
    con = con or db.connect()
    db.init_schema(con)
    run_date = date.today()
    summary = {}

    try:
        for source, sync_cm, sync_fo in ((nse_mod, nse_mod.sync_cm_bhavcopy, nse_mod.sync_fo_bhavcopy),
                                         (bse_mod, bse_mod.sync_cm_bhavcopy, None)):
            name = source.__name__.split(".")[-1]
            target = run_date - timedelta(days=1)
            # walk back to the first missing published file (weekends/holidays return 404)
            for i in range(int(settings()["ingest"]["backfill_lookback_business_days"]) + 1):
                d = target - timedelta(days=i)
                stored = _latest_stored_px_date(con, source_cm_source(name))
                if stored and stored >= d:
                    summary[name] = {"status": "skip", "message": f"{d} already stored"}
                    break
                res = sync_cm(con, d)
                summary[name] = res
                if res.get("status") == "ok":
                    if sync_fo and name == "nse":
                        summary[name]["fo"] = sync_fo(con, d)
                    if name == "bse":
                        summary[name]["master_fallback"] = bse_mod.sync_master_from_bhavcopy(con)
                    break
                if res.get("status") == "fail":
                    break  # do not hammer a failing host today

        summary["corp_actions"] = nse_mod.sync_corporate_actions(con)
        try:
            summary["pr_mcap"] = nse_mod.sync_nse_pr_mcap(con)
        except Exception as exc:
            summary["pr_mcap_error"] = str(exc)
        try:
            from ingest import ownership as own_mod
            summary["bulk_block_deals"] = own_mod.sync_bulk_block_deals(con)
            summary["insider_trades"] = own_mod.sync_insider_trades(con, days_back=7)
        except Exception as exc:
            summary["deals_pit_error"] = str(exc)
        try:
            from ingest.fno_metrics import compute_fno_metrics_for_date
            from ingest.technicals_job import run_technicals_job
            summary["fno_metrics"] = compute_fno_metrics_for_date(con)
            summary["technicals"] = run_technicals_job(con)
        except Exception as exc:
            summary["compute_error"] = str(exc)
        try:
            from app.query.snapshot import build_screener_snapshot
            summary["snapshot"] = build_screener_snapshot(con)
        except Exception as exc:
            summary["snapshot_error"] = str(exc)
        _mark(con, "daily", run_date, "ok", 0, str(summary)[:400], t0)
    except Exception as e:
        log.exception("daily sync failed")
        _mark(con, "daily", run_date, "fail", 0, f"{type(e).__name__}: {e}", t0)
        summary["error"] = str(e)
    finally:
        if own:
            con.close()
    return summary


def source_cm_source(name: str) -> str:
    return "NSE" if name == "nse" else "BSE"


def run_weekly(con=None) -> dict:
    """Weekly: inbox first (manual drops win), masters, SME master, index lists, F&O lots, AMFI, ETF NAV, FBIL."""
    t0 = time.time()
    own = con is None
    con = con or db.connect()
    db.init_schema(con)
    run_date = date.today()
    summary = {}
    try:
        inbox_res = process_inbox(con)
        summary["inbox"] = inbox_res
        summary["equity_master"] = nse_mod.sync_equity_master(con)
        summary["sme_master"] = nse_mod.sync_sme_master(con)
        summary["etf_master"] = nse_mod.sync_etf_master(con)
        summary["fno_lots"] = nse_mod.sync_fno_lots(con)
        summary["indices"] = nse_mod.sync_index_constituents(con)
        summary["bse_master_from_bhav"] = bse_mod.sync_master_from_bhavcopy(con)
        try:
            from ingest.master_enrichment import enrich_securities_from_constituents
            summary["sector_enrichment"] = enrich_securities_from_constituents(con)
            summary["total_market_industries"] = nse_mod.sync_total_market_industries(con)
        except Exception as exc:
            summary["sector_enrichment_error"] = str(exc)
        summary["amfi"] = amfi_mod.sync_categorisation(con)
        try:
            from ingest.etf import sync_amfi_nav
            summary["etf_nav"] = sync_amfi_nav(con)
        except Exception as exc:
            summary["etf_nav_error"] = str(exc)
        summary["fbil"] = fbil_mod.sync_manual_rate(con)
        try:
            from app.query.snapshot import build_screener_snapshot
            summary["snapshot"] = build_screener_snapshot(con)
        except Exception as exc:
            summary["snapshot_error"] = str(exc)
        _mark(con, "weekly", run_date, "ok", 0, str(summary)[:400], t0)
    except Exception as e:
        log.exception("weekly sync failed")
        _mark(con, "weekly", run_date, "fail", 0, f"{type(e).__name__}: {e}", t0)
        summary["error"] = str(e)
    finally:
        if own:
            con.close()
    return summary


def run_quarterly(
    con=None,
    *,
    universe: str = "nifty100",
    max_symbols: int | None = None,
    resume: bool = True,
) -> dict:
    """Quarterly: Targeted resumable SHP (3 quarters) + Ind-AS XBRL (6Y annual, 4Q quarterly)."""
    t0 = time.time()
    own = con is None
    con = con or db.connect()
    db.init_schema(con)
    run_date = date.today()
    summary = {
        "status": "ok",
        "universe": universe,
        "shp_synced": 0,
        "fin_synced": 0,
        "skipped_resume": 0,
        "requests_made": 0,
        "blocked": False,
        "fin_quarantine_count": 0,
    }
    try:
        from ingest.financials import sync_financials_for_symbol
        from ingest.http import bootstrap_nse_session
        from ingest.ownership import ordered_universe_symbols, sync_shareholding_for_symbol

        syms = ordered_universe_symbols(con, universe)
        if max_symbols is not None:
            syms = syms[:max_symbols]

        done_q = db.get_progress_keys(con, "quarterly", statuses=("ok",)) if resume else set()
        session = bootstrap_nse_session()

        for sym in syms:
            if sym in done_q:
                summary["skipped_resume"] += 1
                continue

            r_shp = sync_shareholding_for_symbol(con, sym, max_quarters=3, session=session)
            summary["requests_made"] += 1 + int(r_shp.get("quarters", 0))
            if r_shp.get("status") == "blocked":
                db.mark_progress(con, "quarterly", sym, "fail", r_shp.get("message", "403/429"))
                log.error(
                    "NSE returned 403/429 during SHP sync for %s. Stopping immediately.\n"
                    "Manual fallback: place SHP_<sym>.xml / INDAS_<sym>.xml in data/inbox/ and run `make synkinbox`.",
                    sym,
                )
                summary["blocked"] = True
                summary["status"] = "partial"
                break
            if r_shp.get("quarters", 0) > 0:
                summary["shp_synced"] += 1

            r_fin = sync_financials_for_symbol(con, sym, max_annual=6, max_quarterly=4, session=session, resume=resume)
            summary["requests_made"] += int(r_fin.get("requests", 0))
            if r_fin.get("status") == "blocked":
                db.mark_progress(con, "quarterly", sym, "fail", r_fin.get("message", "403/429"))
                log.error(
                    "NSE returned 403/429 during XBRL financials sync for %s. Stopping immediately.\n"
                    "Manual fallback: drop INDAS_*.xml in data/inbox/ and run `make synkinbox`.",
                    sym,
                )
                summary["blocked"] = True
                summary["status"] = "partial"
                break
            if r_fin.get("filings", 0) > 0:
                summary["fin_synced"] += 1

            db.mark_progress(con, "quarterly", sym, "ok", f"shp={r_shp.get('quarters', 0)},fin={r_fin.get('filings', 0)}")

        q_row = con.execute("SELECT COUNT(*) FROM fin_quarantine").fetchone()
        summary["fin_quarantine_count"] = int(q_row[0]) if q_row else 0
        try:
            from app.query.snapshot import build_screener_snapshot
            summary["snapshot"] = build_screener_snapshot(con)
        except Exception as exc:
            summary["snapshot_error"] = str(exc)
        summary["elapsed_seconds"] = round(time.time() - t0, 2)
        _mark(
            con,
            "quarterly",
            run_date,
            "partial" if summary["blocked"] else "ok",
            summary["shp_synced"] + summary["fin_synced"],
            str(summary)[:400],
            t0,
        )
    except Exception as e:
        log.exception("quarterly sync failed")
        _mark(con, "quarterly", run_date, "fail", 0, f"{type(e).__name__}: {e}", t0)
        summary["error"] = str(e)
        summary["status"] = "fail"
    finally:
        if own:
            con.close()
    return summary


def status_report(con=None) -> dict:
    """What could the UI tell the user right now (source x as-of)?"""
    own = con is None
    con = con or db.connect()
    try:
        px = con.execute(
            "SELECT source, max(date) AS last_px, count(*) FROM px_daily GROUP BY source"
        ).fetchall()
        fno = con.execute("SELECT max(date) FROM fno_daily").fetchone()
        amfi = con.execute("SELECT max(as_of_date) FROM ref_amfi_classification").fetchone()
        corp = con.execute("SELECT max(ex_date) FROM corp_action").fetchone()
        mibor = con.execute("SELECT max(rate_date) FROM ref_fbil_mibor").fetchone()
        secs = con.execute("SELECT count(*), sum(fno_eligible::INT), sum(is_etf::INT), sum(CASE WHEN shares_outstanding > 0 THEN 1 ELSE 0 END) FROM ref_security").fetchone()
        jobs = con.execute(
            "SELECT job, run_date, status, message FROM ingest_status ORDER BY finished_at DESC LIMIT 20"
        ).fetchall()
        quar = con.execute("SELECT count(*) FROM fin_quarantine").fetchone()
        prog_rows = con.execute("SELECT job, status, count(*) FROM ingest_progress GROUP BY job, status ORDER BY job, status").fetchall()
        progress: dict = {}
        for j, st, c in prog_rows:
            progress.setdefault(j, {})[st] = int(c)
        return {
            "px_per_source": [{"source": s, "as_of": str(d), "rows": c} for s, d, c in px],
            "fno_as_of": str(fno[0] or "n/a"),
            "amfi_period": str(amfi[0] or "n/a"),
            "corp_actions_as_of": str(corp[0] or "n/a"),
            "fbil_as_of": str(mibor[0] or "n/a"),
            "securities": {"total": secs[0], "fno_eligible": secs[1], "etf": secs[2], "shares_populated": secs[3]},
            "fin_quarantine_count": int(quar[0]) if quar else 0,
            "progress": progress,
            "recent_jobs": [{"job": j, "on": str(d), "status": st, "msg": m} for j, d, st, m in jobs],
        }
    finally:
        if own:
            con.close()
