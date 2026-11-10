"""BSE ingestion: bhavcopy (network + bytes) and master fallbacks."""
from __future__ import annotations

import csv
import hashlib
import io
import logging
from datetime import date
from pathlib import Path

from app import db
from app.config import endpoints, settings
from ingest import http
from ingest.udiff import parse_udiff, read_bhav_bytes

log = logging.getLogger(__name__)


def cm_bhav_from_bytes(con, payload: bytes, d: date, url: str = "") -> dict:
    parsed = parse_udiff(payload, source="BSE",
                         series_keep=settings()["ingest"]["series_equity_bse"])
    n = db.upsert_rows(con, "px_daily", parsed["px_rows"], keys=["source", "symbol", "date", "series"])
    return {"status": "ok", "date": str(d), "rows": n}


def sync_cm_bhavcopy(con, d: date) -> dict:
    ep = endpoints()["sources"]["bse_cm_bhavcopy"]
    url = ep["url_pattern"].format(yyyymmdd=d.strftime("%Y%m%d"))
    r = http.fetch(url, source="bse", save_name=f"BhavCopy_BSE_CM_{d.strftime('%y%m%d')}.CSV")
    if not r.ok():
        return {"status": "skip", "date": str(d), "message": f"no file ({r.error})"}
    res = cm_bhav_from_bytes(con, r.bytes, d, url)
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(r.bytes).hexdigest(),
        "source": "BSE",
        "url": url,
        "saved_path": str(r.saved_path),
        "bytes": len(r.bytes),
        "rows": res.get("rows", 0),
        "http_code": r.status,
        "notes": "",
    }], keys=["sha256"])
    res["raw"] = str(r.saved_path)
    return res


def sync_cm_bhavcopy_from_bytes(con, payload: bytes, d: date) -> dict:
    res = cm_bhav_from_bytes(con, payload, d)
    _mark(con, payload, "(manual BSE bhavcopy)", res, 0)
    return res


def fo_bhav_from_bytes(con, payload: bytes, d: date, url: str = "") -> dict:
    parsed = parse_udiff(payload, source="BSE", fo_mode=True)
    rows = parsed["fno_rows"]
    for r in rows:
        if not r.get("option_type"):
            r["option_type"] = ""
        if r.get("strike") is None:
            r["strike"] = 0.0
    n = db.upsert_rows(con, "fno_daily", rows,
                       keys=["source", "underlying", "expiry", "instrument", "option_type", "strike", "date"])
    return {"status": "ok", "date": str(d), "rows": n}


def sync_fo_bhavcopy(con, d: date) -> dict:
    ep = endpoints()["sources"]["bse_fo_bhavcopy"]
    url = ep["url_pattern"].format(yyyymmdd=d.strftime("%Y%m%d"))
    r = http.fetch(url, source="bse", save_name=f"BhavCopy_BSE_FO_{d.strftime('%y%m%d')}.CSV")
    if not r.ok():
        return {"status": "skip", "date": str(d), "message": f"no file ({r.error})"}
    res = fo_bhav_from_bytes(con, r.bytes, d, url)
    _mark(con, r.bytes, url, res, r.status)
    res["raw"] = str(r.saved_path)
    return res


def sync_fo_bhavcopy_from_bytes(con, payload: bytes, d: date) -> dict:
    res = fo_bhav_from_bytes(con, payload, d)
    _mark(con, payload, "(manual BSE FO bhavcopy)", res, 0)
    return res


def _mark(con, payload: bytes, url: str, res: dict, http_code):
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "BSE",
        "url": url,
        "saved_path": "(bytes import)",
        "bytes": len(payload),
        "rows": res.get("rows", 0),
        "http_code": http_code,
        "notes": "",
    }], keys=["sha256"])


def sync_master_from_bhavcopy(con, payload: bytes | None = None) -> dict:
    """Derive a partial BSE master (ISIN + scrip code + name + series) from the latest stored bhavcopy."""
    if payload is None:
        row = con.execute(
            "SELECT saved_path FROM raw_files WHERE source='BSE' ORDER BY fetched_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"status": "skip", "message": "no BSE bhavcopy on disk yet"}
        payload = Path(row[0]).read_bytes()
    rows = read_bhav_bytes(payload)
    header = [h.strip() for h in rows[0]]
    idx = {c: i for i, c in enumerate(header)}
    out = []
    for row in rows[1:]:
        if idx["FinInstrmId"] >= len(row):
            continue
        isin = row[idx["ISIN"]].strip()
        code = row[idx["FinInstrmId"]].strip()
        name = row[idx["FinInstrmNm"]].strip()
        series = row[idx["SctySrs"]].strip()
        if not code or not name:
            continue
        out.append({
            "security_id": isin if isin else f"BSE:{code}",
            "isin": isin or None,
            "bse_code": code,
            "bse_series": series or None,
            "name": name,
            "listing_status": "listed",
        })
    n = db.merge_rows(con, "ref_security", out, keys=["security_id"], preserve_existing={"name"})
    return {"status": "ok", "rows": n}


def sync_scrip_master_from_inbox_csv(con, path) -> dict:
    """Parse an official BSE 'List of Scrips' CSV the user exports and drops into data/inbox/."""
    payload = Path(path).read_bytes()
    rows = list(csv.reader(io.StringIO(payload.decode("utf-8", "replace"))))
    hdr = [h.strip().upper() for h in rows[0]]

    def find(*names):
        for nm in names:
            for j, h in enumerate(hdr):
                if h == nm or h.startswith(nm):
                    return j
        return None

    i_code = find("SECURITY CODE", "SCRIPT CODE", "SCRIP CODE", "CODE")
    i_isin = find("ISIN NO", "ISIN", "ISIN CODE")
    i_name = find("ISSUER NAME", "SECURITY NAME", "SCRIPT NAME", "SCRIP NAME", "NAME OF COMPANY", "NAME")
    i_fv = find("FACE VALUE", "FACE VAL.")
    i_ind = find("INDUSTRY", "SECTOR NAME", "SUBSECTOR", "BASIC INDUSTRY")
    if i_code is None or i_name is None:
        return {"status": "fail", "message": f"unrecognized scrip master header: {hdr[:10]}"}
    out = []
    ind_pairs: list[tuple[str, str]] = []
    for row in rows[1:]:
        if len(row) <= max(x for x in [i_code, i_name] if x is not None):
            continue
        code, name = row[i_code].strip(), row[i_name].strip()
        if not code or not name:
            continue
        isin = row[i_isin].strip() if i_isin is not None and len(row) > i_isin else ""
        fv = _f(row[i_fv]) if i_fv is not None and len(row) > i_fv else None
        raw_ind = row[i_ind].strip() if i_ind is not None and len(row) > i_ind and row[i_ind].strip() else None
        out.append({
            "security_id": isin if isin else f"BSE:{code}",
            "isin": isin or None,
            "bse_code": code,
            "name": name,
            "face_value": fv,
            "listing_status": "listed",
        })
        if raw_ind:
            ind_pairs.append((code, raw_ind))
    n = db.merge_rows(con, "ref_security", out, keys=["security_id"], preserve_existing={"name"})
    cls_res = None
    if ind_pairs:
        from ingest.master_enrichment import classify_security_industries
        cls_res = classify_security_industries(con, ind_pairs, key_col="bse_code", overwrite=True)
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "BSE",
        "url": "(inbox scrip master)",
        "saved_path": str(path),
        "bytes": len(payload),
        "rows": n,
        "notes": "manual inbox import",
    }], keys=["sha256"])
    return {"status": "ok", "rows": n, "classified": cls_res, "file": str(path)}


def _f(v):
    v = (v or "").strip() if isinstance(v, str) else v
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None
