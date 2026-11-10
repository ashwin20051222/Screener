"""app/metrics/scores.py
Section 11 Open-Approximation Quant Scores Engine ("Approximate - computed locally"):
- Price Momentum Rank (0-100)
- Earnings Quality Rank (0-100)
- Price to Intrinsic Value Rank (0-100)
- Value Momentum Rank (0-100)
- Fundamental Score (1-10, sector percentile composite with bank-specific financial health rules)
Weights & parameters loaded directly from config/scores.yaml.
"""
from __future__ import annotations

import statistics
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def scores_config() -> dict:
    with open(ROOT / "config" / "scores.yaml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def percentile_ranks(
    values: Dict[str, Optional[float]],
    *,
    higher_is_better: bool = True,
) -> Dict[str, float]:
    """Computes cross-sectional percentile ranks (0.0 to 100.0) across non-null entries."""
    valid = [(sym, float(v)) for sym, v in values.items() if v is not None]
    n = len(valid)
    if n == 0:
        return {}
    if n == 1:
        return {valid[0][0]: 50.0}

    valid.sort(key=lambda kv: kv[1], reverse=not higher_is_better)
    ranks: Dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valid[j + 1][1] == valid[i][1]:
            j += 1
        avg_pos = (i + j) / 2.0
        pct = (avg_pos / float(n - 1)) * 100.0
        for k in range(i, j + 1):
            ranks[valid[k][0]] = round(pct, 2)
        i = j + 1
    return ranks


def compute_intrinsic_value(row: Dict[str, Any], cfg: dict) -> Optional[float]:
    """IV = median of available estimates {Graham EPS, FCF perpetuity, Dividend Gordon growth}."""
    params = (cfg.get("price_to_intrinsic_value_rank") or {}).get("parameters") or {}
    r = float(params.get("discount_rate", 0.11))
    g_term = float(params.get("terminal_growth", 0.04))
    g_def = float(params.get("graham_default_growth_pct", 8.0))
    g_cap = float(params.get("graham_max_growth_pct", 20.0))

    estimates: List[float] = []

    # 1. Graham EPS estimate: EPS * (8.5 + 2 * g)
    eps = row.get("earnings_per_share")
    if eps is not None and eps > 0:
        g_eps = row.get("5y_historical_eps_growth")
        g_pct = min(g_cap, max(0.0, float(g_eps) if g_eps is not None else g_def))
        estimates.append(float(eps) * (8.5 + 2.0 * g_pct))

    # 2. FCF perpetuity: (FCF_per_share * (1 + g)) / (r - g)
    cfo = row.get("cash_flow_operating_activities")
    capex = row.get("capital_expenditures") or 0.0
    shares = row.get("total_common_shares_outstanding")
    if cfo is not None and shares and shares > 0 and r > g_term:
        fcf_cr = float(cfo) - float(capex)
        if fcf_cr > 0:
            fcf_ps = (fcf_cr * 1e7) / float(shares)
            estimates.append((fcf_ps * (1.0 + g_term)) / (r - g_term))

    # 3. Dividend Gordon Growth: (DPS * (1 + g)) / (r - g)
    dps = row.get("dividend_per_share")
    if dps is not None and dps > 0 and r > g_term:
        estimates.append((float(dps) * (1.0 + g_term)) / (r - g_term))

    if not estimates:
        return None
    return statistics.median(estimates)


def _weighted_avg(parts: List[tuple[Optional[float], float]]) -> Optional[float]:
    avail = [(v, w) for v, w in parts if v is not None and w > 0]
    if not avail:
        return None
    w_sum = sum(w for _, w in avail)
    if w_sum <= 0:
        return None
    return round(sum(v * w for v, w in avail) / w_sum, 2)


def compute_all_quant_scores(stocks: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Optional[float]]]:
    """Computes all 5 Section 11 quant scores for a full-market stock list.
    Returns {symbol_or_name: {price_momentum_rank, earnings_quality_rank,
                              price_to_intrinsic_value_rank, value_momentum_rank, fundamental_score}}.
    """
    cfg = scores_config()
    if not stocks:
        return {}

    key_for = lambda r: str(r.get("nse_symbol") or r.get("name"))

    # 1. Price Momentum Rank = 0.6 * pct(12M return) + 0.4 * pct(12M return - subsector median 12M return)
    sub_rets: Dict[str, List[float]] = {}
    for r in stocks:
        ret1y = r.get("1y_return")
        sub = r.get("sub_sector") or r.get("sub")
        if ret1y is not None and sub:
            sub_rets.setdefault(sub, []).append(float(ret1y))
    sub_med = {sub: statistics.median(vs) for sub, vs in sub_rets.items() if vs}

    ret_abs = {key_for(r): r.get("1y_return") for r in stocks}
    ret_rel = {
        key_for(r): (
            float(r["1y_return"]) - sub_med[r.get("sub_sector") or r.get("sub")]
            if r.get("1y_return") is not None and (r.get("sub_sector") or r.get("sub")) in sub_med
            else r.get("1y_return")
        )
        for r in stocks
    }
    pct_ret_abs = percentile_ranks(ret_abs, higher_is_better=True)
    pct_ret_rel = percentile_ranks(ret_rel, higher_is_better=True)

    pm_w = (cfg.get("price_momentum_rank") or {}).get("weights") or {}
    w_abs = float(pm_w.get("abs_12m_return_pct", 0.6))
    w_rel = float(pm_w.get("rel_subsector_12m_return_pct", 0.4))

    # 2. Earnings Quality Rank = equal mix of pct(net margin), pct(asset turnover), pct(CFO / net income)
    margins = {key_for(r): r.get("net_profit_margin") for r in stocks}
    turnovers = {key_for(r): r.get("asset_turnover_ratio") for r in stocks}
    cfo_ni: Dict[str, Optional[float]] = {}
    for r in stocks:
        cfo = r.get("cash_flow_operating_activities")
        ni = r.get("net_income")
        cfo_ni[key_for(r)] = (float(cfo) / float(ni)) if (cfo is not None and ni is not None and ni > 0) else None
    pct_margin = percentile_ranks(margins, higher_is_better=True)
    pct_turn = percentile_ranks(turnovers, higher_is_better=True)
    pct_cfoni = percentile_ranks(cfo_ni, higher_is_better=True)

    # 3. Price to Intrinsic Value Rank
    p_iv: Dict[str, Optional[float]] = {}
    for r in stocks:
        px = r.get("close_price")
        iv = compute_intrinsic_value(r, cfg)
        if px is not None and px > 0 and iv is not None and iv > 0:
            p_iv[key_for(r)] = float(px) / float(iv)
        else:
            p_iv[key_for(r)] = None
    pct_piv = percentile_ranks(p_iv, higher_is_better=False)  # low P/IV -> high rank!

    # 4. Value Momentum Rank = 0.5 * valuation_pct(growth-adj PE vs sector) + 0.5 * Price Momentum Rank
    g_pe_adj: Dict[str, Optional[float]] = {}
    for r in stocks:
        pe_prem = r.get("pe_premium_vs_sector")
        if pe_prem is None and r.get("pe_ratio") is not None:
            pe_prem = float(r["pe_ratio"])
        if pe_prem is not None:
            g = r.get("5y_historical_eps_growth") or r.get("5y_historical_revenue_growth") or 0.0
            g_adj = pe_prem - float(g) * 0.5  # rewards higher historical growth at lower sector premium
            g_pe_adj[key_for(r)] = g_adj
        else:
            g_pe_adj[key_for(r)] = None
    pct_val_g = percentile_ranks(g_pe_adj, higher_is_better=False)

    # 5. Fundamental Score pillars (cross-market percentiles, then ranked within sector!)
    pct_pe_inv = percentile_ranks({key_for(r): r.get("pe_premium_vs_sector") or r.get("pe_ratio") for r in stocks}, higher_is_better=False)
    pct_pb_inv = percentile_ranks({key_for(r): r.get("pb_premium_vs_sector") or r.get("pb_ratio") for r in stocks}, higher_is_better=False)
    pct_roe = percentile_ranks({key_for(r): r.get("return_on_equity") for r in stocks}, higher_is_better=True)
    pct_roce = percentile_ranks({key_for(r): r.get("roce") for r in stocks}, higher_is_better=True)
    pct_roa = percentile_ranks({key_for(r): r.get("return_on_assets") for r in stocks}, higher_is_better=True)
    pct_rev5 = percentile_ranks({key_for(r): r.get("5y_historical_revenue_growth") or r.get("1y_historical_revenue_growth") for r in stocks}, higher_is_better=True)
    pct_eps5 = percentile_ranks({key_for(r): r.get("5y_historical_eps_growth") or r.get("1y_historical_eps_growth") for r in stocks}, higher_is_better=True)
    pct_de_inv = percentile_ranks({key_for(r): r.get("debt_to_equity") for r in stocks}, higher_is_better=False)
    pct_ic = percentile_ranks({key_for(r): r.get("interest_coverage_ratio") for r in stocks}, higher_is_better=True)
    pct_nii = percentile_ranks(
        {
            key_for(r): (
                (float(r["net_interest_income"]) / float(r["total_revenue"])) * 100.0
                if r.get("net_interest_income") is not None and r.get("total_revenue")
                else None
            )
            for r in stocks
        },
        higher_is_better=True,
    )

    f_weights = (cfg.get("fundamental_score") or {}).get("pillar_weights") or {}
    raw_composite: Dict[str, Dict[str, Optional[float]]] = {}
    out: Dict[str, Dict[str, Optional[float]]] = {}

    for r in stocks:
        k = key_for(r)
        sec = r.get("sector") or "Other"
        is_fin = bool(r.get("is_financial_institution")) or sec == "Financials"

        pm_rank = _weighted_avg([(pct_ret_abs.get(k), w_abs), (pct_ret_rel.get(k), w_rel)])
        eq_rank = _weighted_avg([
            (pct_margin.get(k), 1.0),
            (pct_turn.get(k), 1.0),
            (pct_cfoni.get(k), 1.0),
        ])
        piv_rank = pct_piv.get(k)
        vm_rank = _weighted_avg([(pct_val_g.get(k), 0.5), (pm_rank, 0.5)])

        p_val = _weighted_avg([(pct_pe_inv.get(k), 0.5), (pct_pb_inv.get(k), 0.5)])
        p_prof = _weighted_avg([
            (pct_roe.get(k), 0.4),
            (pct_roa.get(k) if is_fin else pct_roce.get(k), 0.35),
            (pct_margin.get(k), 0.25),
        ])
        p_gr = _weighted_avg([(pct_rev5.get(k), 0.5), (pct_eps5.get(k), 0.5)])
        if is_fin:
            p_hlth = _weighted_avg([(pct_nii.get(k), 0.5), (pct_roa.get(k), 0.5)])
        else:
            p_hlth = _weighted_avg([(pct_de_inv.get(k), 0.5), (pct_ic.get(k), 0.5)])

        comp = _weighted_avg([
            (p_val, float(f_weights.get("valuation", 0.25))),
            (p_prof, float(f_weights.get("profitability", 0.30))),
            (p_gr, float(f_weights.get("growth", 0.25))),
            (p_hlth, float(f_weights.get("financial_health", 0.20))),
        ])
        raw_composite.setdefault(sec, {})[k] = comp

        out[k] = {
            "price_momentum_rank": pm_rank,
            "earnings_quality_rank": eq_rank,
            "price_to_intrinsic_value_rank": piv_rank,
            "value_momentum_rank": vm_rank,
            "fundamental_score": None,
        }

    # Map composite within each sector to Fundamental Score 1.0 .. 10.0
    for sec, comp_map in raw_composite.items():
        sec_pct = percentile_ranks(comp_map, higher_is_better=True)
        for k, pct in sec_pct.items():
            out[k]["fundamental_score"] = round(1.0 + 9.0 * (pct / 100.0), 2)

    return out
