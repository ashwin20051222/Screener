# FILTER_CATALOG.md — Master Screener Filter Catalog

> Single source of truth union of all filters visible in reference screenshots and specified in Build Prompt Section 10.
> Total filters: **255** across 13 categories.

## Category Summary

| Category | Total | In Screenshot | Locked in Orig. | Official-direct | Computed | Approx. | Unavailable |
|----------|-------|---------------|-----------------|-----------------|----------|---------|-------------|
| Profitability | 16 | 14 | 0 | 1 | 15 | 0 | 0 |
| Growth | 13 | 13 | 4 | 0 | 9 | 0 | 4 |
| Valuation | 27 | 27 | 10 | 0 | 25 | 0 | 2 |
| Ownership | 22 | 22 | 6 | 8 | 14 | 0 | 0 |
| Futures & Options | 28 | 28 | 21 | 6 | 22 | 0 | 0 |
| Price and Volume | 20 | 20 | 0 | 3 | 17 | 0 | 0 |
| Financial Ratios | 14 | 14 | 3 | 0 | 14 | 0 | 0 |
| Special | 5 | 5 | 5 | 0 | 0 | 5 | 0 |
| Analyst Ratings | 6 | 6 | 6 | 0 | 0 | 0 | 6 |
| Technical Indicators | 33 | 0 | 0 | 1 | 32 | 0 | 0 |
| Balance Sheet & Cash Flow | 39 | 0 | 0 | 39 | 0 | 0 | 0 |
| ETFs | 2 | 2 | 0 | 1 | 1 | 0 | 0 |
| Income Statement | 30 | 23 | 0 | 21 | 9 | 0 | 0 |
| **Total** | **255** | **174** | **55** | **80** | **158** | **5** | **12** |

## Profitability

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `return_on_equity` | Return on Equity | % | Yes | No | Yes | `Computed-from-official` | Annual/TTM |
| `return_on_assets` | Return on Assets | % | Yes | No | Yes | `Computed-from-official` | Annual/TTM |
| `return_on_investment` | Return on Investment | % | Yes | No | Yes | `Computed-from-official` | Annual/TTM |
| `roce` | ROCE | % | Yes | No | Yes | `Computed-from-official` | Annual/TTM |
| `net_profit_margin` | Net Profit Margin | % | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `ebitda_margin` | EBITDA Margin | % | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `operating_profit_margin` | Operating Profit Margin | % | No | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `cash_flow_margin` | Cash Flow Margin | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `cost_of_goods_sold` | Cost of Goods Sold | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `5y_avg_ebitda_margin` | 5Y Avg EBITDA Margin | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_net_profit_margin` | 5Y Avg Net Profit Margin | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_return_on_equity` | 5Y Avg Return on Equity | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_return_on_assets` | 5Y Avg Return on Assets | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_return_on_investment` | 5Y Avg Return on Investment | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_cash_flow_margin` | 5Y Avg Cash Flow Margin | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_avg_operating_profit_margin` | 5Y Avg Operating Profit Margin | % | No | No | Yes | `Computed-from-official` | Annual |

## Growth

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `1y_forward_revenue_growth` | 1Y Forward Revenue Growth | % | Yes | 🔒 Yes | No | `Unavailable` | Annual |
| `1y_hist_op_cash_flow_growth` | 1Y Hist Op. Cash Flow Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `1y_forward_ebitda_growth` | 1Y Forward EBITDA Growth | % | Yes | 🔒 Yes | No | `Unavailable` | Annual |
| `1y_historical_eps_growth` | 1Y Historical EPS Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `1y_historical_revenue_growth` | 1Y Historical Revenue Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `1y_fwd_op_cash_flow_growth` | 1Y Fwd Op. Cash Flow Growth | % | Yes | 🔒 Yes | No | `Unavailable` | Annual |
| `5y_historical_ebitda_growth` | 5Y Historical EBITDA Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_hist_op_cash_flow_growth` | 5Y Hist Op. Cash Flow Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `3y_historical_dividend_growth` | 3Y Historical Dividend Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_historical_eps_growth` | 5Y Historical EPS Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `5y_historical_revenue_growth` | 5Y Historical Revenue Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `1y_historical_ebitda_growth` | 1Y Historical EBITDA Growth | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `1y_forward_eps_growth` | 1Y Forward EPS Growth | % | Yes | 🔒 Yes | No | `Unavailable` | Annual |

## Valuation

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `pe_ratio` | PE Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ttm_pe_ratio` | TTM PE Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `forward_pe_ratio` | Forward PE Ratio |  | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `pb_ratio` | PB Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ps_ratio` | PS Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `forward_ps_ratio` | Forward PS Ratio |  | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `dividend_yield` | Dividend Yield | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `ev_ebitda_ratio` | EV/EBITDA Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ev_ebit_ratio` | EV / EBIT Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ev_revenue_ratio` | EV / Revenue Ratio |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ev_free_cash_flow` | EV / Free Cash Flow |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `ev_invested_capital` | EV / Invested Capital |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `enterprise_value` | Enterprise Value | Rs Cr | Yes | No | Yes | `Computed-from-official` | Daily |
| `price_free_cash_flow` | Price / Free Cash Flow |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `price_cfo` | Price / CFO |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `price_sales` | Price / Sales |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `pe_premium_vs_sector` | PE Premium vs Sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `pb_premium_vs_sector` | PB Premium vs Sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `ps_premium_vs_sector` | PS Premium vs Sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `dividend_yield_vs_sector` | Dividend Yield vs Sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `pe_premium_vs_sub_sector` | PE Premium vs Sub-sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `pb_premium_vs_sub_sector` | PB Premium vs Sub-sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `ps_premium_vs_sub_sector` | PS Premium vs Sub-sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `dividend_yield_vs_sub_sector` | Dividend Yield vs Sub-sector | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `sector_dividend_yield` | Sector Dividend Yield | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `sector_pb` | Sector PB |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `sector_pe` | Sector PE |  | Yes | No | Yes | `Computed-from-official` | Daily |

## Ownership

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `mutual_fund_holding` | Mutual Fund Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `domestic_institutional_holding` | Domestic Institutional Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `foreign_institutional_holding` | Foreign Institutional Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `promoter_holding` | Promoter Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `pledged_promoter_holdings` | Pledged Promoter Holdings | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `retail_investor_holding` | Retail Investor Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `insurance_firms_holding` | Insurance Firms Holding | % | Yes | No | Yes | `Official-direct` | Quarterly |
| `no_of_shareholders` | No. of Shareholders |  | Yes | No | Yes | `Official-direct` | Quarterly |
| `mf_holding_change_3m` | MF Holding Change – 3M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `mf_holding_change_6m` | MF Holding Change – 6M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `dii_holding_change_3m` | DII Holding Change – 3M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `dii_holding_change_6m` | DII Holding Change – 6M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `fii_holding_change_3m` | FII Holding Change – 3M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `fii_holding_change_6m` | FII Holding Change – 6M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `promoter_holding_change_3m` | Promoter Holding Change – 3M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `promoter_holding_change_6m` | Promoter Holding Change – 6M | % | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `insider_trades_1m_cumulative` | Insider Trades - 1M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `insider_trades_3m_cumulative` | Insider Trades - 3M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `insider_trades_6m_cumulative` | Insider Trades - 6M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `bulk_deals_1m_cumulative` | Bulk Deals - 1M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `bulk_deals_3m_cumulative` | Bulk Deals - 3M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `bulk_deals_6m_cumulative` | Bulk Deals - 6M Cumulative | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |

## Futures & Options

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `lot_size` | Lot Size |  | Yes | No | Yes | `Official-direct` | Monthly |
| `future_close_price` | Future Close Price | Rs | Yes | No | Yes | `Official-direct` | Daily |
| `future_volume` | Future Volume |  | Yes | No | Yes | `Official-direct` | Daily |
| `future_open_interest` | Future Open Interest |  | Yes | No | Yes | `Official-direct` | Daily |
| `fair_value` | Fair Value | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `fair_value_spread` | Fair Value Spread | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `basis` | Basis | Rs | Yes | No | Yes | `Computed-from-official` | Daily |
| `rollover_cost` | Rollover Cost | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `percentage_rollover` | Percentage Rollover | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `calendar_spread` | Calendar Spread | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `cash_carry_profit` | Cash & Carry Profit | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `put_call_ratio` | Put Call Ratio |  | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `call_open_interest` | Call Open Interest |  | Yes | No | Yes | `Official-direct` | Daily |
| `put_open_interest` | Put Open Interest |  | Yes | No | Yes | `Official-direct` | Daily |
| `1d_change_in_future_oi` | 1D Change in Future OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1w_change_in_future_oi` | 1W Change in Future OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1d_change_in_future_volume` | 1D Change in Future Volume | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1w_change_in_future_volume` | 1W Change in Future Volume | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1d_change_in_call_oi` | 1D Change in Call OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1w_change_in_call_oi` | 1W Change in Call OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1d_change_in_put_oi` | 1D Change in Put OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `1w_change_in_put_oi` | 1W Change in Put OI | % | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_call_oi_strike` | Highest Call OI Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_put_oi_strike` | Highest Put OI Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_1d_oi_change_ce_strike` | Highest 1D OI Change CE Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_1d_oi_change_pe_strike` | Highest 1D OI Change PE Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_1w_oi_change_ce_strike` | Highest 1W OI Change CE Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |
| `highest_1w_oi_change_pe_strike` | Highest 1W OI Change PE Strike | Rs | Yes | 🔒 Yes | Yes | `Computed-from-official` | Daily |

## Price and Volume

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `market_cap` | Market Cap | Rs Cr | Yes | No | Yes | `Computed-from-official` | Daily |
| `close_price` | Close Price | Rs | Yes | No | Yes | `Official-direct` | Daily |
| `1d_return` | 1D Return | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1w_return` | 1W Return | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1m_return` | 1M Return | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `6m_return` | 6M Return | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1y_return` | 1Y Return | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `5y_cagr` | 5Y CAGR | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1w_return_vs_nifty` | 1W Return vs Nifty | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1m_return_vs_nifty` | 1M Return vs Nifty | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `6m_return_vs_nifty` | 6M Return vs Nifty | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1y_return_vs_nifty` | 1Y Return vs Nifty | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `away_from_52w_high` | % Away From 52W High | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `away_from_52w_low` | % Away From 52W Low | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `daily_volume` | Daily Volume |  | Yes | No | Yes | `Official-direct` | Daily |
| `1m_average_volume` | 1M Average Volume |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `3m_average_volume` | 3M Average Volume |  | Yes | No | Yes | `Computed-from-official` | Daily |
| `1d_change_in_volume` | 1D Change in Volume | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `1w_change_in_volume` | 1W Change in Volume | % | Yes | No | Yes | `Computed-from-official` | Daily |
| `face_value` | Face value | Rs | Yes | No | Yes | `Official-direct` | Static/Infrequent |

## Financial Ratios

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `current_ratio` | Current Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `quick_ratio` | Quick Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `debt_to_equity` | Debt to Equity |  | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `long_term_debt_to_equity` | Long Term Debt to Equity |  | Yes | No | Yes | `Computed-from-official` | Annual |
| `interest_coverage_ratio` | Interest Coverage Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `cash_conversion_cycle` | Cash Conversion Cycle | days | Yes | No | Yes | `Computed-from-official` | Annual |
| `net_income_liabilities` | Net Income / Liabilities |  | Yes | No | Yes | `Computed-from-official` | Annual |
| `working_capital_turnover_ratio` | Working Capital Turnover Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual |
| `inventory_turnover_ratio` | Inventory Turnover Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual |
| `asset_turnover_ratio` | Asset Turnover Ratio |  | Yes | No | Yes | `Computed-from-official` | Annual |
| `days_of_inventory_outstanding` | Days of Inventory Outstanding | days | Yes | 🔒 Yes | Yes | `Computed-from-official` | Annual |
| `days_of_sales_outstanding` | Days of Sales Outstanding | days | Yes | 🔒 Yes | Yes | `Computed-from-official` | Annual |
| `days_payable_outstanding` | Days Payable Outstanding | days | Yes | 🔒 Yes | Yes | `Computed-from-official` | Annual |
| `earning_power` | Earning Power |  | Yes | No | Yes | `Computed-from-official` | Annual |

## Special

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `price_momentum_rank` | Price Momentum Rank | rank | Yes | 🔒 Yes | Yes | `Approximate` | Daily |
| `fundamental_score` | Fundamental Score | score | Yes | 🔒 Yes | Yes | `Approximate` | Quarterly |
| `value_momentum_rank` | Value Momentum Rank | rank | Yes | 🔒 Yes | Yes | `Approximate` | Daily |
| `earnings_quality_rank` | Earnings Quality Rank | rank | Yes | 🔒 Yes | Yes | `Approximate` | Annual/Quarterly |
| `price_to_intrinsic_value_rank` | Price to Intrinsic Value Rank | rank | Yes | 🔒 Yes | Yes | `Approximate` | Daily |

## Analyst Ratings

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `percentage_upside` | Percentage Upside | % | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `percentage_buy_recos` | Percentage Buy Reco's | % | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `percentage_hold_recos` | Percentage Hold Reco's | % | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `percentage_sell_recos` | Percentage Sell Reco's | % | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `no_of_analysts_with_buy_reco` | No. of analysts with buy reco |  | Yes | 🔒 Yes | No | `Unavailable` | Daily |
| `total_no_of_analysts` | Total no. of analysts |  | Yes | 🔒 Yes | No | `Unavailable` | Daily |

## Technical Indicators

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `1y_max_loss` | 1Y Max Loss | % | No | No | Yes | `Computed-from-official` | Daily |
| `sma_10d` | SMA 10D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `sma_50d` | SMA 50D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `sma_100d` | SMA 100D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `sma_200d` | SMA 200D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `ema_10d` | EMA 10D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `ema_50d` | EMA 50D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `ema_100d` | EMA 100D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `ema_200d` | EMA 200D | Rs | No | No | Yes | `Computed-from-official` | Daily |
| `alpha` | Alpha | % | No | No | Yes | `Computed-from-official` | Daily |
| `beta` | Beta |  | No | No | Yes | `Computed-from-official` | Daily |
| `sharpe_ratio` | Sharpe Ratio |  | No | No | Yes | `Computed-from-official` | Daily |
| `relative_volume` | Relative Volume |  | No | No | Yes | `Computed-from-official` | Daily |
| `volatility` | Volatility | % | No | No | Yes | `Computed-from-official` | Daily |
| `volatility_vs_nifty` | Volatility vs Nifty | % | No | No | Yes | `Computed-from-official` | Daily |
| `vwap` | Volume Weighted Average Price | Rs | No | No | Yes | `Official-direct` | Daily |
| `price_above_1m_sma` | % Price above 1M SMA | % | No | No | Yes | `Computed-from-official` | Daily |
| `price_above_12m_sma` | % Price above 12M SMA | % | No | No | Yes | `Computed-from-official` | Daily |
| `price_above_1m_ema` | % Price above 1M EMA | % | No | No | Yes | `Computed-from-official` | Daily |
| `rsi_14d` | RSI 14D |  | No | No | Yes | `Computed-from-official` | Daily |
| `rsi_exponential_14d` | RSI Exponential 14D |  | No | No | Yes | `Computed-from-official` | Daily |
| `adx_rating` | ADX Rating |  | No | No | Yes | `Computed-from-official` | Daily |
| `macd_line_1` | MACD Line 1 |  | No | No | Yes | `Computed-from-official` | Daily |
| `macd_line_2` | MACD Line 2 |  | No | No | Yes | `Computed-from-official` | Daily |
| `from_upper_bollinger_band` | % From Upper Bollinger Band | % | No | No | Yes | `Computed-from-official` | Daily |
| `from_lower_bollinger_band` | % From Lower Bollinger Band | % | No | No | Yes | `Computed-from-official` | Daily |
| `from_parabolic_sar` | % From Parabolic SAR | % | No | No | Yes | `Computed-from-official` | Daily |
| `williams_r` | Williams %R | % | No | No | Yes | `Computed-from-official` | Daily |
| `stochastic_k` | Stochastic %K | % | No | No | Yes | `Computed-from-official` | Daily |
| `stochastic_d` | Stochastic %D | % | No | No | Yes | `Computed-from-official` | Daily |
| `1w_change_in_obv` | 1W Change in On Balance Volume | % | No | No | Yes | `Computed-from-official` | Daily |
| `1w_change_in_ad_line` | 1W Change in AD Line | % | No | No | Yes | `Computed-from-official` | Daily |
| `super_trend` | Super Trend |  | No | No | Yes | `Computed-from-official` | Daily |

## Balance Sheet & Cash Flow

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `book_value` | Book Value | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `cash_short_term_investments` | Cash and Short-term Investments | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_receivables` | Total Receivables | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_inventory` | Total Inventory | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `other_current_assets` | Other Current Assets | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_current_assets` | Total Current Assets | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `net_loans` | Net Loans | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `net_ppe` | Net Property Plant Equipment | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `goodwill_intangibles` | Goodwill and Intangibles | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `long_term_investments` | Long Term Investments | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `other_assets` | Other Assets | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_assets` | Total Assets | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `accounts_payable` | Accounts Payable | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_deposits` | Total Deposits | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `other_current_liabilities` | Other Current Liabilities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_current_liabilities` | Total Current Liabilities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_long_term_debt` | Total Long Term Debt | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_debt` | Total Debt | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `deferred_income_tax` | Deferred Income Tax | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `minority_interest` | Minority Interest | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `other_liabilities` | Other Liabilities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_liabilities` | Total Liabilities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `common_stock` | Common Stock | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `additional_paid_in_capital` | Additional Paid-in Capital | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `retained_earnings` | Retained Earnings | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `other_equity` | Other Equity | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_equity` | Total Equity | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_liabilities_shareholders_equity` | Total Liabilities & Shareholders Equity | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_common_shares_outstanding` | Total Common Shares Outstanding |  | No | No | Yes | `Official-direct` | Annual/Quarterly |
| `total_preferred_shares_outstanding` | Total Preferred Shares Outstanding |  | No | No | Yes | `Official-direct` | Annual |
| `policy_liabilities` | Policy Liabilities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `changes_in_working_capital` | Changes in Working Capital | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `cash_flow_operating_activities` | Cash Flow from Operating Activities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `capital_expenditures` | Capital Expenditures | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `cash_investing_activities` | Cash from Investing Activities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `total_cash_dividends_paid` | Total Cash Dividends Paid | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `cash_financing_activities` | Cash from Financing Activities | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `foreign_exchange_effects` | Foreign Exchange Effects | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `net_change_in_cash` | Net Change in Cash | Rs Cr | No | No | Yes | `Official-direct` | Annual |

## ETFs

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `expense_ratio` | Expense Ratio | % | Yes | No | Yes | `Official-direct` | Monthly |
| `tracking_error` | Tracking Error | % | Yes | No | Yes | `Computed-from-official` | Daily |

## Income Statement

| ID | Filter Name | Unit | In Screenshot | Locked in Orig. | Needs Official | Availability | Frequency |
|---|---|---|---|---|---|---|---|
| `total_revenue` | Total Revenue | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `cost_of_revenue` | Cost of Revenue | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `gross_profit` | Gross Profit | Rs Cr | No | No | Yes | `Computed-from-official` | Annual |
| `ebitda` | EBITDA | Rs Cr | Yes | No | Yes | `Computed-from-official` | Annual |
| `depreciation_amortization` | Depreciation & Amortization | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `pbit` | PBIT | Rs Cr | Yes | No | Yes | `Computed-from-official` | Annual |
| `interest_other_items` | Interest & Other Items | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `pbt` | PBT | Rs Cr | Yes | No | Yes | `Computed-from-official` | Annual |
| `taxes_other_items` | Taxes & Other Items | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `net_income` | Net Income | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `earnings_per_share` | Earnings Per Share | Rs | Yes | No | Yes | `Official-direct` | Annual |
| `dividend_per_share` | Dividend Per Share | Rs | Yes | No | Yes | `Official-direct` | Annual |
| `payout_ratio` | Payout Ratio | % | Yes | No | Yes | `Computed-from-official` | Annual |
| `power_fuel_cost` | Power & Fuel Cost | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `raw_materials` | Raw Materials | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `operating_other_expenses` | Operating & Other expenses | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `employee_cost` | Employee Cost | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `selling_administrative_expenses` | Selling & Administrative Expenses | Rs Cr | Yes | No | Yes | `Official-direct` | Annual |
| `research_development` | Research & Development | Rs Cr | No | No | Yes | `Official-direct` | Annual |
| `interest_income` | Interest Income | Rs Cr | No | No | Yes | `Official-direct` | Annual/Quarterly |
| `total_interest_expense` | Total Interest Expense | Rs Cr | No | No | Yes | `Official-direct` | Annual/Quarterly |
| `net_interest_income` | Net Interest Income | Rs Cr | No | No | Yes | `Computed-from-official` | Annual/Quarterly |
| `loan_loss_provision` | Loan Loss Provision | Rs Cr | No | No | Yes | `Official-direct` | Annual/Quarterly |
| `total_revenue_q` | Total revenue (Q) | Rs Cr | Yes | No | Yes | `Official-direct` | Quarterly |
| `net_income_q` | Net Income (Q) | Rs Cr | Yes | No | Yes | `Official-direct` | Quarterly |
| `eps_q` | EPS (Q) | Rs | Yes | No | Yes | `Official-direct` | Quarterly |
| `ebitda_q` | EBITDA (Q) | Rs Cr | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `operating_and_other_expenses_q` | Operating and Other Expenses (Q) | Rs Cr | Yes | No | Yes | `Official-direct` | Quarterly |
| `pbit_q` | PBIT (Q) | Rs Cr | Yes | No | Yes | `Computed-from-official` | Quarterly |
| `pbt_q` | PBT (Q) | Rs Cr | Yes | No | Yes | `Computed-from-official` | Quarterly |

