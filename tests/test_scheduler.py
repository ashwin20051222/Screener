"""Scheduler cron mapping tests - guards the POSIX-dow -> APScheduler-day bug
(POSIX '6' = Saturday; APScheduler numeric 6 = Sunday. We ship names, so it stays unambiguous)."""
from __future__ import annotations

import pytest
from apscheduler.triggers.cron import CronTrigger

from app.scheduler import _cron_fields


def test_daily_cron_maps():
    k = _cron_fields("30 6 * * *")
    assert k["hour"] == "6" and k["minute"] == "30"
    assert k["day"] == "*" and k["month"] == "*"


def test_weekly_cron_saturday():
    k = _cron_fields("15 7 * * 6")  # POSIX 6 = Saturday
    assert k["day_of_week"] == "sat"
    # and APScheduler itself accepts what we produce (construct trigger, no exception)
    CronTrigger(**k)  # noqa: B018 - construction is the assertion


@pytest.mark.parametrize("posix,expected", [
    ("0 7 * * 0", "sun"),      # Sunday is 0 (or 7) in POSIX cron
    ("0 7 * * 7", "sun"),
    ("0 7 * * 1", "mon"),
    ("0 7 * * 1-5", "mon,tue,wed,thu,fri"),  # numeric range expanded to names
    ("0 7 * * 1,3", "mon,wed"),
    ("0 7 * * *", "*"),        # wildcard passes through
])
def test_dow_translations(posix, expected):
    k = _cron_fields(posix)
    assert k["day_of_week"] == expected
    CronTrigger(**k)  # the translated value is directly usable by APScheduler


def test_bad_cron_raises():
    with pytest.raises(ValueError):
        _cron_fields("30 6 * *")          # 4 fields
    with pytest.raises(ValueError):
        _cron_fields("30 6 * * 9")        # out-of-range dow


def test_build_scheduler_registers_jobs_when_auto_sync_on(monkeypatch):
    from app import scheduler as schedmod

    sched = schedmod.build_scheduler()
    try:
        jobs = {j.id: j.trigger for j in sched.get_jobs()}  # jobs register without .start()
        assert set(jobs) == {"daily_eod", "weekly_masters"}
    finally:
        sched.remove_all_jobs()
