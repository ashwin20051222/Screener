"""app/metrics/formulas.py
Core financial, valuation, profitability, growth, and derivatives formulas.
Strictly adheres to Section 10 mathematical conventions and Section 12 golden test specifications.
"""
from __future__ import annotations

from typing import Optional, Sequence


def safe_div(num: Optional[float], den: Optional[float], allow_negative_den: bool = False) -> Optional[float]:
    """Safe division returning None if either operand is None or if denominator is 0 (or negative if disallowed)."""
    if num is None or den is None:
        return None
    if den == 0:
        return None
    if not allow_negative_den and den < 0:
        return None
    return num / den


def cagr(start_val: Optional[float], end_val: Optional[float], years: float) -> Optional[float]:
    """Compound Annual Growth Rate over n years: (end / start)^(1/n) - 1.
    Returns percentage as a fraction (e.g. 0.065 for 6.5%).
    Null if start or end <= 0 or years <= 0.
    """
    if start_val is None or end_val is None or years <= 0:
        return None
    if start_val <= 0 or end_val <= 0:
        return None
    return (end_val / start_val) ** (1.0 / years) - 1.0


def avg2(x0: Optional[float], x1: Optional[float]) -> Optional[float]:
    """2-period average: (x0 + x1) / 2."""
    if x0 is not None and x1 is not None:
        return (x0 + x1) / 2.0
    return x0 if x0 is not None else x1


def avg5(values: Sequence[Optional[float]]) -> Optional[float]:
    """5-period arithmetic mean over FY0 to FY-4."""
    clean = [v for v in values if v is not None]
    if len(clean) < 5:
        return None
    return sum(clean[:5]) / 5.0


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------

def return_on_equity(net_profit: Optional[float], avg_equity: Optional[float]) -> Optional[float]:
    """ROE = Net Profit / avg2(Common Equity) * 100."""
    res = safe_div(net_profit, avg_equity, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def return_on_assets(net_profit: Optional[float], avg_assets: Optional[float]) -> Optional[float]:
    """ROA = Net Profit / avg2(Total Assets) * 100."""
    res = safe_div(net_profit, avg_assets, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def return_on_investment(net_income: Optional[float], avg_invested_capital: Optional[float]) -> Optional[float]:
    """ROI = Net Income / avg2(Invested Capital) * 100."""
    res = safe_div(net_income, avg_invested_capital, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def roce(ebit: Optional[float], capital_employed: Optional[float]) -> Optional[float]:
    """ROCE = EBIT / (Total Assets - Current Liabilities) * 100."""
    res = safe_div(ebit, capital_employed, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def margin(item: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Generic margin = Item / Revenue * 100."""
    res = safe_div(item, revenue, allow_negative_den=False)
    return res * 100.0 if res is not None else None


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

def pe_ratio(price: Optional[float], eps: Optional[float]) -> Optional[float]:
    """PE = Price / EPS. Null if EPS <= 0."""
    return safe_div(price, eps, allow_negative_den=False)


def pb_ratio(price: Optional[float], bvps: Optional[float]) -> Optional[float]:
    """PB = Price / Book Value Per Share. Null if BVPS <= 0."""
    return safe_div(price, bvps, allow_negative_den=False)


def ps_ratio(price: Optional[float], sps: Optional[float]) -> Optional[float]:
    """PS = Price / Sales Per Share. Null if SPS <= 0."""
    return safe_div(price, sps, allow_negative_den=False)


def dividend_yield(dps: Optional[float], price: Optional[float]) -> Optional[float]:
    """Dividend Yield (%) = DPS / Price * 100."""
    res = safe_div(dps, price, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def enterprise_value(
    market_cap: Optional[float],
    total_debt: Optional[float] = 0.0,
    minority_interest: Optional[float] = 0.0,
    cash_and_equivalents: Optional[float] = 0.0,
) -> Optional[float]:
    """EV = Market Cap + Total Debt + Minority Interest - Cash & Short-Term Investments."""
    if market_cap is None:
        return None
    debt = total_debt or 0.0
    mi = minority_interest or 0.0
    cash = cash_and_equivalents or 0.0
    return market_cap + debt + mi - cash


def ev_multiple(ev: Optional[float], denominator_item: Optional[float]) -> Optional[float]:
    """EV / Item (e.g. EBITDA, EBIT, Revenue). Null if denominator <= 0."""
    return safe_div(ev, denominator_item, allow_negative_den=False)


def price_to_cashflow(market_cap: Optional[float], cash_flow: Optional[float]) -> Optional[float]:
    """Price / CFO or Price / FCF. Null if cash flow <= 0."""
    return safe_div(market_cap, cash_flow, allow_negative_den=False)


# ---------------------------------------------------------------------------
# Benchmark Premiums & Spreads
# ---------------------------------------------------------------------------

def multiple_premium(stock_multiple: Optional[float], sector_benchmark: Optional[float]) -> Optional[float]:
    """Relative multiple premium (%): (Stock Multiple / Sector Benchmark - 1) * 100."""
    if stock_multiple is None or sector_benchmark is None or sector_benchmark <= 0:
        return None
    return ((stock_multiple / sector_benchmark) - 1.0) * 100.0


def yield_spread(stock_yield: Optional[float], sector_yield: Optional[float]) -> Optional[float]:
    """Dividend yield spread vs sector (percentage points): Stock Yield - Sector Yield."""
    if stock_yield is None or sector_yield is None:
        return None
    return stock_yield - sector_yield


# ---------------------------------------------------------------------------
# Financial Ratios
# ---------------------------------------------------------------------------

def current_ratio(
    current_assets: Optional[float],
    current_liabilities: Optional[float],
    is_financial_institution: bool = False,
) -> Optional[float]:
    """Current Ratio = Current Assets / Current Liabilities. Null for banks/insurers."""
    if is_financial_institution:
        return None
    return safe_div(current_assets, current_liabilities, allow_negative_den=False)


def quick_ratio(
    current_assets: Optional[float],
    inventory: Optional[float],
    current_liabilities: Optional[float],
    is_financial_institution: bool = False,
) -> Optional[float]:
    """Quick Ratio = (Current Assets - Inventory) / Current Liabilities."""
    if is_financial_institution or current_assets is None or current_liabilities is None:
        return None
    inv = inventory or 0.0
    return safe_div(current_assets - inv, current_liabilities, allow_negative_den=False)


def debt_to_equity(
    total_debt: Optional[float],
    total_equity: Optional[float],
    is_financial_institution: bool = False,
) -> Optional[float]:
    """Debt to Equity = Total Debt / Total Equity. Null for banks/insurers."""
    if is_financial_institution:
        return None
    return safe_div(total_debt, total_equity, allow_negative_den=False)


def interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    """Interest Coverage = EBIT / Interest Expense."""
    return safe_div(ebit, interest_expense, allow_negative_den=False)


def cash_conversion_cycle(
    dio: Optional[float],
    dso: Optional[float],
    dpo: Optional[float],
    is_financial_institution: bool = False,
) -> Optional[float]:
    """Cash Conversion Cycle = DIO + DSO - DPO. Null for financial institutions."""
    if is_financial_institution or dio is None or dso is None or dpo is None:
        return None
    return dio + dso - dpo


# ---------------------------------------------------------------------------
# Futures & Options
# ---------------------------------------------------------------------------

def futures_fair_value(spot_price: Optional[float], r_mibor: Optional[float], days_to_expiry: int) -> Optional[float]:
    """Fair Value = Spot * (1 + r * days / 365) with r in decimal (e.g. 0.065 for 6.5%)."""
    if spot_price is None or r_mibor is None or days_to_expiry < 0:
        return None
    return spot_price * (1.0 + r_mibor * (days_to_expiry / 365.0))


def futures_basis(futures_price: Optional[float], spot_price: Optional[float]) -> Optional[float]:
    """Basis = Futures Price - Spot Price."""
    if futures_price is None or spot_price is None:
        return None
    return futures_price - spot_price


def fair_value_spread(fair_val: Optional[float], futures_price: Optional[float]) -> Optional[float]:
    """Fair Value Spread = Fair Value - Futures Price."""
    if fair_val is None or futures_price is None:
        return None
    return fair_val - futures_price


def cash_and_carry_profit(futures_price: Optional[float], fair_val: Optional[float]) -> Optional[float]:
    """Cash & Carry Profit = Futures Price - Fair Value."""
    if futures_price is None or fair_val is None:
        return None
    return futures_price - fair_val


def rollover_cost(next_futures_price: Optional[float], near_futures_price: Optional[float]) -> Optional[float]:
    """Rollover Cost (%) = (Next Month Futures / Near Month Futures - 1) * 100."""
    res = safe_div(next_futures_price, near_futures_price, allow_negative_den=False)
    return (res - 1.0) * 100.0 if res is not None else None


def percentage_rollover(oi_next: Optional[float], oi_near: Optional[float], oi_far: Optional[float] = 0.0) -> Optional[float]:
    """Percentage Rollover (%) = OI(next) / (OI(near) + OI(next) + OI(far)) * 100."""
    if oi_next is None or oi_near is None:
        return None
    total_oi = (oi_near or 0.0) + (oi_next or 0.0) + (oi_far or 0.0)
    res = safe_div(oi_next, total_oi, allow_negative_den=False)
    return res * 100.0 if res is not None else None


def put_call_ratio(put_oi: Optional[float], call_oi: Optional[float]) -> Optional[float]:
    """PCR = Put OI / Call OI."""
    return safe_div(put_oi, call_oi, allow_negative_den=False)


def oi_change_pct(current_oi: Optional[float], previous_oi: Optional[float]) -> Optional[float]:
    """OI Change (%) = (Current OI / Previous OI - 1) * 100."""
    res = safe_div(current_oi, previous_oi, allow_negative_den=False)
    return (res - 1.0) * 100.0 if res is not None else None


# ---------------------------------------------------------------------------
# Banking & Balance Sheet Integrity
# ---------------------------------------------------------------------------

def bank_net_loans(gross_loans: Optional[float], npa_provisions: Optional[float]) -> Optional[float]:
    """Bank Net Loans = Gross Advances / Loans - NPA Provisions."""
    if gross_loans is None:
        return None
    prov = npa_provisions or 0.0
    return gross_loans - prov


def validate_balance_sheet(
    total_assets: Optional[float],
    total_liabilities: Optional[float],
    total_equity: Optional[float],
    tolerance: float = 1e-2,
) -> bool:
    """Integrity check: Assets == Liabilities + Equity within tolerance."""
    if total_assets is None or total_liabilities is None or total_equity is None:
        return False
    return abs(total_assets - (total_liabilities + total_equity)) <= tolerance

