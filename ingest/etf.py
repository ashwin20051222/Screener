"""ingest/etf.py
ETF Expense Ratio & Tracking Error connector (Step 4.7):
- Parses official AMFI NAVAll.txt (8-column semicolon format verified live 2026-11-10:
  Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date)
- Parses AMFI / AMC Total Expense Ratio (TER) CSV/XLSX drops from data/inbox/
- Computes 1Y annualized Tracking Error = std(daily_ETF_NAV_ret - daily_benchmark_ret) * sqrt(252) * 100.
"""
from __future__ import annotations

import csv
import hashlib
import io
import logging
import math
import statistics
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

from app import db
from ingest import http

log = logging.getLogger(__name__)

AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


def parse_nav_all_txt(payload: bytes, *, etf_only: bool = True) -> List[Dict[str, Any]]:
    """Parses AMFI NAVAll.txt supporting both 6-column legacy and 8-column (Plan;Option) live format."""
    text = payload.decode("utf-8-sig", "replace")
    lines = [ln.strip() for ln in text.splitlines() if ";" in ln]
    if not lines:
        return []

    hdr = [h.strip().lower() for h in lines[0].split(";")]
    idx = {c: i for i, c in enumerate(hdr)}

    def _get(parts: List[str], *keys: str) -> str:
        for k in keys:
            for col_name, pos in idx.items():
                if k in col_name and pos < len(parts):
                    return parts[pos].strip()
        return ""

    out: List[Dict[str, Any]] = []
    for ln in lines[1:]:
        parts = ln.split(";")
        if len(parts) < 6:
            continue
        code = _get(parts, "scheme code") or parts[0].strip()
        isin = _get(parts, "isin div payout", "isin growth") or parts[1].strip()
        name = _get(parts, "scheme name") or parts[3].strip()
        nav_str = _get(parts, "net asset value") or parts[-2].strip()
        dt_str = _get(parts, "date") or parts[-1].strip()

        if not code.isdigit():
            continue
        if isin in ("-", ""):
            isin = None
        if etf_only and "etf" not in name.lower() and "bees" not in name.lower():
            continue

        try:
            nav = float(nav_str)
        except ValueError:
            continue

        nav_dt = None
        for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                nav_dt = datetime.strptime(dt_str, fmt).date()
                break
            except ValueError:
                continue
        if not nav_dt:
            continue

        out.append({
            "scheme_code": code,
            "isin": isin,
            "nav_date": nav_dt,
            "scheme_name": name,
            "nav": nav,
            "source": "AMFI NAVAll.txt",
        })
    return out


def sync_amfi_nav(con, *, etf_only: bool = True) -> dict:
    """Fetches AMFI NAVAll.txt once, caches raw bytes, and persists ETF daily NAVs."""
    r = http.fetch(AMFI_NAV_URL, source="amfi", save_name="NAVAll.txt")
    if not r.ok():
        return {"status": "fail", "message": f"AMFI NAVAll failed: {r.error}"}
    return sync_amfi_nav_from_bytes(con, r.bytes, etf_only=etf_only, saved_path=str(r.saved_path))


def sync_amfi_nav_from_bytes(
    con, payload: bytes, *, etf_only: bool = True, saved_path: str | None = None
) -> dict:
    rows = parse_nav_all_txt(payload, etf_only=etf_only)
    n = db.upsert_rows(con, "etf_nav_daily", rows, keys=["scheme_code", "nav_date"])
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "AMFI",
        "url": AMFI_NAV_URL,
        "saved_path": saved_path or "(manual NAVAll.txt)",
        "bytes": len(payload),
        "rows": n,
        "notes": "ETF daily NAV",
    }], keys=["sha256"])
    return {"status": "ok", "rows": n}


def parse_ter_csv_bytes(payload: bytes) -> List[Dict[str, Any]]:
    """Parses AMFI / AMC Total Expense Ratio CSV disclosures into etf_meta upserts."""
    text = payload.decode("utf-8-sig", "replace")
    reader = list(csv.reader(io.StringIO(text)))
    if len(reader) < 2:
        return []
    hdr = [h.strip().lower() for h in reader[0]]

    def _find(*names):
        for nm in names:
            for j, h in enumerate(hdr):
                if nm in h:
                    return j
        return None

    i_sym = _find("symbol", "ticker")
    i_isin = _find("isin")
    i_code = _find("scheme code", "amfi")
    i_name = _find("scheme name", "name")
    i_ter = _find("ter", "expense ratio", "total expense", "direct")
    i_dt = _find("date", "as on", "as_of")

    if i_ter is None or (i_sym is None and i_isin is None):
        return []

    out: List[Dict[str, Any]] = []
    for row in reader[1:]:
        if len(row) <= i_ter:
            continue
        sym = row[i_sym].strip().upper() if i_sym is not None and i_sym < len(row) else ""
        isin = row[i_isin].strip().upper() if i_isin is not None and i_isin < len(row) else ""
        if not sym and not isin:
            continue
        ter_raw = row[i_ter].replace("%", "").strip()
        try:
            ter = float(ter_raw)
        except ValueError:
            continue

        as_of = date.today()
        if i_dt is not None and i_dt < len(row) and row[i_dt].strip():
            for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y"):
                try:
                    as_of = datetime.strptime(row[i_dt].strip(), fmt).date()
                    break
                except ValueError:
                    continue

        out.append({
            "symbol": sym or isin,
            "isin": isin or None,
            "scheme_code": row[i_code].strip() if i_code is not None and i_code < len(row) else None,
            "scheme_name": row[i_name].strip() if i_name is not None and i_name < len(row) else None,
            "expense_ratio": ter,
            "ter_as_of": as_of,
            "source": "AMFI / AMC official TER",
        })
    return out


def compute_tracking_error(
    etf_navs: Sequence[float],
    benchmark_closes: Sequence[float],
) -> Optional[float]:
    """Annualized 1Y Tracking Error (%) = stdev(ETF daily return - index daily return) * sqrt(252) * 100."""
    n = min(len(etf_navs), len(benchmark_closes))
    if n < 20:
        return None
    e_sub = etf_navs[-n:]
    b_sub = benchmark_closes[-n:]
    diffs = []
    for i in range(1, n):
        if e_sub[i - 1] > 0 and b_sub[i - 1] > 0:
            r_e = (e_sub[i] / e_sub[i - 1]) - 1.0
            r_b = (b_sub[i] / b_sub[i - 1]) - 1.0
            diffs.append(r_e - r_b)
    if len(diffs) < 10:
        return None
    return statistics.stdev(diffs) * math.sqrt(252.0) * 100.0
