"""AMFI: half-yearly Large/Mid/Small cap categorisation (network + bytes entryways)."""
from __future__ import annotations

import logging
import re
from datetime import date

from app import db
from app.config import endpoints
from ingest import http

log = logging.getLogger(__name__)

PAGE_URL = endpoints()["sources"]["amfi_categorisation"]["page"]
XLSX_RE = re.compile(
    r'https?://[^\s"\']+AverageMarketCapitalization(\d{1,2})([A-Za-z]{3})(\d{4})\.xlsx', re.I)
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def resolve_latest_xlsx() -> str | None:
    r = http.fetch(PAGE_URL, source="amfi", save_name="categorisation_page.html")
    if not r.ok():
        return None
    html = r.bytes.decode("utf-8", "replace")
    best, best_key = None, None
    for m in XLSX_RE.finditer(html):
        key = (int(m.group(3)), MONTHS.get(m.group(2).title(), 0), int(m.group(1)))
        if best_key is None or key > best_key:
            best_key, best = key, m.group(0)
    return best


def parse_period_from_url(url: str) -> date | None:
    m = XLSX_RE.search(url)
    if not m:
        return None
    return date(int(m.group(3)), MONTHS[m.group(2).title()], int(m.group(1)))


def _norm(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def categorisation_from_bytes(con, payload: bytes, period: date | None = None) -> dict:
    """Parse an AMFI AverageMarketCapitalization workbook.

    `period` is REQUIRED (it is part of the primary key and every value's as-of badge):
    without it rows cannot be dated, and per the data policy we fail cleanly rather than
    guess a period.
    """
    if period is None:
        return {"status": "fail",
                "message": "amfi period unknowable; keep the official filename "
                           "pattern AverageMarketCapitalization<DDMonYYYY>.xlsx"}

    import io
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))

    header_row = None
    for i, row in enumerate(rows[:40]):
        cells = [str(c).strip().upper() if c is not None else "" for c in row]
        if any("ISIN" in c for c in cells) and (
            any(("CLASSIF" in c) or ("CATEGORI" in c)  # 'Categorisation', 'Categorization', 'Categorized'
                or ("GROUP" in c) or ("SEBI" in c) for c in cells)
            or any("RANK" in c for c in cells)
        ):
            header_row = i
            break
    if header_row is None:
        return {"status": "fail", "message": "AMFI ISIN/classification header row not found"}

    hdr = [str(c).strip().upper() if c is not None else "" for c in rows[header_row]]

    def col(*names):
        for nm in names:
            for j, h in enumerate(hdr):
                if nm in h:
                    return j
        return None

    i_isin = col("ISIN")
    i_sym = col("SYMBOL")
    i_name = col("NAME")
    # prefer AMFI's all-exchange average, then any generic average-market-cap column;
    # accept both "Capitalisation" and "Capitalization" spellings
    i_mc = col("AVERAGE OF ALL", "AVG MARKET", "AVERAGE MARKET CAPITALI", "MARKET CAPITALI")
    i_rank = col("RANK")
    i_cls = col("CLASSIF", "CATEGORI", "GROUP")
    if i_isin is None:
        return {"status": "fail", "message": "ISIN column missing in AMFI sheet"}

    out = []
    for row in rows[header_row + 1:]:
        if len(row) <= i_isin:
            continue
        isin = _norm(row[i_isin])
        if not isin:
            continue
        mc = row[i_mc] if i_mc is not None and len(row) > i_mc else None
        rank = row[i_rank] if i_rank is not None and len(row) > i_rank else None
        cls = _norm(row[i_cls]) if i_cls is not None and len(row) > i_cls else None
        if rank is not None:
            try:
                rank = int(rank)
            except (TypeError, ValueError):
                rank = None
        if mc is not None:
            try:
                mc = float(str(mc).replace(",", ""))
            except (TypeError, ValueError):
                mc = None
        out.append({
            "as_of_date": period,
            "isin": isin,
            "symbol": _norm(row[i_sym]) if i_sym is not None and len(row) > i_sym else None,
            "company": _norm(row[i_name]) if i_name is not None and len(row) > i_name else None,
            "avg_mcap_crs": mc,
            "rank": rank,
            "classification": cls,
        })
    n = db.upsert_rows(con, "ref_amfi_classification", out, keys=["as_of_date", "isin"])
    return {"status": "ok", "rows": n, "period": str(period)}


def average_market_cap_from_inbox_bytes(con, payload: bytes, filename: str) -> dict:
    m = re.search(r"AverageMarketCapitalization(\d{1,2})([A-Za-z]{3})(\d{4})\.xlsx", filename, re.I)
    period = parse_period_from_url(filename) if m else None
    res = categorisation_from_bytes(con, payload, period)
    return res


def sync_categorisation(con) -> dict:
    url = resolve_latest_xlsx()
    if not url:
        return {"status": "fail",
                "message": "no AverageMarketCapitalization*.xlsx link found on the AMFI categorisation page"}
    r = http.fetch(url, source="amfi", save_name=url.rsplit("/", 1)[-1])
    if not r.ok():
        return {"status": "fail", "message": f"xlsx download failed {r.error}"}
    period = parse_period_from_url(url)
    res = categorisation_from_bytes(con, r.bytes, period)
    res["url"] = url
    return res


def sync_categorisation_from_bytes(con, payload: bytes, filename_hint: str = "") -> dict:
    m = re.search(r"AverageMarketCapitalization(\d{1,2})([A-Za-z]{3})(\d{4})", filename_hint, re.I)
    period = None
    if m:
        period = date(int(m.group(3)), MONTHS[m.group(2).title()], int(m.group(1)))
    return categorisation_from_bytes(con, payload, period)
