"""app/metrics/benchmarks.py
Sector & Sub-sector benchmark calculations.
Supports dual benchmark scopes ('market' vs 'universe') as required by Spec Section 10.4 & Section 5.
"""
from __future__ import annotations

import statistics
from typing import Dict, List, Optional, Sequence


def calculate_group_benchmark(
    values: Sequence[Optional[float]],
    method: str = "median",
) -> Optional[float]:
    """Calculates benchmark multiple for a group. Default method is median of positive values."""
    positive_vals = [v for v in values if v is not None and v > 0]
    if not positive_vals:
        return None

    if method == "median":
        return statistics.median(positive_vals)
    elif method == "trimmed_mean":
        if len(positive_vals) >= 4:
            s = sorted(positive_vals)
            cut = int(len(s) * 0.1)
            trimmed = s[cut: len(s) - cut] if cut > 0 else s
            return sum(trimmed) / float(len(trimmed))
        return statistics.mean(positive_vals)
    elif method == "aggregate":
        return sum(positive_vals) / float(len(positive_vals))
    else:
        return statistics.median(positive_vals)


class BenchmarkEngine:
    """Manages sector and sub-sector benchmarks across market and active universe."""

    def __init__(self, default_scope: str = "market", method: str = "median"):
        self.default_scope = default_scope
        self.method = method

    def compute_benchmarks(
        self,
        stocks: Sequence[dict],
        group_key: str = "sector",
        metrics: Sequence[str] = ("pe_ratio", "pb_ratio", "ps_ratio", "dividend_yield"),
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """Returns {group_name: {metric_name: benchmark_value}}."""
        grouped: Dict[str, Dict[str, List[float]]] = {}

        for s in stocks:
            grp = s.get(group_key)
            if not grp:
                continue
            if grp not in grouped:
                grouped[grp] = {m: [] for m in metrics}

            for m in metrics:
                val = s.get(m)
                if val is not None and isinstance(val, (int, float)):
                    grouped[grp][m].append(float(val))

        benchmarks: Dict[str, Dict[str, Optional[float]]] = {}
        for grp, m_dict in grouped.items():
            benchmarks[grp] = {}
            for m, vals in m_dict.items():
                benchmarks[grp][m] = calculate_group_benchmark(vals, method=self.method)

        return benchmarks

    def enrich_stock_with_benchmarks(
        self,
        stock: dict,
        sector_benchmarks: Dict[str, Dict[str, Optional[float]]],
        subsector_benchmarks: Dict[str, Dict[str, Optional[float]]],
    ) -> dict:
        """Enriches a stock dictionary with sector and sub-sector benchmark comparisons."""
        out = dict(stock)
        sector = stock.get("sector")
        subsector = stock.get("sub_sector")

        # Sector metrics
        s_bench = sector_benchmarks.get(sector, {}) if sector else {}
        sub_bench = subsector_benchmarks.get(subsector, {}) if subsector else {}

        # Sector PE / PB / PS / Div Yield
        out["sector_pe"] = s_bench.get("pe_ratio")
        out["sector_pb"] = s_bench.get("pb_ratio")
        out["sector_ps"] = s_bench.get("ps_ratio")
        out["sector_dividend_yield"] = s_bench.get("dividend_yield")

        # Sector Premiums
        for m, prem_key in [
            ("pe_ratio", "pe_premium_vs_sector"),
            ("pb_ratio", "pb_premium_vs_sector"),
            ("ps_ratio", "ps_premium_vs_sector"),
        ]:
            val = stock.get(m)
            b = s_bench.get(m)
            if val is not None and b is not None and b > 0:
                out[prem_key] = ((val / b) - 1.0) * 100.0
            else:
                out[prem_key] = None

        # Sector Dividend Yield Spread
        val_dy = stock.get("dividend_yield")
        b_dy = s_bench.get("dividend_yield")
        if val_dy is not None and b_dy is not None:
            out["dividend_yield_vs_sector"] = val_dy - b_dy
        else:
            out["dividend_yield_vs_sector"] = None

        # Sub-sector Premiums
        for m, prem_key in [
            ("pe_ratio", "pe_premium_vs_sub_sector"),
            ("pb_ratio", "pb_premium_vs_sub_sector"),
            ("ps_ratio", "ps_premium_vs_sub_sector"),
        ]:
            val = stock.get(m)
            b = sub_bench.get(m)
            if val is not None and b is not None and b > 0:
                out[prem_key] = ((val / b) - 1.0) * 100.0
            else:
                out[prem_key] = None

        # Sub-sector Dividend Yield Spread
        b_sub_dy = sub_bench.get("dividend_yield")
        if val_dy is not None and b_sub_dy is not None:
            out["dividend_yield_vs_sub_sector"] = val_dy - b_sub_dy
        else:
            out["dividend_yield_vs_sub_sector"] = None

        return out
