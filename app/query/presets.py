"""app/query/presets.py
Dynamic presets & counts calculator:
- Tertile bounds (Low / Mid / High) computed on non-null values of the active universe.
- AMFI Market Cap category bounds (Largecap 1-100, Midcap 101-250, Smallcap 251+).
- Dynamic sector and sub-sector counts tracking the active universe.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple


def calculate_tertiles(values: Sequence[Optional[float]]) -> Optional[Dict[str, Tuple[float, float]]]:
    """Calculates [min, max] bounds for Low, Mid, and High tertiles over non-null values."""
    clean = sorted([v for v in values if v is not None and isinstance(v, (int, float)) and not math.isnan(v)])
    if len(clean) < 3:
        if clean:
            mn, mx = clean[0], clean[-1]
            return {
                "low": (mn, mn + (mx - mn) / 3.0),
                "mid": (mn + (mx - mn) / 3.0, mn + 2.0 * (mx - mn) / 3.0),
                "high": (mn + 2.0 * (mx - mn) / 3.0, mx),
            }
        return None

    n = len(clean)
    idx_t1 = int(n / 3.0)
    idx_t2 = int(2.0 * n / 3.0)

    val_min = clean[0]
    val_t1 = clean[idx_t1]
    val_t2 = clean[idx_t2]
    val_max = clean[-1]

    return {
        "low": (val_min, val_t1),
        "mid": (val_t1, val_t2),
        "high": (val_t2, val_max),
    }


def calculate_amfi_market_cap_categories(
    stocks: Sequence[Dict[str, Any]],
    market_cap_key: str = "market_cap",
) -> Dict[str, Tuple[float, float]]:
    """Calculates Largecap, Midcap, and Smallcap ranges according to AMFI categorization:
    Large Cap: 1st to 100th stock by market cap.
    Mid Cap: 101st to 250th stock by market cap.
    Small Cap: 251st and beyond.
    Returns (min_cap, max_cap) for each category.
    """
    valid_stocks = [
        s for s in stocks
        if s.get(market_cap_key) is not None and isinstance(s.get(market_cap_key), (int, float))
    ]
    # Sort descending by market cap
    sorted_stocks = sorted(valid_stocks, key=lambda s: float(s[market_cap_key]), reverse=True)

    if not sorted_stocks:
        # Fallback default values in Rs Cr
        return {
            "smallcap": (0.0, 5000.0),
            "midcap": (5000.0, 20000.0),
            "largecap": (20000.0, 2000000.0),
        }

    caps = [float(s[market_cap_key]) for s in sorted_stocks]
    min_cap = caps[-1]
    max_cap = caps[0]

    # Largecap: top 100
    large_cutoff_idx = min(100, len(caps)) - 1
    large_min = caps[large_cutoff_idx]

    # Midcap: 101 to 250
    mid_start_idx = min(100, len(caps))
    mid_cutoff_idx = min(250, len(caps)) - 1
    mid_min = caps[mid_cutoff_idx] if mid_cutoff_idx >= mid_start_idx else large_min
    mid_max = caps[mid_start_idx - 1] if mid_start_idx > 0 else max_cap

    # Smallcap: 251 onwards
    small_start_idx = min(250, len(caps))
    small_max = caps[small_start_idx - 1] if small_start_idx > 0 else mid_min
    small_min = min_cap

    return {
        "largecap": (large_min, max_cap),
        "midcap": (mid_min, mid_max),
        "smallcap": (small_min, small_max),
    }


def compute_sector_counts(stocks: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Computes total counts for each sector and sub-sector across the provided stocks.
    Returns {
      sector_name: {
        "total": count,
        "sub_sectors": {subsector_name: count}
      }
    }
    """
    counts: Dict[str, Dict[str, Any]] = {}
    for s in stocks:
        sec = s.get("sector")
        sub = s.get("sub_sector")
        if not sec:
            continue
        if sec not in counts:
            counts[sec] = {"total": 0, "sub_sectors": {}}
        counts[sec]["total"] += 1
        if sub:
            counts[sec]["sub_sectors"][sub] = counts[sec]["sub_sectors"].get(sub, 0) + 1

    return counts

