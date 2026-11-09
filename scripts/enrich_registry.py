#!/usr/bin/env python3
"""Enrich registry/filters.yaml with full metadata:
- inputs: list of required fields
- null_rule: condition under which the filter evaluates to null
- direction_of_goodness: higher_is_better | lower_is_better | neutral
- glossary: clean, original explanatory text
Also syncs to apps/web/src/data/filters.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "filters.yaml"
WEB_JSON_PATH = ROOT / "apps" / "web" / "src" / "data" / "filters.json"


def build_metadata(fid: str, name: str, category: str, unit: str, formula: str, availability: str) -> dict:
    # Defaults
    inputs = []
    null_rule = "Null if underlying data point is missing"
    direction = "neutral"
    glossary = f"{name} measures the performance of a company."

    # 1. Profitability
    if category == "Profitability":
        if fid == "return_on_equity":
            inputs = ["net_profit", "common_equity"]
            null_rule = "Null if avg2(common_equity) <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Return on Equity (ROE) measures how efficiently management generates profits from shareholders' equity capital. Calculated as Net Profit divided by the 2-year average common equity."
        elif fid == "return_on_assets":
            inputs = ["net_profit", "total_assets"]
            null_rule = "Null if avg2(total_assets) <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Return on Assets (ROA) evaluates how efficiently a company's total assets generate earnings. Calculated as Net Profit divided by the 2-year average total assets."
        elif fid == "return_on_investment":
            inputs = ["net_income", "equity", "long_term_debt", "other_long_term_liabilities"]
            null_rule = "Null if average invested capital <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Return on Investment (ROI) gauges profitability generated from all long-term capital deployed (equity plus long-term debt and liabilities). Calculated as Net Income over the 2-year average invested capital."
        elif fid == "roce":
            inputs = ["ebit", "total_assets", "current_liabilities"]
            null_rule = "Null if capital employed (total assets - current liabilities) <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Return on Capital Employed (ROCE) measures operating profitability relative to net capital invested in the business. Calculated as Operating Profit (EBIT) divided by Capital Employed (Total Assets minus Current Liabilities)."
        elif fid == "net_profit_margin":
            inputs = ["net_profit", "revenue"]
            null_rule = "Null if revenue <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Net Profit Margin represents the percentage of top-line revenue that translates into bottom-line profit after all operating costs, taxes, and interest expenses. Calculated as Net Profit divided by Total Revenue."
        elif fid == "ebitda_margin":
            inputs = ["ebitda", "revenue"]
            null_rule = "Null if revenue <= 0 or missing"
            direction = "higher_is_better"
            glossary = "EBITDA Margin measures operating profitability before the non-cash impact of depreciation and amortization and capital structure financing costs. Calculated as EBITDA divided by Total Revenue."
        elif fid == "operating_profit_margin":
            inputs = ["operating_profit", "revenue"]
            null_rule = "Null if revenue <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Operating Profit Margin indicates core business profitability by dividing Operating Profit (EBIT) by Total Revenue, reflecting operational efficiency before taxes and financing costs."
        elif fid == "cash_flow_margin":
            inputs = ["cash_flow_operating_activities", "revenue"]
            null_rule = "Null if revenue <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Cash Flow Margin expresses operating cash generation as a percentage of total revenue, assessing how effectively reported sales convert into real cash inflows. Calculated as Operating Cash Flow divided by Total Revenue."
        elif fid == "cost_of_goods_sold":
            inputs = ["cost_of_goods_sold"]
            null_rule = "Null for financial institutions and lenders, or if missing"
            direction = "lower_is_better"
            glossary = "Cost of Goods Sold (COGS) represents the direct costs incurred in producing or manufacturing the goods sold by a business during the fiscal period. Inapplicable for banks and financial institutions."
        elif fid.startswith("5y_avg_"):
            metric_base = fid.replace("5y_avg_", "")
            inputs = [metric_base]
            null_rule = "Null if fewer than 5 consecutive fiscal years of data are available"
            direction = "higher_is_better"
            glossary = f"5-Year Average {name.replace('5Y Avg ', '')} computes the arithmetic mean of the metric over the past 5 full fiscal years (FY0 through FY-4) to smooth out cyclical swings."

    # 2. Growth
    elif category == "Growth":
        if "forward" in fid or "fwd" in fid:
            inputs = ["consensus_estimates"]
            null_rule = "Null - unavailable from official sources without consensus analyst coverage"
            direction = "higher_is_better"
            glossary = f"{name} captures forward consensus growth projections based on aggregated sell-side research estimates compared to actual prior-year performance. Unavailable from official exchange sources."
        elif fid.startswith("1y_hist"):
            metric_base = fid.replace("1y_historical_", "").replace("1y_hist_", "")
            inputs = [f"{metric_base}_fy0", f"{metric_base}_fym1"]
            null_rule = f"Null if {metric_base}[FY-1] <= 0 or missing"
            direction = "higher_is_better"
            glossary = f"1-Year Historical {name.replace('1Y Hist ', '').replace('1Y Historical ', '')} reflects the percentage change in the metric from the previous fiscal year (FY-1) to the latest reported fiscal year (FY0)."
        elif fid.startswith("5y_hist"):
            metric_base = fid.replace("5y_historical_", "").replace("5y_hist_", "")
            inputs = [f"{metric_base}_fy0", f"{metric_base}_fym5"]
            null_rule = f"Null if {metric_base}[FY-5] <= 0 or {metric_base}[FY0] <= 0 or missing"
            direction = "higher_is_better"
            glossary = f"5-Year Historical {name.replace('5Y Hist ', '').replace('5Y Historical ', '')} measures the compound annual growth rate (CAGR) over a 5-year multi-year horizon ((FY0 / FY-5)^(1/5) - 1)."
        elif fid == "3y_historical_dividend_growth":
            inputs = ["dps_fy0", "dps_fym3"]
            null_rule = "Null if DPS[FY-3] <= 0 or DPS[FY0] <= 0 or missing"
            direction = "higher_is_better"
            glossary = "3-Year Historical Dividend Growth calculates the compound annual growth rate (CAGR) of Dividends Per Share (DPS) over the trailing three fiscal years."

    # 3. Valuation
    elif category == "Valuation":
        if fid in ("pe_ratio", "ttm_pe_ratio"):
            inputs = ["close_price", "earnings_per_share"]
            null_rule = "Null if EPS <= 0 or missing"
            direction = "lower_is_better"
            glossary = f"{name} compares the current market price of a stock to its earnings per share. Lower multiples indicate potentially undervalued securities, while negative earnings yield null."
        elif fid == "forward_pe_ratio":
            inputs = ["close_price", "forward_eps"]
            null_rule = "Null - forward earnings consensus unavailable from official exchange sources"
            direction = "lower_is_better"
            glossary = "Forward PE Ratio compares current price against estimated next-twelve-months or next-fiscal-year earnings per share based on analyst consensus."
        elif fid == "pb_ratio":
            inputs = ["close_price", "book_value_per_share"]
            null_rule = "Null if book value per share <= 0 or missing"
            direction = "lower_is_better"
            glossary = "Price to Book (PB) Ratio measures the stock price relative to its net asset value (book value per share). Lower values can identify value investments or asset-heavy discounts."
        elif fid in ("ps_ratio", "price_sales"):
            inputs = ["close_price", "revenue_per_share"]
            null_rule = "Null if revenue per share <= 0 or missing"
            direction = "lower_is_better"
            glossary = "Price to Sales (PS) Ratio measures market value against top-line sales per share, widely used for early-stage or cyclical companies with volatile net earnings."
        elif fid == "forward_ps_ratio":
            inputs = ["close_price", "forward_revenue"]
            null_rule = "Null - forward sales consensus unavailable from official exchange sources"
            direction = "lower_is_better"
            glossary = "Forward PS Ratio measures current price against estimated forward sales per share."
        elif fid == "dividend_yield":
            inputs = ["dividend_per_share", "close_price"]
            null_rule = "Null if close_price <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Dividend Yield expresses the annual dividend income paid per share as a percentage of the current market price ((DPS / Price) * 100)."
        elif fid == "enterprise_value":
            inputs = ["market_cap", "total_debt", "minority_interest", "cash_short_term_investments"]
            null_rule = "Null if market cap or balance sheet components missing"
            direction = "neutral"
            glossary = "Enterprise Value (EV) measures the total economic value of a firm (Market Cap + Total Debt + Minority Interest - Cash & Short-term Investments)."
        elif fid in ("ev_ebitda_ratio", "ev_ebit_ratio", "ev_revenue_ratio"):
            denom = fid.split("_")[1].upper()
            inputs = ["enterprise_value", denom.lower()]
            null_rule = f"Null if {denom.lower()} <= 0 or EV <= 0 or missing"
            direction = "lower_is_better"
            glossary = f"EV to {denom} evaluates the total enterprise value relative to operational cash generation ({denom}), normalizing across capital structure differences."
        elif fid in ("ev_free_cash_flow", "price_free_cash_flow", "price_cfo"):
            inputs = ["market_cap", "free_cash_flow", "cash_flow_operating_activities"]
            null_rule = "Null if denominator cash flow <= 0 or missing"
            direction = "lower_is_better"
            glossary = f"{name} measures firm market valuation against underlying cash generation (free cash flow or operating cash flow)."
        elif fid == "ev_invested_capital":
            inputs = ["enterprise_value", "invested_capital"]
            null_rule = "Null if invested capital <= 0 or missing"
            direction = "lower_is_better"
            glossary = "EV to Invested Capital compares enterprise value to total capital employed (Equity + Debt + Minority Interest), analogous to Tobin's Q."
        elif "premium_vs_sector" in fid or "premium_vs_sub_sector" in fid:
            inputs = [fid.split("_premium")[0], "benchmark_multiple"]
            null_rule = "Null if stock multiple or sector benchmark is missing or non-positive"
            direction = "lower_is_better"
            glossary = f"{name} computes the percentage premium or discount of the stock multiple relative to its industry benchmark ((Multiple / Sector Benchmark - 1) * 100)."
        elif "yield_vs_sector" in fid or "yield_vs_sub_sector" in fid:
            inputs = ["dividend_yield", "sector_dividend_yield"]
            null_rule = "Null if stock yield or sector yield is missing"
            direction = "higher_is_better"
            glossary = f"{name} calculates the percentage-point difference between the stock's dividend yield and its benchmark yield (Stock Yield minus Sector Yield)."
        elif fid.startswith("sector_"):
            inputs = [fid.replace("sector_", "")]
            null_rule = "Null if fewer than 2 peers exist in the sector"
            direction = "neutral"
            glossary = f"{name} represents the market-wide median multiple computed across all actively traded peers within the sector."

    # 4. Ownership
    elif category == "Ownership":
        if "change" in fid:
            holder = fid.split("_")[0].upper()
            period = "3 months" if "3m" in fid else "6 months"
            inputs = [f"{holder.lower()}_holding_current", f"{holder.lower()}_holding_prev"]
            null_rule = "Null if comparative quarterly shareholding filings are unavailable"
            direction = "higher_is_better"
            glossary = f"{name} measures the absolute percentage-point change in {holder} equity ownership over the trailing {period}."
        elif "bulk_deals" in fid or "insider_trades" in fid:
            period = "1 month" if "1m" in fid else ("3 months" if "3m" in fid else "6 months")
            inputs = ["trades_signed_shares", "shares_outstanding"]
            null_rule = "Null if no disclosure data or shares outstanding missing"
            direction = "higher_is_better"
            glossary = f"{name} computes the cumulative net percentage of company equity traded through official disclosures over {period}."
        elif fid == "pledged_promoter_holdings":
            inputs = ["pledged_shares", "promoter_shares"]
            null_rule = "Null if promoter shares <= 0 or missing"
            direction = "lower_is_better"
            glossary = "Pledged Promoter Holdings indicates what percentage of the promoter group's equity stake is encumbered or pledged as collateral for debt financing."
        elif fid == "no_of_shareholders":
            inputs = ["total_shareholders"]
            null_rule = "Null if shareholding filing missing"
            direction = "neutral"
            glossary = "Total number of equity shareholder accounts registered in the company's official depository and registrar records."
        else:
            inputs = ["shareholding_pattern"]
            null_rule = "Null if quarterly shareholding filing is unavailable"
            direction = "higher_is_better" if "promoter" in fid or "institutional" in fid or "fund" in fid else "neutral"
            glossary = f"{name} represents the percentage of total outstanding equity owned by this investor category according to official quarterly filings."

    # 5. Futures & Options
    elif category == "Futures & Options":
        null_rule = "Null for cash-only securities; valid for F&O-eligible securities only"
        if fid == "lot_size":
            inputs = ["fno_contract_master"]
            direction = "neutral"
            glossary = "Official exchange-mandated standardized market lot size for trading derivative futures and options contracts on this underlying security."
        elif fid == "future_close_price":
            inputs = ["fno_bhavcopy_near_price"]
            direction = "neutral"
            glossary = "Daily settlement price for the active near-month futures contract traded on the exchange."
        elif fid in ("future_volume", "future_open_interest"):
            inputs = ["fno_bhavcopy"]
            direction = "neutral"
            glossary = f"Total daily traded contract volume or open interest recorded in the active near-month futures contract."
        elif fid == "fair_value":
            inputs = ["close_price", "mibor_rate", "days_to_expiry"]
            direction = "neutral"
            glossary = "Theoretical fair value price of the near-month futures contract calculated using the cost-of-carry model (Spot * (1 + r * days/365)) with FBIL 3M MIBOR."
        elif fid == "fair_value_spread":
            inputs = ["fair_value", "future_close_price"]
            direction = "neutral"
            glossary = "Difference between the theoretical cost-of-carry fair value and the actual traded futures price (Fair Value minus Futures Price)."
        elif fid == "basis":
            inputs = ["future_close_price", "close_price"]
            direction = "neutral"
            glossary = "Derivative basis representing the spread between the futures price and the underlying spot closing price (Futures Price minus Spot Price)."
        elif fid == "cash_carry_profit":
            inputs = ["future_close_price", "fair_value"]
            direction = "neutral"
            glossary = "Theoretical arbitrage profit available by holding spot equity and shorting futures to expiration (Futures Price minus Fair Value)."
        elif fid == "rollover_cost":
            inputs = ["future_next_price", "future_near_price"]
            direction = "neutral"
            glossary = "Cost incurred by market participants when rolling open futures positions to the subsequent expiration cycle ((Next Month Price / Near Month Price) - 1)."
        elif fid == "percentage_rollover":
            inputs = ["oi_near", "oi_next", "oi_far"]
            direction = "neutral"
            glossary = "Percentage of open interest successfully transferred into the next expiration cycle relative to total open contracts across all active months."
        elif fid == "calendar_spread":
            inputs = ["future_mid_price", "future_near_price"]
            direction = "neutral"
            glossary = "Spread between the settlement prices of the mid-month and near-month derivative contracts (Mid-Month Price minus Near-Month Price)."
        elif fid == "put_call_ratio":
            inputs = ["total_put_oi", "total_call_oi"]
            null_rule = "Null if total call open interest <= 0 or not F&O eligible"
            direction = "neutral"
            glossary = "Put Call Ratio (PCR) measures total put open interest divided by total call open interest across all strikes and expiries, widely used as a market sentiment indicator."
        elif "change_in" in fid:
            inputs = ["fno_bhavcopy_series"]
            direction = "neutral"
            glossary = f"Percentage change in open interest or traded volume across active derivative contracts over the specified daily (1D) or weekly (1W) period."
        elif "strike" in fid:
            inputs = ["fno_strike_matrix"]
            direction = "neutral"
            glossary = f"Key option strike price exhibiting the highest open interest or the largest relative open interest accumulation across call or put series."
        else:
            inputs = ["fno_bhavcopy"]
            direction = "neutral"
            glossary = f"{name} is an official exchange-derived derivative indicator for F&O-eligible instruments."

    # 6. Price and Volume
    elif category == "Price and Volume":
        if fid == "market_cap":
            inputs = ["close_price", "shares_outstanding"]
            null_rule = "Null if close price or shares outstanding missing"
            direction = "neutral"
            glossary = "Total market capitalization expressed in Rs Crores, calculated as the closing market price multiplied by total shares outstanding divided by 10,000,000."
        elif fid == "close_price":
            inputs = ["bhavcopy_close"]
            null_rule = "Null if stock unquoted or missing bhavcopy"
            direction = "neutral"
            glossary = "Official end-of-day closing price reported in the exchange bhavcopy."
        elif "return_vs_nifty" in fid:
            inputs = ["stock_return", "nifty_return"]
            direction = "higher_is_better"
            glossary = f"Excess performance of the stock over the Nifty 50 benchmark over the specified trailing timeframe (Stock % Return minus Nifty 50 % Return)."
        elif "return" in fid or "cagr" in fid:
            inputs = ["close_price_series"]
            direction = "higher_is_better"
            glossary = f"{name} measures the historical percentage price appreciation or compound annual return over the designated holding horizon."
        elif fid == "away_from_52w_high":
            inputs = ["close_price", "52w_high"]
            null_rule = "Null if 52-week high is missing or zero"
            direction = "lower_is_better"
            glossary = "Percentage discount from the 52-week peak price ((52W High / Close) - 1 * 100), indicating drawdown from yearly highs."
        elif fid == "away_from_52w_low":
            inputs = ["close_price", "52w_low"]
            null_rule = "Null if 52-week low is missing or zero"
            direction = "higher_is_better"
            glossary = "Percentage gain from the 52-week bottom price ((Close / 52W Low) - 1 * 100), measuring recovery momentum."
        elif "volume" in fid:
            inputs = ["daily_volume_series"]
            direction = "neutral"
            glossary = f"{name} tracks the number of equity shares traded on the exchange over the specified trading window."
        elif fid == "face_value":
            inputs = ["security_master"]
            direction = "neutral"
            glossary = "Nominal or par value assigned to each equity share by the issuing corporation."

    # 7. Financial Ratios
    elif category == "Financial Ratios":
        if fid == "current_ratio":
            inputs = ["total_current_assets", "total_current_liabilities"]
            null_rule = "Null for financial institutions or if current liabilities <= 0"
            direction = "higher_is_better"
            glossary = "Current Ratio tests short-term liquidity by dividing Total Current Assets by Total Current Liabilities. Inapplicable for banks and insurers."
        elif fid == "quick_ratio":
            inputs = ["total_current_assets", "total_inventory", "total_current_liabilities"]
            null_rule = "Null for financial institutions or if current liabilities <= 0"
            direction = "higher_is_better"
            glossary = "Quick Ratio (Acid Test) evaluates immediate liquidity by excluding inventory from current assets ((Current Assets - Inventory) / Current Liabilities)."
        elif fid in ("debt_to_equity", "long_term_debt_to_equity"):
            inputs = ["total_debt", "total_equity"]
            null_rule = "Null for financial institutions or if equity <= 0"
            direction = "lower_is_better"
            glossary = "Debt to Equity ratio measures financial leverage by dividing total debt by total equity capital. Not applicable to banks or financial lenders."
        elif fid == "interest_coverage_ratio":
            inputs = ["ebit", "interest_expense"]
            null_rule = "Null if interest expense <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Interest Coverage Ratio measures the margin of safety for debt servicing (Operating Profit (EBIT) divided by Interest Expense)."
        elif fid == "cash_conversion_cycle":
            inputs = ["days_of_inventory_outstanding", "days_of_sales_outstanding", "days_payable_outstanding"]
            null_rule = "Null for financial institutions or missing working capital ratios"
            direction = "lower_is_better"
            glossary = "Cash Conversion Cycle (CCC) quantifies the days required to turn capital invested into cash inflows (DIO + DSO - DPO)."
        elif fid in ("days_of_inventory_outstanding", "days_of_sales_outstanding", "days_payable_outstanding"):
            inputs = ["balance_sheet", "income_statement"]
            null_rule = "Null for financial institutions or zero denominator"
            direction = "lower_is_better" if "payable" not in fid else "higher_is_better"
            glossary = f"{name} measures operational efficiency in working capital management over the fiscal year."
        elif fid == "earning_power":
            inputs = ["ebit", "total_assets"]
            null_rule = "Null if total assets <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Basic Earning Power measures operational earning capacity independent of tax and leverage (EBIT / Total Assets)."
        elif "turnover" in fid:
            inputs = ["revenue", "balance_sheet_asset"]
            null_rule = "Null if denominator asset <= 0 or missing"
            direction = "higher_is_better"
            glossary = f"{name} measures asset productivity by computing the ratio of annual revenue to the deployed asset base."
        elif fid == "net_income_liabilities":
            inputs = ["net_income", "total_liabilities"]
            null_rule = "Null if total liabilities <= 0 or missing"
            direction = "higher_is_better"
            glossary = "Net Income to Liabilities ratio gauges insolvency risk by comparing net profit against total debt and liabilities."

    # 8. Technical Indicators
    elif category == "Technical Indicators":
        if "sma" in fid or "ema" in fid:
            inputs = ["close_price_series"]
            null_rule = "Null if trading history is shorter than required lookback period"
            direction = "neutral"
            glossary = f"{name} calculates the trend baseline using an arithmetic or exponential moving average of closing prices over the specified window."
        elif "price_above" in fid:
            inputs = ["close_price", "moving_average"]
            direction = "higher_is_better"
            glossary = f"Percentage distance between the current market price and the benchmark moving average ((Close / MA - 1) * 100)."
        elif fid in ("rsi_14d", "rsi_exponential_14d"):
            inputs = ["close_price_series"]
            null_rule = "Null if fewer than 15 trading days available"
            direction = "neutral"
            glossary = "Relative Strength Index (RSI) measures price momentum on a 0-100 scale, highlighting overbought (>70) and oversold (<30) market conditions."
        elif fid == "adx_rating":
            inputs = ["high_series", "low_series", "close_series"]
            null_rule = "Null if fewer than 28 trading days available"
            direction = "higher_is_better"
            glossary = "Average Directional Index (ADX) quantifies trend strength on a 0-100 scale regardless of directional movement."
        elif "macd" in fid:
            inputs = ["close_price_series"]
            direction = "neutral"
            glossary = "Moving Average Convergence Divergence (MACD) tracks momentum shifts through exponential moving average spreads."
        elif "bollinger" in fid:
            inputs = ["close_price_series"]
            direction = "neutral"
            glossary = f"Distance of current price from the upper or lower 2-standard-deviation Bollinger Band over 20 trading days."
        elif fid == "from_parabolic_sar":
            inputs = ["high_series", "low_series", "close_series"]
            direction = "higher_is_better"
            glossary = "Percentage distance of closing price from the trailing Parabolic SAR level ((Close / SAR - 1) * 100)."
        elif fid == "williams_r":
            inputs = ["high_series", "low_series", "close_series"]
            direction = "neutral"
            glossary = "Williams %R momentum indicator oscillating between 0 and -100 ((Highest High - Close) / (Highest High - Lowest Low) * -100)."
        elif "stochastic" in fid:
            inputs = ["high_series", "low_series", "close_series"]
            direction = "neutral"
            glossary = "Stochastic oscillator measuring closing price location relative to high-low range over trailing 14 trading sessions."
        elif fid == "1w_change_in_obv":
            inputs = ["close_series", "volume_series"]
            direction = "higher_is_better"
            glossary = "Weekly percentage change in On-Balance Volume (OBV), measuring volume accumulation or distribution flow."
        elif fid == "1w_change_in_ad_line":
            inputs = ["high_series", "low_series", "close_series", "volume_series"]
            direction = "higher_is_better"
            glossary = "Weekly percentage change in the Accumulation/Distribution Line based on money flow volume."
        elif fid == "super_trend":
            inputs = ["high_series", "low_series", "close_series"]
            direction = "higher_is_better"
            glossary = "SuperTrend trend-following volatility indicator based on Average True Range (ATR 10, Multiplier 3)."
        elif fid == "1y_max_loss":
            inputs = ["close_price_series"]
            direction = "lower_is_better"
            glossary = "Maximum peak-to-trough price drawdown experienced by the stock over the trailing 250 trading sessions."
        elif fid in ("volatility", "volatility_vs_nifty"):
            inputs = ["close_price_series", "nifty_close_series"]
            direction = "lower_is_better"
            glossary = "Annualized historical volatility computed from daily log returns over trailing 200 trading sessions."
        elif fid in ("beta", "alpha", "sharpe_ratio"):
            inputs = ["weekly_closes_104w", "nifty_weekly_closes_104w"]
            direction = "higher_is_better" if fid != "beta" else "neutral"
            glossary = f"{name} evaluates risk-adjusted return and benchmark sensitivity using 104 weekly closes relative to the Nifty 50."
        elif fid == "vwap":
            inputs = ["bhavcopy_traded_value", "bhavcopy_traded_qty"]
            direction = "neutral"
            glossary = "Intraday Volume Weighted Average Price (VWAP) reported in the exchange bhavcopy."
        elif fid == "relative_volume":
            inputs = ["volume_10d_avg", "volume_91d_avg"]
            direction = "neutral"
            glossary = "Ratio of average daily volume over the past 10 trading sessions compared to the 91-day historical baseline."

    # 9. Special (Quant Ranks)
    elif category == "Special":
        inputs = ["price_history", "fundamentals", "sector_peers"]
        null_rule = "Null if required historical data or fundamental ratios missing"
        direction = "higher_is_better"
        glossary = f"{name} is an open quantitative composite score (0-100 percentile or 1-10) evaluated across the active market universe."

    # 10. Analyst Ratings
    elif category == "Analyst Ratings":
        inputs = ["analyst_consensus"]
        null_rule = "Null - sell-side research coverage unavailable from official exchange sources"
        direction = "higher_is_better"
        glossary = f"{name} reports consensus analyst sentiment. Unavailable from official exchange data; can be populated from user spreadsheet uploads."

    # 11. ETFs
    elif category == "ETFs":
        null_rule = "Null for corporate equities; applicable exclusively to Exchange Traded Funds (ETFs)"
        if fid == "expense_ratio":
            inputs = ["amfi_ter_filing"]
            direction = "lower_is_better"
            glossary = "Total Expense Ratio (TER) officially published by AMFI and asset management companies."
        elif fid == "tracking_error":
            inputs = ["etf_nav_series", "benchmark_index_series"]
            direction = "lower_is_better"
            glossary = "Annualized standard deviation of daily return differences between the ETF NAV and its underlying benchmark index."

    # 12. Income Statement
    elif category == "Income Statement":
        inputs = ["xbrl_income_statement"]
        null_rule = "Null if financial report missing or not disclosed"
        direction = "higher_is_better" if "cost" not in fid and "expense" not in fid else "lower_is_better"
        glossary = f"Official audited income statement line item ({name}) reported in periodic corporate financial filings."

    # 13. Balance Sheet & Cash Flow
    elif category == "Balance Sheet & Cash Flow":
        inputs = ["xbrl_balance_sheet_cashflow"]
        null_rule = "Null if balance sheet filing missing or inapplicable to sector"
        direction = "neutral"
        glossary = f"Official audited balance sheet or cash flow statement line item ({name}) disclosed in regulatory corporate filings."

    return {
        "id": fid,
        "name": name,
        "category": category,
        "unit": unit,
        "formula": formula,
        "inputs": inputs,
        "null_rule": null_rule,
        "direction_of_goodness": direction,
        "glossary": glossary,
        "availability": availability,
    }


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    filters = raw.get("filters", {})
    enriched = {}

    for fid, f in filters.items():
        name = f.get("name", fid)
        cat = f.get("category", "General")
        unit = f.get("unit", "")
        formula = f.get("formula", "")
        avail = f.get("availability", "Computed-from-official")
        in_sc = f.get("in_screenshot", False)
        locked = f.get("locked_in_original", False)
        needs_src = f.get("needs_official_source", True)
        freq = f.get("frequency", "Annual")

        meta = build_metadata(fid, name, cat, unit, formula, avail)
        meta["in_screenshot"] = in_sc
        meta["locked_in_original"] = locked
        meta["needs_official_source"] = needs_src
        meta["frequency"] = freq
        enriched[fid] = meta

    out_yaml = {"version": "2.0", "filters": enriched}

    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        yaml.safe_dump(out_yaml, fh, sort_keys=False, allow_unicode=True)

    # Sync to frontend JSON
    WEB_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WEB_JSON_PATH, "w", encoding="utf-8") as fh:
        json.dump(out_yaml, fh, indent=2)

    print(f"Enriched {len(enriched)} filters in {REGISTRY_PATH}")
    print(f"Synced JSON to {WEB_JSON_PATH}")


if __name__ == "__main__":
    main()
