"""FBIL 3-month MIBOR - manual-rate path (automated access declines by design).

FBIL fronts its downloads with an access key + reCAPTCHA (verified 2026-10-25); machine
consumption of its benchmarks is a licensed, paid service. The official daily rate IS publicly
displayed on fbil.org.in. Compliant approach per the data policy:
  - the user pastes the official value into the app (or drops the JSON file below),
  - the rate is stored with its as-of date and badged "manual (official FBIL rate)",
  - if missing, fair-value filters show "Not available from official sources" - never a guess.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path

from app import db
from app.config import data_path, settings

log = logging.getLogger(__name__)


def load_manual_file() -> dict | None:
    p = data_path(settings()["rates"]["fbil_mibor_3m_manual_file"])
    if not p.exists():
        return None
    blob = json.loads(p.read_text(encoding="utf-8"))
    as_of = blob.get("as_of")
    rate = blob.get("rate_pct")
    if not rate:
        return None
    return {
        "rate_date": datetime.strptime(str(as_of), "%Y-%m-%d").date() if as_of else date.today(),
        "rate_pct": float(rate),
    }


def sync_manual_rate(con) -> dict:
    entry = load_manual_file()
    if not entry:
        return {"status": "skip",
                "message": "no manual FBIL rate provided (drop config JSON into data/inbox/fbil_mibor.json using config/settings.yaml::rates path)"}
    if entry["rate_date"] < date.today() - __import__("datetime").timedelta(days=35):
        log.warning("FBIL rate older than 35 days - fair-value filters will stay badged stale")
    n = db.upsert_rows(con, "ref_fbil_mibor", [{
        "rate_date": entry["rate_date"],
        "tenor": "mibor_3m",
        "rate_pct": entry["rate_pct"],
        "source": "manual (official FBIL public rate)",
    }], keys=["rate_date", "tenor"])
    return {"status": "ok", "rows": n, "rate_date": str(entry["rate_date"]),
            "note": "badge in UI: manual entry, official FBIL public rate"}
