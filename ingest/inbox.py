"""Manual-import inbox: official files you download in a browser (screenshot-driven fallback).

Drop an official file into data/inbox/ and run `make synkinbox` (or run scripts.sync_weekly,
which processes the inbox first). Recognized patterns:
 - BhavCopy_NSE_CM_*_F_0000.csv.zip  -> NSE CM prices for that date
 - BhavCopy_NSE_FO_*_F_0000.csv.zip  -> NSE F&O for that date
 - BhavCopy_BSE_CM_*_F_0000.CSV      -> BSE CM prices for that date
 - EQUITY_L.csv                      -> NSE security master
 - eq_etfseclist.csv                 -> NSE ETF master
 - fo_mktlots.csv                    -> NSE F&O lot sizes
 - ind_nifty*list.csv                -> index constituents
 - AverageMarketCapitalization*.xlsx -> AMFI categorisation
 - ListofScripData*.csv (BSE export) -> BSE scrip master drop
 - fbil_mibor.json                   -> manual FBIL 3M MIBOR {"as_of": "...", "rate_pct": x}

After successful ingest, files move to data/processed/ so the same file isn't parsed twice.
Every import writes rows + ingest_status (traceability).
"""
from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime, date
from pathlib import Path

from app.config import data_path, settings
from ingest import amfi as amfi_mod
from ingest import bse as bse_mod
from ingest import nse as nse_mod
from ingest.udiff import parse_udiff

log = logging.getLogger(__name__)

PAT_NSE_CM = re.compile(r"BhavCopy_NSE_CM_0_0_0_(\d{8})_F_0000\.csv\.zip$", re.I)
PAT_NSE_FO = re.compile(r"BhavCopy_NSE_FO_0_0_0_(\d{8})_F_0000\.csv\.zip$", re.I)
PAT_BSE_CM = re.compile(r"BhavCopy_BSE_CM_0_0_0_(\d{8})_F_0000\.CSV$", re.I)
PAT_NIFTY = re.compile(r"ind_nifty\w*list\.csv$", re.I)


def process_inbox(con) -> list[dict]:
    inbox = data_path(settings()["data"]["inbox_dir"])
    processed = data_path(settings()["data"]["processed_dir"])
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    results = []
    for p in sorted(inbox.iterdir()):
        if p.is_dir() or p.name.startswith("."):
            continue
        res = _process_one(con, p)
        results.append({"file": p.name, **res})
        if res.get("status") == "ok":
            shutil.move(str(p), processed / p.name)
    return results


def _process_one(con, p: Path) -> dict:
    name = p.name
    try:
        m = PAT_NSE_CM.match(name) or PAT_BSE_CM.match(name)
        if m and name.lower().endswith(".zip"):
            d = datetime.strptime(m.group(1), "%Y%m%d").date()
            res = nse_mod.sync_cm_bhavcopy_from_bytes(con, p.read_bytes(), d)
            return res
        if PAT_BSE_CM.match(name):
            d = datetime.strptime(PAT_BSE_CM.match(name).group(1), "%Y%m%d").date()
            res = bse_mod.sync_cm_bhavcopy_from_bytes(con, p.read_bytes(), d)
            return res
        if PAT_NSE_FO.match(name):
            d = datetime.strptime(PAT_NSE_FO.match(name).group(1), "%Y%m%d").date()
            res = nse_mod.sync_fo_bhavcopy_from_bytes(con, p.read_bytes(), d)
            return res
        if name.lower() == "equity_l.csv":
            return nse_mod.sync_equity_master_from_bytes(con, p.read_bytes())
        if name.lower() == "eq_etfseclist.csv":
            return nse_mod.sync_etf_master_from_bytes(con, p.read_bytes())
        if name.lower() == "fo_mktlots.csv":
            return nse_mod.sync_fno_lots_from_bytes(con, p.read_bytes())
        if PAT_NIFTY.match(name):
            return nse_mod.sync_index_list_from_bytes(con, p.read_bytes())
        if name.lower().startswith("averagemarketcapitalization") and name.lower().endswith(".xlsx"):
            return amfi_mod.sync_categorisation_from_bytes(con, p.read_bytes())
        if name.lower().startswith("listofscripdata") and name.lower().endswith(".csv"):
            return bse_mod.sync_scrip_master_from_inbox_csv(con, p)
        if name.lower() == "fbil_mibor.json":
            return __import__("ingest.fbil", fromlist=["sync_manual_rate"]).sync_manual_rate(con)
        return {"status": "skip", "message": "unrecognized file pattern"}
    except Exception as e:  # never drop a row silently; keep file for retry
        log.exception("inbox import failed for %s", name)
        return {"status": "fail", "message": f"{type(e).__name__}: {e}"}
