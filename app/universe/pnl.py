"""app/universe/pnl.py
Portfolio P&L calculation engine:
Computes Invested Value, Current Value, P&L Amount, and P&L % from user columns.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def compute_row_pnl(
    row: Dict[str, Any],
    close_price: Optional[float],
    qty_col: Optional[str] = "quantity",
    buy_price_col: Optional[str] = "buy_price",
) -> Dict[str, Optional[float]]:
    """Calculates P&L metrics for a row if quantity and buy price are present."""
    qty_val = None
    buy_val = None

    # Case-insensitive / alias search for quantity
    qty_candidates = [qty_col, "quantity", "Quantity", "qty", "Qty", "shares", "Shares", "units", "Units"]
    for k in qty_candidates:
        if k and k in row and row[k] not in (None, ""):
            try:
                qty_val = float(str(row[k]).replace(",", "").strip())
                break
            except (ValueError, TypeError):
                pass

    # Case-insensitive / alias search for buy price
    price_candidates = [
        buy_price_col, "buy_price", "Buy_Price", "Buy Price", "buyprice",
        "purchase_price", "Purchase Price", "avg_price", "Avg Price",
        "avg_cost", "Avg Cost", "cost", "Cost", "entry_price",
    ]
    for k in price_candidates:
        if k and k in row and row[k] not in (None, ""):
            try:
                buy_val = float(str(row[k]).replace(",", "").strip())
                break
            except (ValueError, TypeError):
                pass

    if qty_val is None or buy_val is None or buy_val <= 0 or close_price is None or close_price <= 0:
        return {
            "quantity": qty_val,
            "buy_price": buy_val,
            "invested_value": None,
            "current_value": None,
            "pnl_amount": None,
            "pnl_pct": None,
        }

    invested = qty_val * buy_val
    current = qty_val * close_price
    pnl_amt = current - invested
    pnl_pct = ((close_price / buy_val) - 1.0) * 100.0

    return {
        "quantity": qty_val,
        "buy_price": buy_val,
        "invested_value": round(invested, 2),
        "current_value": round(current, 2),
        "pnl_amount": round(pnl_amt, 2),
        "pnl_pct": round(pnl_pct, 2),
    }
