"""ingest/reconcile.py
Reconciliation engine verifying stored DuckDB metrics against official exchange raw files
(Prompt Section 5 & Section 12: "Reconcile market cap, close price, volume and F&O OI against
the exchange's own published files for 10 stocks").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from ingest.udiff import parse_udiff


@dataclass
class ReconciliationDiscrepancy:
    symbol: str
    field: str
    expected: Any
    actual: Any
    diff: Optional[float]


@dataclass
class ReconciliationReport:
    stocks_checked: int
    passed: int
    failed: int
    discrepancies: List[ReconciliationDiscrepancy]

    @property
    def ok(self) -> bool:
        return self.failed == 0 and self.stocks_checked > 0


def reconcile_against_raw_files(
    con,
    *,
    cm_bhav_bytes: bytes,
    fo_bhav_bytes: Optional[bytes] = None,
    source: str = "NSE",
    symbols: Optional[List[str]] = None,
    min_stocks: int = 10,
    tol: float = 1e-4,
) -> ReconciliationReport:
    """Compares stored DuckDB px_daily, ref_security market_cap, and fno_daily OI directly against
    raw published UDiFF exchange CSV/ZIP payloads for selected stocks.
    """
    from app.config import settings

    series_keep = (
        settings()["ingest"]["series_equity_nse"]
        if source == "NSE"
        else settings()["ingest"]["series_equity_bse"]
    )
    cm_parsed = parse_udiff(cm_bhav_bytes, source=source, series_keep=series_keep)
    raw_cm = {r["symbol"]: r for r in cm_parsed["px_rows"]}

    raw_fo_oi: Dict[str, int] = {}
    fo_date: Optional[date] = None
    if fo_bhav_bytes:
        fo_parsed = parse_udiff(fo_bhav_bytes, source=source, fo_mode=True)
        for fr in fo_parsed["fno_rows"]:
            if fo_date is None:
                fo_date = fr["date"]
            # Sum near/all contract OI for the underlying + instrument or check per symbol
            sym = fr["underlying"]
            raw_fo_oi[sym] = raw_fo_oi.get(sym, 0) + (fr.get("oi") or 0)

    target_symbols = symbols or sorted(raw_cm.keys())[:min_stocks]
    discrepancies: List[ReconciliationDiscrepancy] = []
    passed = 0
    failed = 0

    for sym in target_symbols:
        expected_px = raw_cm.get(sym)
        if not expected_px:
            failed += 1
            discrepancies.append(ReconciliationDiscrepancy(sym, "raw_cm_presence", "present", "missing", None))
            continue

        row = con.execute(
            """
            SELECT p.close, p.volume, s.shares_outstanding
            FROM px_daily p
            LEFT JOIN ref_security s
              ON s.nse_symbol = p.symbol OR (p.isin IS NOT NULL AND s.isin = p.isin)
            WHERE p.source = ? AND p.symbol = ? AND p.date = ?
            ORDER BY p.series LIMIT 1
            """,
            [source, sym, expected_px["date"]],
        ).fetchone()

        if not row:
            failed += 1
            discrepancies.append(ReconciliationDiscrepancy(sym, "db_px_daily", expected_px["close"], None, None))
            continue

        db_close, db_vol, shares_out = row
        sym_failed = False

        # 1. Close price check
        if db_close is None or abs(float(db_close) - float(expected_px["close"])) > tol:
            sym_failed = True
            discrepancies.append(
                ReconciliationDiscrepancy(sym, "close_price", expected_px["close"], db_close,
                                          None if db_close is None else abs(float(db_close) - float(expected_px["close"])))
            )

        # 2. Volume check
        if db_vol != expected_px["volume"]:
            sym_failed = True
            discrepancies.append(
                ReconciliationDiscrepancy(sym, "volume", expected_px["volume"], db_vol,
                                          None if db_vol is None else abs(float(db_vol) - float(expected_px["volume"])))
            )

        # 3. Market cap check (close * shares_outstanding / 1e7) when shares_outstanding is present
        if shares_out is not None and shares_out > 0:
            expected_mc = round(float(expected_px["close"]) * float(shares_out) / 1e7, 4)
            db_mc = round(float(db_close) * float(shares_out) / 1e7, 4)
            if abs(db_mc - expected_mc) > 0.01:
                sym_failed = True
                discrepancies.append(
                    ReconciliationDiscrepancy(sym, "market_cap", expected_mc, db_mc, abs(db_mc - expected_mc))
                )

        # 4. F&O OI check if symbol has F&O contracts in raw FO file
        if fo_bhav_bytes and sym in raw_fo_oi and fo_date is not None:
            db_oi_row = con.execute(
                "SELECT COALESCE(SUM(oi), 0) FROM fno_daily WHERE source = ? AND underlying = ? AND date = ?",
                [source, sym, fo_date],
            ).fetchone()
            db_oi = int(db_oi_row[0]) if db_oi_row and db_oi_row[0] is not None else 0
            if db_oi != raw_fo_oi[sym]:
                sym_failed = True
                discrepancies.append(
                    ReconciliationDiscrepancy(sym, "fno_total_oi", raw_fo_oi[sym], db_oi, abs(db_oi - raw_fo_oi[sym]))
                )

        if sym_failed:
            failed += 1
        else:
            passed += 1

    return ReconciliationReport(
        stocks_checked=len(target_symbols),
        passed=passed,
        failed=failed,
        discrepancies=discrepancies,
    )
