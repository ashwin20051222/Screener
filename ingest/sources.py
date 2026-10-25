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
    """Weekly: inbox first (manual drops win), masters, index lists, F&O lots, AMFI check, FBIL."""
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
        summary["etf_master"] = nse_mod.sync_etf_master(con)
        summary["fno_lots"] = nse_mod.sync_fno_lots(con)
        summary["indices"] = nse_mod.sync_index_constituents(con)
        summary["bse_master_from_bhav"] = bse_mod.sync_master_from_bhavcopy(con)
        summary["amfi"] = amfi_mod.sync_categorisation(con)
        summary["fbil"] = fbil_mod.sync_manual_rate(con)
        _mark(con, "weekly", run_date, "ok", 0, str(summary)[:400], t0)
    except Exception as e:
        log.exception("weekly sync failed")
        _mark(con, "weekly", run_date, "fail", 0, f"{type(e).__name__}: {e}", t0)
        summary["error"] = str(e)
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
        secs = con.execute("SELECT count(*), sum(fno_eligible::INT), sum(is_etf::INT) FROM ref_security").fetchone()
        jobs = con.execute(
            "SELECT job, run_date, status, message FROM ingest_status ORDER BY finished_at DESC LIMIT 20"
        ).fetchall()
        return {
            "px_per_source": [{"source": s, "as_of": str(d), "rows": c} for s, d, c in px],
            "fno_as_of": str(fno[0] or "n/a"),
            "amfi_period": str(amfi[0] or "n/a"),
            "corp_actions_as_of": str(corp[0] or "n/a"),
            "fbil_as_of": str(mibor[0] or "n/a"),
            "securities": {"total": secs[0], "fno_eligible": secs[1], "etf": secs[2]},
            "recent_jobs": [{"job": j, "on": str(d), "status": st, "msg": m} for j, d, st, m in jobs],
        }
    finally:
        if own:
            con.close()
