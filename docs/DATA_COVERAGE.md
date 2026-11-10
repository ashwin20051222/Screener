# DATA_COVERAGE.md — Live Database Filter Coverage

> **Generated:** `2026-11-10T11:56:42+05:30`
> **Database Synced:** `True` | **All Listed Rows:** `2645` | **NIFTY100 Rows:** `100`
> **Registry Filters Checked:** `255`

## 1. Index Universes Loaded

| Index Slug | Member Count |
|---|---|
| `NIFTY100` | 100 |
| `NIFTY200` | 200 |
| `NIFTY50` | 50 |
| `NIFTY500` | 501 |
| `NIFTYMIDCAP100` | 100 |
| `NIFTYMIDCAP150` | 150 |
| `NIFTYNEXT50` | 50 |
| `NIFTYSMALLCAP100` | 100 |
| `NIFTYSMALLCAP250` | 251 |

## 2. Coverage Summary by Feeding Job (`feeds`)

| Feeds Job | Filter Count | Filters With >= 1 Value |
|---|---|---|
| `amfi` | 2 | 0 |
| `daily` | 3 | 3 |
| `deals` | 6 | 6 |
| `fno` | 24 | 0 |
| `history` | 49 | 0 |
| `manual` | 3 | 0 |
| `shp` | 17 | 17 |
| `unavailable` | 12 | 0 |
| `weekly` | 2 | 1 |
| `xbrl` | 137 | 97 |

## 3. Per-Filter Non-Null Coverage

| Filter ID | Name | Category | Availability | Feeds | All Non-Null | All % | NIFTY100 Non-Null | NIFTY100 % |
|---|---|---|---|---|---|---|---|---|
| `return_on_equity` | Return on Equity | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `return_on_assets` | Return on Assets | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `return_on_investment` | Return on Investment | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `roce` | ROCE | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `net_profit_margin` | Net Profit Margin | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ebitda_margin` | EBITDA Margin | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `operating_profit_margin` | Operating Profit Margin | Profitability | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `cash_flow_margin` | Cash Flow Margin | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `cost_of_goods_sold` | Cost of Goods Sold | Profitability | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `5y_avg_ebitda_margin` | 5Y Avg EBITDA Margin | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_avg_net_profit_margin` | 5Y Avg Net Profit Margin | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_avg_return_on_equity` | 5Y Avg Return on Equity | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_avg_return_on_assets` | 5Y Avg Return on Assets | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_avg_return_on_investment` | 5Y Avg Return on Investment | Profitability | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `5y_avg_cash_flow_margin` | 5Y Avg Cash Flow Margin | Profitability | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `5y_avg_operating_profit_margin` | 5Y Avg Operating Profit Margin | Profitability | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `1y_forward_revenue_growth` | 1Y Forward Revenue Growth | Growth | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `1y_hist_op_cash_flow_growth` | 1Y Hist Op. Cash Flow Growth | Growth | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `1y_forward_ebitda_growth` | 1Y Forward EBITDA Growth | Growth | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `1y_historical_eps_growth` | 1Y Historical EPS Growth | Growth | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `1y_historical_revenue_growth` | 1Y Historical Revenue Growth | Growth | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `1y_fwd_op_cash_flow_growth` | 1Y Fwd Op. Cash Flow Growth | Growth | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `5y_historical_ebitda_growth` | 5Y Historical EBITDA Growth | Growth | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_hist_op_cash_flow_growth` | 5Y Hist Op. Cash Flow Growth | Growth | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `3y_historical_dividend_growth` | 3Y Historical Dividend Growth | Growth | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `5y_historical_eps_growth` | 5Y Historical EPS Growth | Growth | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `5y_historical_revenue_growth` | 5Y Historical Revenue Growth | Growth | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `1y_historical_ebitda_growth` | 1Y Historical EBITDA Growth | Growth | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `1y_forward_eps_growth` | 1Y Forward EPS Growth | Growth | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `pe_ratio` | PE Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ttm_pe_ratio` | TTM PE Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `forward_pe_ratio` | Forward PE Ratio | Valuation | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `pb_ratio` | PB Ratio | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `ps_ratio` | PS Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `forward_ps_ratio` | Forward PS Ratio | Valuation | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `dividend_yield` | Dividend Yield | Valuation | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `ev_ebitda_ratio` | EV/EBITDA Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ev_ebit_ratio` | EV / EBIT Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ev_revenue_ratio` | EV / Revenue Ratio | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ev_free_cash_flow` | EV / Free Cash Flow | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `ev_invested_capital` | EV / Invested Capital | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `enterprise_value` | Enterprise Value | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `price_free_cash_flow` | Price / Free Cash Flow | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `price_cfo` | Price / CFO | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `price_sales` | Price / Sales | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pe_premium_vs_sector` | PE Premium vs Sector | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pb_premium_vs_sector` | PB Premium vs Sector | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `ps_premium_vs_sector` | PS Premium vs Sector | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `dividend_yield_vs_sector` | Dividend Yield vs Sector | Valuation | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `pe_premium_vs_sub_sector` | PE Premium vs Sub-sector | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pb_premium_vs_sub_sector` | PB Premium vs Sub-sector | Valuation | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `ps_premium_vs_sub_sector` | PS Premium vs Sub-sector | Valuation | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `dividend_yield_vs_sub_sector` | Dividend Yield vs Sub-sector | Valuation | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `sector_dividend_yield` | Sector Dividend Yield | Valuation | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `sector_pb` | Sector PB | Valuation | Computed-from-official | `xbrl` | 169 | 6.4% | 14 | 14.0% |
| `sector_pe` | Sector PE | Valuation | Computed-from-official | `xbrl` | 196 | 7.4% | 20 | 20.0% |
| `mutual_fund_holding` | Mutual Fund Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `domestic_institutional_holding` | Domestic Institutional Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `foreign_institutional_holding` | Foreign Institutional Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `promoter_holding` | Promoter Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `pledged_promoter_holdings` | Pledged Promoter Holdings | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `retail_investor_holding` | Retail Investor Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `insurance_firms_holding` | Insurance Firms Holding | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `no_of_shareholders` | No. of Shareholders | Ownership | Official-direct | `shp` | 2 | 0.1% | 2 | 2.0% |
| `mf_holding_change_3m` | MF Holding Change – 3M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `mf_holding_change_6m` | MF Holding Change – 6M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `dii_holding_change_3m` | DII Holding Change – 3M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `dii_holding_change_6m` | DII Holding Change – 6M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `fii_holding_change_3m` | FII Holding Change – 3M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `fii_holding_change_6m` | FII Holding Change – 6M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `promoter_holding_change_3m` | Promoter Holding Change – 3M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `promoter_holding_change_6m` | Promoter Holding Change – 6M | Ownership | Computed-from-official | `shp` | 2 | 0.1% | 2 | 2.0% |
| `insider_trades_1m_cumulative` | Insider Trades - 1M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `insider_trades_3m_cumulative` | Insider Trades - 3M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `insider_trades_6m_cumulative` | Insider Trades - 6M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `bulk_deals_1m_cumulative` | Bulk Deals - 1M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `bulk_deals_3m_cumulative` | Bulk Deals - 3M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `bulk_deals_6m_cumulative` | Bulk Deals - 6M Cumulative | Ownership | Computed-from-official | `deals` | 2644 | 100.0% | 100 | 100.0% |
| `lot_size` | Lot Size | Futures & Options | Official-direct | `weekly` | 0 | 0.0% | 0 | 0.0% |
| `future_close_price` | Future Close Price | Futures & Options | Official-direct | `fno` | 0 | 0.0% | 0 | 0.0% |
| `future_volume` | Future Volume | Futures & Options | Official-direct | `fno` | 0 | 0.0% | 0 | 0.0% |
| `future_open_interest` | Future Open Interest | Futures & Options | Official-direct | `fno` | 0 | 0.0% | 0 | 0.0% |
| `fair_value` | Fair Value | Futures & Options | Computed-from-official | `manual` | 0 | 0.0% | 0 | 0.0% |
| `fair_value_spread` | Fair Value Spread | Futures & Options | Computed-from-official | `manual` | 0 | 0.0% | 0 | 0.0% |
| `basis` | Basis | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `rollover_cost` | Rollover Cost | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `percentage_rollover` | Percentage Rollover | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `calendar_spread` | Calendar Spread | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `cash_carry_profit` | Cash & Carry Profit | Futures & Options | Computed-from-official | `manual` | 0 | 0.0% | 0 | 0.0% |
| `put_call_ratio` | Put Call Ratio | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `call_open_interest` | Call Open Interest | Futures & Options | Official-direct | `fno` | 0 | 0.0% | 0 | 0.0% |
| `put_open_interest` | Put Open Interest | Futures & Options | Official-direct | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1d_change_in_future_oi` | 1D Change in Future OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_future_oi` | 1W Change in Future OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1d_change_in_future_volume` | 1D Change in Future Volume | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_future_volume` | 1W Change in Future Volume | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1d_change_in_call_oi` | 1D Change in Call OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_call_oi` | 1W Change in Call OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1d_change_in_put_oi` | 1D Change in Put OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_put_oi` | 1W Change in Put OI | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_call_oi_strike` | Highest Call OI Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_put_oi_strike` | Highest Put OI Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_1d_oi_change_ce_strike` | Highest 1D OI Change CE Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_1d_oi_change_pe_strike` | Highest 1D OI Change PE Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_1w_oi_change_ce_strike` | Highest 1W OI Change CE Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `highest_1w_oi_change_pe_strike` | Highest 1W OI Change PE Strike | Futures & Options | Computed-from-official | `fno` | 0 | 0.0% | 0 | 0.0% |
| `market_cap` | Market Cap | Price and Volume | Computed-from-official | `shp` | 2385 | 90.2% | 100 | 100.0% |
| `close_price` | Close Price | Price and Volume | Official-direct | `daily` | 2385 | 90.2% | 100 | 100.0% |
| `1d_return` | 1D Return | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1w_return` | 1W Return | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1m_return` | 1M Return | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `6m_return` | 6M Return | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1y_return` | 1Y Return | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `5y_cagr` | 5Y CAGR | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1w_return_vs_nifty` | 1W Return vs Nifty | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1m_return_vs_nifty` | 1M Return vs Nifty | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `6m_return_vs_nifty` | 6M Return vs Nifty | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1y_return_vs_nifty` | 1Y Return vs Nifty | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `away_from_52w_high` | % Away From 52W High | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `away_from_52w_low` | % Away From 52W Low | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `daily_volume` | Daily Volume | Price and Volume | Official-direct | `daily` | 2385 | 90.2% | 100 | 100.0% |
| `1m_average_volume` | 1M Average Volume | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `3m_average_volume` | 3M Average Volume | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1d_change_in_volume` | 1D Change in Volume | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_volume` | 1W Change in Volume | Price and Volume | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `face_value` | Face value | Price and Volume | Official-direct | `weekly` | 2645 | 100.0% | 100 | 100.0% |
| `current_ratio` | Current Ratio | Financial Ratios | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `quick_ratio` | Quick Ratio | Financial Ratios | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `debt_to_equity` | Debt to Equity | Financial Ratios | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `long_term_debt_to_equity` | Long Term Debt to Equity | Financial Ratios | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `interest_coverage_ratio` | Interest Coverage Ratio | Financial Ratios | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `cash_conversion_cycle` | Cash Conversion Cycle | Financial Ratios | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `net_income_liabilities` | Net Income / Liabilities | Financial Ratios | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `working_capital_turnover_ratio` | Working Capital Turnover Ratio | Financial Ratios | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `inventory_turnover_ratio` | Inventory Turnover Ratio | Financial Ratios | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `asset_turnover_ratio` | Asset Turnover Ratio | Financial Ratios | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `days_of_inventory_outstanding` | Days of Inventory Outstanding | Financial Ratios | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `days_of_sales_outstanding` | Days of Sales Outstanding | Financial Ratios | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `days_payable_outstanding` | Days Payable Outstanding | Financial Ratios | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `earning_power` | Earning Power | Financial Ratios | Computed-from-official | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `price_momentum_rank` | Price Momentum Rank | Special | Approximate | `history` | 0 | 0.0% | 0 | 0.0% |
| `fundamental_score` | Fundamental Score | Special | Approximate | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `value_momentum_rank` | Value Momentum Rank | Special | Approximate | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `earnings_quality_rank` | Earnings Quality Rank | Special | Approximate | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `price_to_intrinsic_value_rank` | Price to Intrinsic Value Rank | Special | Approximate | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `percentage_upside` | Percentage Upside | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `percentage_buy_recos` | Percentage Buy Reco's | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `percentage_hold_recos` | Percentage Hold Reco's | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `percentage_sell_recos` | Percentage Sell Reco's | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `no_of_analysts_with_buy_reco` | No. of analysts with buy reco | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `total_no_of_analysts` | Total no. of analysts | Analyst Ratings | Unavailable | `unavailable` | 0 | 0.0% | 0 | 0.0% |
| `1y_max_loss` | 1Y Max Loss | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `sma_10d` | SMA 10D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `sma_50d` | SMA 50D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `sma_100d` | SMA 100D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `sma_200d` | SMA 200D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `ema_10d` | EMA 10D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `ema_50d` | EMA 50D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `ema_100d` | EMA 100D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `ema_200d` | EMA 200D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `alpha` | Alpha | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `beta` | Beta | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `sharpe_ratio` | Sharpe Ratio | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `relative_volume` | Relative Volume | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `volatility` | Volatility | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `volatility_vs_nifty` | Volatility vs Nifty | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `vwap` | Volume Weighted Average Price | Technical Indicators | Official-direct | `daily` | 2385 | 90.2% | 100 | 100.0% |
| `price_above_1m_sma` | % Price above 1M SMA | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `price_above_12m_sma` | % Price above 12M SMA | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `price_above_1m_ema` | % Price above 1M EMA | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `rsi_14d` | RSI 14D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `rsi_exponential_14d` | RSI Exponential 14D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `adx_rating` | ADX Rating | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `macd_line_1` | MACD Line 1 | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `macd_line_2` | MACD Line 2 | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `from_upper_bollinger_band` | % From Upper Bollinger Band | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `from_lower_bollinger_band` | % From Lower Bollinger Band | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `from_parabolic_sar` | % From Parabolic SAR | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `williams_r` | Williams %R | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `stochastic_k` | Stochastic %K | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `stochastic_d` | Stochastic %D | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_obv` | 1W Change in On Balance Volume | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `1w_change_in_ad_line` | 1W Change in AD Line | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `super_trend` | Super Trend | Technical Indicators | Computed-from-official | `history` | 0 | 0.0% | 0 | 0.0% |
| `book_value` | Book Value | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `cash_short_term_investments` | Cash and Short-term Investments | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_receivables` | Total Receivables | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_inventory` | Total Inventory | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `other_current_assets` | Other Current Assets | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_current_assets` | Total Current Assets | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `net_loans` | Net Loans | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `net_ppe` | Net Property Plant Equipment | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `goodwill_intangibles` | Goodwill and Intangibles | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `long_term_investments` | Long Term Investments | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `other_assets` | Other Assets | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_assets` | Total Assets | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `accounts_payable` | Accounts Payable | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_deposits` | Total Deposits | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `other_current_liabilities` | Other Current Liabilities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_current_liabilities` | Total Current Liabilities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_long_term_debt` | Total Long Term Debt | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_debt` | Total Debt | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `deferred_income_tax` | Deferred Income Tax | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `minority_interest` | Minority Interest | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `other_liabilities` | Other Liabilities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_liabilities` | Total Liabilities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `common_stock` | Common Stock | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `additional_paid_in_capital` | Additional Paid-in Capital | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `retained_earnings` | Retained Earnings | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `other_equity` | Other Equity | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_equity` | Total Equity | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_liabilities_shareholders_equity` | Total Liabilities & Shareholders Equity | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_common_shares_outstanding` | Total Common Shares Outstanding | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `total_preferred_shares_outstanding` | Total Preferred Shares Outstanding | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `policy_liabilities` | Policy Liabilities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `changes_in_working_capital` | Changes in Working Capital | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `cash_flow_operating_activities` | Cash Flow from Operating Activities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `capital_expenditures` | Capital Expenditures | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `cash_investing_activities` | Cash from Investing Activities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `total_cash_dividends_paid` | Total Cash Dividends Paid | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `cash_financing_activities` | Cash from Financing Activities | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 1 | 0.0% | 1 | 1.0% |
| `foreign_exchange_effects` | Foreign Exchange Effects | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `net_change_in_cash` | Net Change in Cash | Balance Sheet & Cash Flow | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `expense_ratio` | Expense Ratio | ETFs | Official-direct | `amfi` | 0 | 0.0% | 0 | 0.0% |
| `tracking_error` | Tracking Error | ETFs | Computed-from-official | `amfi` | 0 | 0.0% | 0 | 0.0% |
| `total_revenue` | Total Revenue | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `cost_of_revenue` | Cost of Revenue | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `gross_profit` | Gross Profit | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ebitda` | EBITDA | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `depreciation_amortization` | Depreciation & Amortization | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pbit` | PBIT | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `interest_other_items` | Interest & Other Items | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pbt` | PBT | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `taxes_other_items` | Taxes & Other Items | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `net_income` | Net Income | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `earnings_per_share` | Earnings Per Share | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `dividend_per_share` | Dividend Per Share | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `payout_ratio` | Payout Ratio | Income Statement | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `power_fuel_cost` | Power & Fuel Cost | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `raw_materials` | Raw Materials | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `operating_other_expenses` | Operating & Other expenses | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `employee_cost` | Employee Cost | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `selling_administrative_expenses` | Selling & Administrative Expenses | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `research_development` | Research & Development | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `interest_income` | Interest Income | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_interest_expense` | Total Interest Expense | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `net_interest_income` | Net Interest Income | Income Statement | Computed-from-official | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `loan_loss_provision` | Loan Loss Provision | Income Statement | Official-direct | `xbrl` | 0 | 0.0% | 0 | 0.0% |
| `total_revenue_q` | Total revenue (Q) | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `net_income_q` | Net Income (Q) | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `eps_q` | EPS (Q) | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `ebitda_q` | EBITDA (Q) | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `operating_and_other_expenses_q` | Operating and Other Expenses (Q) | Income Statement | Official-direct | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pbit_q` | PBIT (Q) | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |
| `pbt_q` | PBT (Q) | Income Statement | Computed-from-official | `xbrl` | 2 | 0.1% | 2 | 2.0% |

## 4. Sector Distribution & Unmapped Industry Log

| UI Sector | All Rows | NIFTY100 Rows |
|---|---|---|
| Unclassified | 1896 | 0 |
| Industrials | 169 | 14 |
| Consumer Discretionary | 144 | 14 |
| Financials | 117 | 23 |
| Materials | 84 | 13 |
| Health Care | 68 | 8 |
| Consumer Staples | 44 | 7 |
| Information Technology | 40 | 6 |
| Utilities | 27 | 6 |
| Communication Services | 20 | 2 |
| Energy | 19 | 6 |
| Real Estate | 17 | 1 |

### Unmapped Official Exchange Industries

_All official exchange industry labels present in DB are mapped cleanly in `config/sector_map.yaml`._
