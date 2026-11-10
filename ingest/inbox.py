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
PAT_NSE_PR = re.compile(r"PR(\d{6})\.zip$", re.I)
PAT_NSE_MCAP = re.compile(r"mcap(\d{8})\.csv$", re.I)


def process_inbox(con) -> list[dict]:
    inbox = data_path(settings()["data"]["inbox_dir"])
    processed = data_path(settings()["data"]["processed_dir"])
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    results = []
    has_new_px = False
    for p in sorted(inbox.iterdir()):
        if p.is_dir() or p.name.startswith("."):
            continue
        res = _process_one(con, p)
        results.append({"file": p.name, **res})
        if res.get("status") == "ok":
            if res.get("px_updated") or PAT_NSE_CM.match(p.name) or PAT_BSE_CM.match(p.name):
                has_new_px = True
            shutil.move(str(p), processed / p.name)
    if has_new_px:
        try:
            from ingest.technicals_job import run_technicals_job
            run_technicals_job(con, incremental=True)
        except Exception as exc:
            log.warning("Post-inbox technicals refresh failed: %s", exc)
    if any(r.get("status") == "ok" for r in results):
        try:
            from app.query.snapshot import build_screener_snapshot
            build_screener_snapshot(con)
        except Exception as exc:
            log.warning("Post-inbox snapshot rebuild failed: %s", exc)
    return results


def _process_one(con, p: Path) -> dict:
    name = p.name
    try:
        m = PAT_NSE_CM.match(name) or PAT_BSE_CM.match(name)
        if m and name.lower().endswith(".zip"):
            from app import db as _db
            d = datetime.strptime(m.group(1), "%Y%m%d").date()
            res = nse_mod.sync_cm_bhavcopy_from_bytes(con, p.read_bytes(), d)
            _db.mark_progress(con, "backfill_cm", str(d), "ok", f"inbox {name}")
            res["px_updated"] = True
            return res
        if "bhav" in name.lower() and name.lower().endswith(".zip") and not PAT_NSE_FO.match(name):
            import zipfile as _zf
            from app import db as _db
            total_rows = 0
            imported = 0
            with _zf.ZipFile(p) as z:
                for inner in z.namelist():
                    base = inner.rsplit("/", 1)[-1]
                    mi = PAT_NSE_CM.match(base) or PAT_BSE_CM.match(base)
                    if mi:
                        d_in = datetime.strptime(mi.group(1), "%Y%m%d").date()
                        r_in = nse_mod.sync_cm_bhavcopy_from_bytes(con, z.read(inner), d_in) if "NSE" in base.upper() else bse_mod.sync_cm_bhavcopy_from_bytes(con, z.read(inner), d_in)
                        _db.mark_progress(con, "backfill_cm", str(d_in), "ok", f"inbox archive {base}")
                        total_rows += int(r_in.get("rows", 0))
                        imported += 1
            if imported > 0:
                return {"status": "ok", "rows": total_rows, "archives_imported": imported, "px_updated": True}
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
        if name.lower() == "sme_equity_l.csv":
            return nse_mod.sync_sme_master_from_bytes(con, p.read_bytes())
        if name.lower() == "eq_etfseclist.csv":
            return nse_mod.sync_etf_master_from_bytes(con, p.read_bytes())
        if name.lower() == "fo_mktlots.csv":
            return nse_mod.sync_fno_lots_from_bytes(con, p.read_bytes())
        if PAT_NIFTY.match(name):
            return nse_mod.sync_index_list_from_bytes(con, p.read_bytes(), filename_hint=name)
        m_pr = PAT_NSE_PR.match(name)
        if m_pr:
            d = datetime.strptime(m_pr.group(1), "%d%m%y").date()
            return nse_mod.sync_nse_pr_mcap_from_zip_bytes(con, p.read_bytes(), d, url=f"(inbox {name})")
        m_mc = PAT_NSE_MCAP.match(name)
        if m_mc:
            d = datetime.strptime(m_mc.group(1), "%d%m%Y").date()
            return nse_mod.sync_nse_mcap_csv_bytes(con, p.read_bytes(), d=d, url=f"(inbox {name})")
        if name.lower().startswith("averagemarketcapitalization") and name.lower().endswith(".xlsx"):
            return amfi_mod.sync_categorisation_from_bytes(con, p.read_bytes(), filename_hint=name)
        if name.lower().startswith("listofscripdata") and name.lower().endswith(".csv"):
            return bse_mod.sync_scrip_master_from_inbox_csv(con, p)
        if name.lower() == "fbil_mibor.json":
            return __import__("ingest.fbil", fromlist=["sync_manual_rate"]).sync_manual_rate(con)
        if name.upper().startswith("SHP_") and name.lower().endswith(".xml"):
            from ingest.ownership import sync_shareholding_xbrl_from_bytes
            return sync_shareholding_xbrl_from_bytes(con, p.read_bytes())
        if name.lower().startswith("bulk_deals") and name.lower().endswith(".csv"):
            from ingest.ownership import parse_deals_csv_bytes
            from app import db as _db
            rows = parse_deals_csv_bytes(p.read_bytes(), deal_type="BULK")
            n = _db.upsert_rows(con, "bulk_block_deals", rows,
                                keys=["deal_date", "exchange", "deal_type", "symbol", "client_name", "buy_sell", "quantity"])
            return {"status": "ok", "rows": n}
        if name.lower().startswith("block_deals") and name.lower().endswith(".csv"):
            from ingest.ownership import parse_deals_csv_bytes
            from app import db as _db
            rows = parse_deals_csv_bytes(p.read_bytes(), deal_type="BLOCK")
            n = _db.upsert_rows(con, "bulk_block_deals", rows,
                                keys=["deal_date", "exchange", "deal_type", "symbol", "client_name", "buy_sell", "quantity"])
            return {"status": "ok", "rows": n}
        if ("insider" in name.lower() or name.lower().startswith("pit_")) and name.lower().endswith(".csv"):
            from ingest.ownership import parse_pit_json_or_csv
            from app import db as _db
            rows = parse_pit_json_or_csv(p.read_bytes())
            n = _db.upsert_rows(con, "insider_trades", rows,
                                keys=["broadcast_date", "symbol", "acquirer_name", "transaction_type", "shares"])
            return {"status": "ok", "rows": n}
        if (name.upper().startswith("INDAS_") or name.upper().startswith("FIN_")) and name.lower().endswith(".xml"):
            from ingest.financials import ingest_financial_xbrl_bytes
            return ingest_financial_xbrl_bytes(con, p.read_bytes())
        if name.lower() == "navall.txt":
            from ingest.etf import sync_amfi_nav_from_bytes
            return sync_amfi_nav_from_bytes(con, p.read_bytes())
        if name.lower().startswith("ter_") and name.lower().endswith(".csv"):
            from ingest.etf import parse_ter_csv_bytes
            from app import db as _db
            rows = parse_ter_csv_bytes(p.read_bytes())
            n = _db.upsert_rows(con, "etf_meta", rows, keys=["symbol"])
            return {"status": "ok", "rows": n}
        return {"status": "skip", "message": "unrecognized file pattern"}
    except Exception as e:  # never drop a row silently; keep file for retry
        log.exception("inbox import failed for %s", name)
        return {"status": "fail", "message": f"{type(e).__name__}: {e}"}
