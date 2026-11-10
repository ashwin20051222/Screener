"""Resumable historical EOD bhavcopy backfill (NSE CM + 10D F&O + corporate actions + technicals)."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from app import db
from app.config import data_path, endpoints, settings
from ingest import http
from ingest import nse as nse_mod

log = logging.getLogger(__name__)


def _find_cached_bhav(raw_dir: Path, prefix: str, d: date) -> Path | None:
    if not raw_dir.exists():
        return None
    for pat in (
        f"{prefix}_{d.strftime('%y%m%d')}*.zip",
        f"{prefix}_0_0_0_{d.strftime('%Y%m%d')}_F_0000*.zip",
    ):
        matches = sorted(raw_dir.glob(pat))
        if matches:
            return matches[-1]
    return None


def backfill_prices(
    con,
    *,
    trading_days: int = 400,
    fo_days: int = 10,
    resume: bool = True,
    sync_actions: bool = True,
    run_technicals: bool = True,
    start_date: date | None = None,
) -> Dict[str, Any]:
    """Backfills historical NSE CM bhavcopies (`trading_days`), recent NSE F&O (`fo_days`),
    refreshes corporate actions, and runs the vectorised technicals pipeline.
    Resumable via `ingest_progress`; skips weekends, cached raw files, and stored dates;
    marks 404 as holiday and aborts immediately on HTTP 403/429 with manual inbox guidance.
    """
    t0 = datetime.now()
    raw_dir = data_path(settings()["data"]["raw_dir"]) / "nse"
    eps = endpoints()["sources"]
    cm_pat = eps["nse_cm_bhavcopy"]["url_pattern"]
    fo_pat = eps["nse_fo_bhavcopy"]["url_pattern"]

    stored_cm = {
        r[0] for r in con.execute("SELECT DISTINCT date FROM px_daily WHERE source = 'NSE'").fetchall()
    }
    done_cm = db.get_progress_keys(con, "backfill_cm", statuses=("ok", "holiday", "skip")) if resume else set()

    stored_fo = {
        r[0] for r in con.execute("SELECT DISTINCT date FROM fno_daily WHERE source = 'NSE'").fetchall()
    }
    done_fo = db.get_progress_keys(con, "backfill_fo", statuses=("ok", "holiday", "skip")) if resume else set()

    anchor = start_date or (date.today() - timedelta(days=1))
    cm_target = max(1, int(trading_days))
    fo_target = max(0, int(fo_days))

    cm_collected = 0
    cm_network = 0
    cm_cached = 0
    cm_holidays = 0
    blocked = False
    max_cal_days = int(cm_target * 1.7) + 30

    d = anchor
    for _ in range(max_cal_days):
        if cm_collected >= cm_target:
            break
        if d.weekday() >= 5:  # Sat/Sun
            d -= timedelta(days=1)
            continue

        d_str = str(d)
        if d in stored_cm:
            if d_str not in done_cm:
                db.mark_progress(con, "backfill_cm", d_str, "ok", "already in px_daily")
            cm_collected += 1
            d -= timedelta(days=1)
            continue

        if resume and d_str in done_cm:
            # Previously confirmed holiday/skip — don't refetch
            d -= timedelta(days=1)
            continue

        cached_zip = _find_cached_bhav(raw_dir, "BhavCopy_NSE_CM", d)
        if cached_zip:
            res = nse_mod.cm_bhav_from_bytes(con, cached_zip.read_bytes(), d, url=str(cached_zip))
            db.mark_progress(con, "backfill_cm", d_str, "ok", f"cache rows={res.get('rows', 0)}")
            cm_collected += 1
            cm_cached += 1
            d -= timedelta(days=1)
            continue

        url = cm_pat.format(yyyymmdd=d.strftime("%Y%m%d"))
        r = http.fetch(url, source="nse", save_name=f"BhavCopy_NSE_CM_{d.strftime('%y%m%d')}.zip")
        if r.blocked() or (r.error or "").startswith("net:"):
            db.mark_progress(con, "backfill_cm", d_str, "fail", r.error or "blocked_or_net")
            log.error(
                "Stopping NSE CM backfill cleanly at %s (%s). Do not hammer host.\n"
                "Manual fallback: download BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip (or a bundle zip) into data/inbox/ and run `make synkinbox`.",
                d_str, r.error or f"http:{r.status}",
            )
            blocked = r.blocked()
            break
        if r.status in (404, 410) or r.error in ("http:404", "http:410"):
            db.mark_progress(con, "backfill_cm", d_str, "holiday", r.error or "404")
            cm_holidays += 1
            d -= timedelta(days=1)
            continue
        if r.ok():
            res = nse_mod.cm_bhav_from_bytes(con, r.bytes, d, url=url)
            db.mark_progress(con, "backfill_cm", d_str, "ok", f"net rows={res.get('rows', 0)}")
            cm_collected += 1
            cm_network += 1
        else:
            db.mark_progress(con, "backfill_cm", d_str, "fail", r.error or "network error")
            break
        d -= timedelta(days=1)

    # F&O recent trading days backfill (skip if already blocked by host)
    fo_collected = 0
    if not blocked and fo_target > 0:
        d_fo = anchor
        for _ in range(int(fo_target * 2.5) + 15):
            if fo_collected >= fo_target:
                break
            if d_fo.weekday() >= 5:
                d_fo -= timedelta(days=1)
                continue
            d_str = str(d_fo)
            if d_fo in stored_fo:
                if d_str not in done_fo:
                    db.mark_progress(con, "backfill_fo", d_str, "ok", "already in fno_daily")
                fo_collected += 1
                d_fo -= timedelta(days=1)
                continue
            if resume and d_str in done_fo:
                d_fo -= timedelta(days=1)
                continue

            cached_fo = _find_cached_bhav(raw_dir, "BhavCopy_NSE_FO", d_fo)
            if cached_fo:
                nse_mod.fo_bhav_from_bytes(con, cached_fo.read_bytes(), d_fo, url=str(cached_fo))
                db.mark_progress(con, "backfill_fo", d_str, "ok", "cache")
                fo_collected += 1
                d_fo -= timedelta(days=1)
                continue

            url_fo = fo_pat.format(yyyymmdd=d_fo.strftime("%Y%m%d"))
            r_fo = http.fetch(url_fo, source="nse", save_name=f"BhavCopy_NSE_FO_{d_fo.strftime('%y%m%d')}.zip")
            if r_fo.blocked():
                db.mark_progress(con, "backfill_fo", d_str, "fail", r_fo.error or "http:403")
                log.error(
                    "HTTP %s on NSE FO backfill (%s). Drop BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip into data/inbox/ and run `make synkinbox`.",
                    r_fo.status, d_str,
                )
                blocked = True
                break
            if r_fo.status in (404, 410) or r_fo.error in ("http:404", "http:410"):
                db.mark_progress(con, "backfill_fo", d_str, "holiday", r_fo.error or "404")
                d_fo -= timedelta(days=1)
                continue
            if r_fo.ok():
                nse_mod.fo_bhav_from_bytes(con, r_fo.bytes, d_fo, url=url_fo)
                db.mark_progress(con, "backfill_fo", d_str, "ok", "net")
                fo_collected += 1
            else:
                db.mark_progress(con, "backfill_fo", d_str, "fail", r_fo.error or "network error")
                break
            d_fo -= timedelta(days=1)

    actions_res = None
    if sync_actions and not blocked:
        try:
            actions_res = nse_mod.sync_corporate_actions(con, days_back=min(730, max(45, int(cm_target * 1.5))))
        except Exception as exc:
            actions_res = {"status": "skip", "error": str(exc)}

    fno_res = None
    if fo_collected > 0:
        try:
            from ingest.fno_metrics import compute_fno_metrics_for_date
            fno_res = compute_fno_metrics_for_date(con)
        except Exception as exc:
            fno_res = {"status": "skip", "error": str(exc)}

    tech_res = None
    if run_technicals:
        from ingest.technicals_job import run_technicals_job
        tech_res = run_technicals_job(con, incremental=True)

    snap_res = None
    try:
        from app.query.snapshot import build_screener_snapshot
        snap_res = build_screener_snapshot(con)
    except Exception as exc:
        snap_res = {"status": "fail", "error": str(exc)}

    summary = {
        "status": "partial" if blocked else "ok",
        "cm_days_ready": cm_collected,
        "cm_network_fetches": cm_network,
        "cm_cached_hits": cm_cached,
        "cm_holidays_marked": cm_holidays,
        "fo_days_ready": fo_collected,
        "blocked": blocked,
        "actions": actions_res,
        "fno_metrics": fno_res,
        "technicals": tech_res,
        "snapshot": snap_res,
    }
    db.upsert_rows(con, "ingest_status", [{
        "id": f"backfill::{date.today()}",
        "job": "backfill",
        "run_date": date.today(),
        "status": summary["status"],
        "rows": cm_collected + fo_collected,
        "message": f"cm_days={cm_collected} net={cm_network} cache={cm_cached} fo={fo_collected} blocked={blocked}",
        "started_at": t0,
        "finished_at": datetime.now(),
    }], keys=["id"])
    return summary
