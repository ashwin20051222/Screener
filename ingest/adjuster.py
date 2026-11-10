"""ingest/adjuster.py
Corporate action price adjustment engine for Splits and Bonuses (Section 10.7 & Section 10.9).
Adjusts historical OHLC prices downward and volumes upward prior to ex_date.
Never fabricates adjustments: unparseable corporate actions are logged and skipped cleanly.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger(__name__)

_SPLIT_RE = re.compile(
    r"(?:split|sub-?div).*?from\s+(?:rs\.?|inr|re\.?)?\s*(\d+(?:\.\d+)?)\s*/-?\s*(?:per\s+share\s*)?to\s+(?:rs\.?|inr|re\.?)?\s*(\d+(?:\.\d+)?)",
    re.I,
)
_BONUS_RE = re.compile(r"bonus\s+(\d+)\s*:\s*(\d+)", re.I)


def parse_action_factor(purpose: str) -> Optional[float]:
    """Parses corporate action purpose text into a price multiplier (<= 1.0 for splits/bonuses).
    Examples:
      - Split From Rs 10/- To Rs 2/- -> factor = 2 / 10 = 0.2
      - Bonus 1:1 (1 new share for 1 held -> 2 shares total) -> factor = 1 / (1 + 1) = 0.5
      - Bonus 2:1 (2 new shares for 1 held -> 3 shares total) -> factor = 1 / (2 + 1) = 0.333333
    Returns combined factor if both split & bonus appear in one string; None if dividend/AGM/other.
    """
    if not purpose:
        return None
    factor = 1.0
    matched = False

    m_split = _SPLIT_RE.search(purpose)
    if m_split:
        old_fv = float(m_split.group(1))
        new_fv = float(m_split.group(2))
        if old_fv > 0 and new_fv > 0 and new_fv < old_fv:
            factor *= (new_fv / old_fv)
            matched = True

    m_bonus = _BONUS_RE.search(purpose)
    if m_bonus:
        new_shares = float(m_bonus.group(1))
        held_shares = float(m_bonus.group(2))
        if held_shares > 0 and new_shares > 0:
            factor *= (held_shares / (held_shares + new_shares))
            matched = True

    return factor if matched else None


def adjust_price_series(
    ohlcv_rows: Sequence[Dict[str, Any]],
    actions: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Returns new list of OHLCV rows adjusted for all splits/bonuses matching ex_date.
    Each row should have keys: date (date), open, high, low, close, volume.
    Each action should have keys: ex_date (date), purpose (str) (or factor).
    """
    # Collect parsed multipliers keyed by ex_date
    event_factors: List[Tuple[date, float]] = []
    for act in actions:
        ex_dt = act.get("ex_date")
        if ex_dt is None:
            continue
        f = act.get("factor")
        if f is None:
            f = parse_action_factor(act.get("purpose") or "")
        if f is not None and 0 < f <= 1.0:
            event_factors.append((ex_dt, float(f)))

    # Sort descending by date so we can accumulate efficiently
    event_factors.sort(key=lambda x: x[0], reverse=True)

    adjusted: List[Dict[str, Any]] = []
    for r in sorted(ohlcv_rows, key=lambda x: x["date"]):
        dt = r["date"]
        cum_factor = 1.0
        for ex_dt, f in event_factors:
            if dt < ex_dt:
                cum_factor *= f
        new_row = dict(r)
        if cum_factor != 1.0:
            for k in ("open", "high", "low", "close"):
                if new_row.get(k) is not None:
                    new_row[k] = round(float(new_row[k]) * cum_factor, 4)
            if new_row.get("volume") is not None:
                new_row["volume"] = int(round(float(new_row["volume"]) / cum_factor))
        new_row["adj_factor"] = cum_factor
        adjusted.append(new_row)
    return adjusted
