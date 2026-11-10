"""Backgrounder scheduler (APScheduler) wired to the ingest jobs, IST timezone.

Important: settings.yaml cron strings use POSIX cron semantics (day-of-week 0/7 = Sunday,
1 = Monday ... 6 = Saturday), while APScheduler's numeric day_of_week runs Mon=0..Sun=6.
We therefore translate the numeric dow into APScheduler weekday names, so `15 7 * * 6`
lands on Saturday as intended (not APScheduler's Sunday).
"""
from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from ingest import sources

log = logging.getLogger(__name__)
_IST = ZoneInfo(settings()["scheduler"]["timezone"])

# APScheduler weekday names, indexed by Python's datetime convention (Mon=0).
_NAMES_BY_PY = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _posix_dow_name(token: str) -> str:
    """POSIX dow single number (0/7=Sun, 1=Mon ... 6=Sat) -> APScheduler weekday name."""
    n = int(token)
    if not (0 <= n <= 7):
        raise ValueError(f"day-of-week out of range: {token!r}")
    if n in (0, 7):
        return "sun"
    return _NAMES_BY_PY[n - 1]  # POSIX n=Mon(1)..Sat(6) -> Python idx n-1


def _day_of_week_ap(token: str) -> str | None:
    """Translate one POSIX dow token to APScheduler syntax; None = pass through unchanged.

    Fits our controlled settings.yaml (numbers, comma lists, simple ranges, `*`). Anything
    fancier (steps, `?`) is passed through untouched so APScheduler can decide.
    """
    if token in ("*", "?") or any(ch in token for ch in "*/") or not token:
        return None
    if "-" in token:
        lo, _, hi = token.partition("-")
        if lo.isdigit() and hi.isdigit():
            num_lo, num_hi = int(lo), int(hi)
            if not (0 <= num_lo <= 7 and 0 <= num_hi <= 7) or num_hi < num_lo:
                raise ValueError(f"unsupported day-of-week range in cron: {token!r}")
            return ",".join(dict.fromkeys(
                _posix_dow_name(str(n)) for n in range(num_lo, num_hi + 1)))
        return None
    if "," in token:
        out = []
        for part in token.split(","):
            out.append(_posix_dow_name(part) if part.isdigit() else part.lower())
        return ",".join(out)
    return _posix_dow_name(token) if token.isdigit() else token.lower()


def _cron_fields(expr: str) -> dict[str, str]:
    """Parse a 5-field POSIX cron string into APScheduler trigger kwargs."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"cron expression must have 5 fields (min hour dom month dow): {expr!r}")
    minute, hour, day, month, dow = parts

    dow_ap_parts = [_day_of_week_ap(tok) for tok in dow.split(",")]
    dow_ap = ",".join(p if p is not None else tok
                      for p, tok in zip(dow_ap_parts, dow.split(",")))
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": dow_ap or "*",
        "second": "0",
    }


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone=str(_IST))
    cfg = settings()["scheduler"]
    if cfg.get("auto_sync", False):
        sched.add_job(sources.run_daily, "cron", id="daily_eod",
                      **_cron_fields(cfg["eod_job_cron"]),
                      max_instances=1, coalesce=True, misfire_grace_time=3600)
        sched.add_job(sources.run_weekly, "cron", id="weekly_masters",
                      **_cron_fields(cfg["weekly_job_cron"]),
                      max_instances=1, coalesce=True, misfire_grace_time=7200)
        if cfg.get("quarterly_job_cron"):
            sched.add_job(sources.run_quarterly, "cron", id="quarterly_filings",
                          **_cron_fields(cfg["quarterly_job_cron"]),
                          max_instances=1, coalesce=True, misfire_grace_time=7200)
        log.info("auto_sync on: daily cron %r + weekly masters cron %r (IST)",
                 cfg["eod_job_cron"], cfg["weekly_job_cron"])
    else:
        log.info("auto_sync disabled (offline mode); run ingest manually via `make sync-daily`")
    return sched
