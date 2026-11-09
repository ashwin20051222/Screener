# METRICS.md — Metrics & Filter Registry Specification

> **Version:** 2.0 (Phase 2)
> **Source of Truth:** `registry/filters.yaml`
> **Total Filters:** 255 across 13 Categories

---

## 1. Mathematical Conventions (Spec Section 10.1)

- **Financial Periods:**
  - `FY0`: Latest reported full fiscal year
  - `FY-n`: Full fiscal year $ periods prior
  - `Q0`: Latest reported quarter
  - `TTM`: Trailing Twelve Months (sum of trailing 4 quarters)
  - `P`: Latest closing price from official exchange bhavcopy
  - `MC`: Market Capitalization in ₹ Crores ( 	imes 	ext{Shares Outstanding} / 10^7$)
- **Averages & Compound Growth:**
  - $	ext{avg2}(x) = rac{x[FY0] + x[FY-1]}{2}$
  - $	ext{avg5}(x) = rac{1}{5} \sum_{i=0}^{4} x[FY-i]$
  - $	ext{CAGR}_n(x) = \left(rac{x[FY0]}{x[FY-n]}ight)^{1/n} - 1$ (Evaluates to `null` if start or end $\le 0$)
- **Trading Windows:**
  - `1W`: 5 trading days
  - `1M`: 20 trading days (4 weeks for returns)
  - `6M`: 126 trading days (26 weeks)
  - `1Y`: 252 trading days (52 weeks)
  - `12M SMA`: 250 trading days
- **Benchmark Scope:**
  - Sector/Sub-sector benchmarks are computed over the **full listed market** (`benchmark_scope = market`) by default, while filtering, sorting, and user tertiles run against the **active universe** (`universe`).
- **Null Rules:**
  - Division by zero, non-positive denominators where undefined (e.g. negative PE/PB/PS), or sector-inapplicable metrics (e.g. COGS/Inventory for banks, Net Loans for non-financials) evaluate strictly to `null`.
  - In sorting, `NULLS LAST` is strictly enforced in both ascending and descending order.

---

## 2. Metrics Catalog by Category

### 2.1 Analyst Ratings (6 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `percentage_upside` | Percentage Upside | % | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Mean analyst target price / Close - 1 (proprietary consensus) | `Unavailable` |
| `percentage_buy_recos` | Percentage Buy Reco's | % | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Buy recommendations / total analyst recommendations * 100 | `Unavailable` |
| `percentage_hold_recos` | Percentage Hold Reco's | % | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Hold recommendations / total analyst recommendations * 100 | `Unavailable` |
| `percentage_sell_recos` | Percentage Sell Reco's | % | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Sell recommendations / total analyst recommendations * 100 | `Unavailable` |
| `no_of_analysts_with_buy_reco` | No. of analysts with buy reco | - | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Count of analysts with Buy/Strong Buy rating | `Unavailable` |
| `total_no_of_analysts` | Total no. of analysts | - | higher_is_better | Null - sell-side research coverage unavailable from official exchange sources | Total number of analysts covering the stock | `Unavailable` |

### 2.2 Balance Sheet & Cash Flow (39 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `book_value` | Book Value | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Total Equity reported in annual balance sheet | `Official-direct` |
| `cash_short_term_investments` | Cash and Short-term Investments | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Cash + cash equivalents + marketable securities | `Official-direct` |
| `total_receivables` | Total Receivables | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Trade and other receivables | `Official-direct` |
| `total_inventory` | Total Inventory | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Raw materials + WIP + finished goods | `Official-direct` |
| `other_current_assets` | Other Current Assets | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Prepaid expenses, advances, other short-term assets | `Official-direct` |
| `total_current_assets` | Total Current Assets | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Sum of all current assets | `Official-direct` |
| `net_loans` | Net Loans | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Gross loans - provisions (banks and NBFCs) | `Official-direct` |
| `net_ppe` | Net Property Plant Equipment | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Gross PPE - accumulated depreciation | `Official-direct` |
| `goodwill_intangibles` | Goodwill and Intangibles | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Goodwill + other intangible assets | `Official-direct` |
| `long_term_investments` | Long Term Investments | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Non-current financial investments | `Official-direct` |
| `other_assets` | Other Assets | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Deferred tax assets, long-term advances, other non-current assets | `Official-direct` |
| `total_assets` | Total Assets | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Total Assets reported | `Official-direct` |
| `accounts_payable` | Accounts Payable | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Trade payables | `Official-direct` |
| `total_deposits` | Total Deposits | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Demand + term deposits (banks) | `Official-direct` |
| `other_current_liabilities` | Other Current Liabilities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Short-term provisions, accrued expenses, other current liabilities | `Official-direct` |
| `total_current_liabilities` | Total Current Liabilities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Sum of all current liabilities | `Official-direct` |
| `total_long_term_debt` | Total Long Term Debt | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Non-current borrowings | `Official-direct` |
| `total_debt` | Total Debt | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Short-term debt + long-term debt | `Official-direct` |
| `deferred_income_tax` | Deferred Income Tax | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Deferred tax liabilities (net) | `Official-direct` |
| `minority_interest` | Minority Interest | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Non-controlling interest in equity | `Official-direct` |
| `other_liabilities` | Other Liabilities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Other non-current liabilities | `Official-direct` |
| `total_liabilities` | Total Liabilities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Total Liabilities reported | `Official-direct` |
| `common_stock` | Common Stock | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Equity share capital | `Official-direct` |
| `additional_paid_in_capital` | Additional Paid-in Capital | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Securities premium reserve | `Official-direct` |
| `retained_earnings` | Retained Earnings | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Accumulated surplus in P&L | `Official-direct` |
| `other_equity` | Other Equity | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Other reserves, foreign currency translation reserve, etc. | `Official-direct` |
| `total_equity` | Total Equity | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Total shareholders' funds | `Official-direct` |
| `total_liabilities_shareholders_equity` | Total Liabilities & Shareholders Equity | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Total Liabilities + Total Equity (must equal Total Assets) | `Official-direct` |
| `total_common_shares_outstanding` | Total Common Shares Outstanding | - | neutral | Null if balance sheet filing missing or inapplicable to sector | Number of equity shares outstanding | `Official-direct` |
| `total_preferred_shares_outstanding` | Total Preferred Shares Outstanding | - | neutral | Null if balance sheet filing missing or inapplicable to sector | Number of preference shares outstanding | `Official-direct` |
| `policy_liabilities` | Policy Liabilities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Mathematical reserves and policyholder liabilities (insurers) | `Official-direct` |
| `changes_in_working_capital` | Changes in Working Capital | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Working capital adjustments in operating cash flow | `Official-direct` |
| `cash_flow_operating_activities` | Cash Flow from Operating Activities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Net cash generated from operations (CFO) | `Official-direct` |
| `capital_expenditures` | Capital Expenditures | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Purchase of fixed assets / capex from investing cash flow | `Official-direct` |
| `cash_investing_activities` | Cash from Investing Activities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Net cash flow from investing activities (CFI) | `Official-direct` |
| `total_cash_dividends_paid` | Total Cash Dividends Paid | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Dividends paid from financing cash flow | `Official-direct` |
| `cash_financing_activities` | Cash from Financing Activities | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Net cash flow from financing activities (CFF) | `Official-direct` |
| `foreign_exchange_effects` | Foreign Exchange Effects | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | Effect of exchange rate changes on cash | `Official-direct` |
| `net_change_in_cash` | Net Change in Cash | Rs Cr | neutral | Null if balance sheet filing missing or inapplicable to sector | CFO + CFI + CFF + FX effects | `Official-direct` |

### 2.3 ETFs (2 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `expense_ratio` | Expense Ratio | % | lower_is_better | Null for corporate equities; applicable exclusively to Exchange Traded Funds (ETFs) | Total Expense Ratio (TER) published by AMFI / AMC | `Official-direct` |
| `tracking_error` | Tracking Error | % | lower_is_better | Null for corporate equities; applicable exclusively to Exchange Traded Funds (ETFs) | Annualized stdev of (daily ETF NAV return - index return) over 1Y | `Computed-from-official` |

### 2.4 Financial Ratios (14 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `current_ratio` | Current Ratio | - | higher_is_better | Null for financial institutions or if current liabilities <= 0 | Current Assets / Current Liabilities | `Computed-from-official` |
| `quick_ratio` | Quick Ratio | - | higher_is_better | Null for financial institutions or if current liabilities <= 0 | (Current Assets - Inventory) / Current Liabilities | `Computed-from-official` |
| `debt_to_equity` | Debt to Equity | - | lower_is_better | Null for financial institutions or if equity <= 0 | Total Debt / Equity | `Computed-from-official` |
| `long_term_debt_to_equity` | Long Term Debt to Equity | - | lower_is_better | Null for financial institutions or if equity <= 0 | Long Term Debt / Equity | `Computed-from-official` |
| `interest_coverage_ratio` | Interest Coverage Ratio | - | higher_is_better | Null if interest expense <= 0 or missing | EBIT / Interest Expense | `Computed-from-official` |
| `cash_conversion_cycle` | Cash Conversion Cycle | days | lower_is_better | Null for financial institutions or missing working capital ratios | DIO + DSO - DPO | `Computed-from-official` |
| `net_income_liabilities` | Net Income / Liabilities | - | higher_is_better | Null if total liabilities <= 0 or missing | Net Income / Total Liabilities | `Computed-from-official` |
| `working_capital_turnover_ratio` | Working Capital Turnover Ratio | - | higher_is_better | Null if denominator asset <= 0 or missing | Revenue / avg2(Current Assets - Current Liabilities) | `Computed-from-official` |
| `inventory_turnover_ratio` | Inventory Turnover Ratio | - | higher_is_better | Null if denominator asset <= 0 or missing | COGS / avg2(Inventory) | `Computed-from-official` |
| `asset_turnover_ratio` | Asset Turnover Ratio | - | higher_is_better | Null if denominator asset <= 0 or missing | Revenue / avg2(Total Assets) | `Computed-from-official` |
| `days_of_inventory_outstanding` | Days of Inventory Outstanding | days | lower_is_better | Null for financial institutions or zero denominator | avg2(Inventory) / COGS * 365 | `Computed-from-official` |
| `days_of_sales_outstanding` | Days of Sales Outstanding | days | lower_is_better | Null for financial institutions or zero denominator | avg2(Receivables) / Revenue * 365 | `Computed-from-official` |
| `days_payable_outstanding` | Days Payable Outstanding | days | higher_is_better | Null for financial institutions or zero denominator | avg2(Payables) / COGS * 365 | `Computed-from-official` |
| `earning_power` | Earning Power | - | higher_is_better | Null if total assets <= 0 or missing | EBIT / Total Assets | `Computed-from-official` |

### 2.5 Futures & Options (28 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `lot_size` | Lot Size | - | neutral | Null for cash-only securities; valid for F&O-eligible securities only | NSE official contract lot size | `Official-direct` |
| `future_close_price` | Future Close Price | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Near-month futures settlement price | `Official-direct` |
| `future_volume` | Future Volume | - | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Traded contracts in near-month future | `Official-direct` |
| `future_open_interest` | Future Open Interest | - | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Near-month futures open interest | `Official-direct` |
| `fair_value` | Fair Value | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Spot * (1 + r * days_to_expiry / 365), r = 3M MIBOR | `Computed-from-official` |
| `fair_value_spread` | Fair Value Spread | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Fair value - futures price | `Computed-from-official` |
| `basis` | Basis | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Futures price - spot price | `Computed-from-official` |
| `rollover_cost` | Rollover Cost | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Next-month futures / near-month futures - 1 | `Computed-from-official` |
| `percentage_rollover` | Percentage Rollover | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | OI(next) / OI(near + next + far) * 100 | `Computed-from-official` |
| `calendar_spread` | Calendar Spread | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Mid-month futures - near-month futures | `Computed-from-official` |
| `cash_carry_profit` | Cash & Carry Profit | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Futures price - fair value | `Computed-from-official` |
| `put_call_ratio` | Put Call Ratio | - | neutral | Null if total call open interest <= 0 or not F&O eligible | Total Put OI / Total Call OI | `Computed-from-official` |
| `call_open_interest` | Call Open Interest | - | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Sum of OI across all CE strikes and expiries | `Official-direct` |
| `put_open_interest` | Put Open Interest | - | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Sum of OI across all PE strikes and expiries | `Official-direct` |
| `1d_change_in_future_oi` | 1D Change in Future OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Future OI / Future OI[-1] - 1 | `Computed-from-official` |
| `1w_change_in_future_oi` | 1W Change in Future OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Future OI / Future OI[-5] - 1 | `Computed-from-official` |
| `1d_change_in_future_volume` | 1D Change in Future Volume | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Future Vol / Future Vol[-1] - 1 | `Computed-from-official` |
| `1w_change_in_future_volume` | 1W Change in Future Volume | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Future Vol / Future Vol[-5] - 1 | `Computed-from-official` |
| `1d_change_in_call_oi` | 1D Change in Call OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Call OI / Call OI[-1] - 1 | `Computed-from-official` |
| `1w_change_in_call_oi` | 1W Change in Call OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Call OI / Call OI[-5] - 1 | `Computed-from-official` |
| `1d_change_in_put_oi` | 1D Change in Put OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Put OI / Put OI[-1] - 1 | `Computed-from-official` |
| `1w_change_in_put_oi` | 1W Change in Put OI | % | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Put OI / Put OI[-5] - 1 | `Computed-from-official` |
| `highest_call_oi_strike` | Highest Call OI Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike price with the maximum CE open interest | `Computed-from-official` |
| `highest_put_oi_strike` | Highest Put OI Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike price with the maximum PE open interest | `Computed-from-official` |
| `highest_1d_oi_change_ce_strike` | Highest 1D OI Change CE Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike with highest % OI increase over 1D among CE contracts | `Computed-from-official` |
| `highest_1d_oi_change_pe_strike` | Highest 1D OI Change PE Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike with highest % OI increase over 1D among PE contracts | `Computed-from-official` |
| `highest_1w_oi_change_ce_strike` | Highest 1W OI Change CE Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike with highest % OI increase over 1W among CE contracts | `Computed-from-official` |
| `highest_1w_oi_change_pe_strike` | Highest 1W OI Change PE Strike | Rs | neutral | Null for cash-only securities; valid for F&O-eligible securities only | Strike with highest % OI increase over 1W among PE contracts | `Computed-from-official` |

### 2.6 Growth (13 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `1y_forward_revenue_growth` | 1Y Forward Revenue Growth | % | higher_is_better | Null - unavailable from official sources without consensus analyst coverage | (consensus estimate current FY / actual FY0) - 1 | `Unavailable` |
| `1y_hist_op_cash_flow_growth` | 1Y Hist Op. Cash Flow Growth | % | higher_is_better | Null if op_cash_flow_growth[FY-1] <= 0 or missing | CFO[FY0] / CFO[FY-1] - 1 | `Computed-from-official` |
| `1y_forward_ebitda_growth` | 1Y Forward EBITDA Growth | % | higher_is_better | Null - unavailable from official sources without consensus analyst coverage | (consensus EBITDA / actual EBITDA) - 1 | `Unavailable` |
| `1y_historical_eps_growth` | 1Y Historical EPS Growth | % | higher_is_better | Null if eps_growth[FY-1] <= 0 or missing | EPS[FY0] / EPS[FY-1] - 1 | `Computed-from-official` |
| `1y_historical_revenue_growth` | 1Y Historical Revenue Growth | % | higher_is_better | Null if revenue_growth[FY-1] <= 0 or missing | Revenue[FY0] / Revenue[FY-1] - 1 | `Computed-from-official` |
| `1y_fwd_op_cash_flow_growth` | 1Y Fwd Op. Cash Flow Growth | % | higher_is_better | Null - unavailable from official sources without consensus analyst coverage | (consensus CFO / actual CFO) - 1 | `Unavailable` |
| `5y_historical_ebitda_growth` | 5Y Historical EBITDA Growth | % | higher_is_better | Null if ebitda_growth[FY-5] <= 0 or ebitda_growth[FY0] <= 0 or missing | CAGR_5(EBITDA) | `Computed-from-official` |
| `5y_hist_op_cash_flow_growth` | 5Y Hist Op. Cash Flow Growth | % | higher_is_better | Null if op_cash_flow_growth[FY-5] <= 0 or op_cash_flow_growth[FY0] <= 0 or missing | CAGR_5(CFO) | `Computed-from-official` |
| `3y_historical_dividend_growth` | 3Y Historical Dividend Growth | % | higher_is_better | Null if DPS[FY-3] <= 0 or DPS[FY0] <= 0 or missing | CAGR_3(DPS) | `Computed-from-official` |
| `5y_historical_eps_growth` | 5Y Historical EPS Growth | % | higher_is_better | Null if eps_growth[FY-5] <= 0 or eps_growth[FY0] <= 0 or missing | CAGR_5(EPS) | `Computed-from-official` |
| `5y_historical_revenue_growth` | 5Y Historical Revenue Growth | % | higher_is_better | Null if revenue_growth[FY-5] <= 0 or revenue_growth[FY0] <= 0 or missing | CAGR_5(Revenue) | `Computed-from-official` |
| `1y_historical_ebitda_growth` | 1Y Historical EBITDA Growth | % | higher_is_better | Null if ebitda_growth[FY-1] <= 0 or missing | EBITDA[FY0] / EBITDA[FY-1] - 1 | `Computed-from-official` |
| `1y_forward_eps_growth` | 1Y Forward EPS Growth | % | higher_is_better | Null - unavailable from official sources without consensus analyst coverage | (consensus EPS / actual EPS) - 1 | `Unavailable` |

### 2.7 Income Statement (30 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `total_revenue` | Total Revenue | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Revenue from operations + other income | `Official-direct` |
| `cost_of_revenue` | Cost of Revenue | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Direct cost of sales/production | `Official-direct` |
| `gross_profit` | Gross Profit | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Total Revenue - Cost of Revenue | `Computed-from-official` |
| `ebitda` | EBITDA | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Operating profit before D&A | `Computed-from-official` |
| `depreciation_amortization` | Depreciation & Amortization | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Depreciation and amortisation expenses | `Official-direct` |
| `pbit` | PBIT | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | EBITDA - D&A (EBIT) | `Computed-from-official` |
| `interest_other_items` | Interest & Other Items | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Finance costs / interest expense | `Official-direct` |
| `pbt` | PBT | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | PBIT - Interest & Other Items | `Computed-from-official` |
| `taxes_other_items` | Taxes & Other Items | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Current and deferred tax expenses | `Official-direct` |
| `net_income` | Net Income | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | PBT - Taxes (Profit After Tax) | `Official-direct` |
| `earnings_per_share` | Earnings Per Share | Rs | higher_is_better | Null if financial report missing or not disclosed | Net Income / shares outstanding (Diluted) | `Official-direct` |
| `dividend_per_share` | Dividend Per Share | Rs | higher_is_better | Null if financial report missing or not disclosed | Total dividends declared / shares outstanding | `Official-direct` |
| `payout_ratio` | Payout Ratio | % | higher_is_better | Null if financial report missing or not disclosed | DPS / EPS * 100 | `Computed-from-official` |
| `power_fuel_cost` | Power & Fuel Cost | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Power and fuel expenses | `Official-direct` |
| `raw_materials` | Raw Materials | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Cost of materials consumed | `Official-direct` |
| `operating_other_expenses` | Operating & Other expenses | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Other operating expenses | `Official-direct` |
| `employee_cost` | Employee Cost | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Employee benefit expenses | `Official-direct` |
| `selling_administrative_expenses` | Selling & Administrative Expenses | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Selling, general, and administrative expenses | `Official-direct` |
| `research_development` | Research & Development | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | R&D expenditures reported | `Official-direct` |
| `interest_income` | Interest Income | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Interest earned (banks and financial institutions) | `Official-direct` |
| `total_interest_expense` | Total Interest Expense | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Interest expended (banks) | `Official-direct` |
| `net_interest_income` | Net Interest Income | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Interest Income - Total Interest Expense | `Computed-from-official` |
| `loan_loss_provision` | Loan Loss Provision | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Provisions and contingencies for bad loans | `Official-direct` |
| `total_revenue_q` | Total revenue (Q) | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Quarterly total revenue | `Official-direct` |
| `net_income_q` | Net Income (Q) | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Quarterly Profit After Tax | `Official-direct` |
| `eps_q` | EPS (Q) | Rs | higher_is_better | Null if financial report missing or not disclosed | Quarterly Diluted EPS | `Official-direct` |
| `ebitda_q` | EBITDA (Q) | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Quarterly operating profit before D&A | `Computed-from-official` |
| `operating_and_other_expenses_q` | Operating and Other Expenses (Q) | Rs Cr | lower_is_better | Null if financial report missing or not disclosed | Quarterly other operating expenses | `Official-direct` |
| `pbit_q` | PBIT (Q) | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Quarterly EBIT | `Computed-from-official` |
| `pbt_q` | PBT (Q) | Rs Cr | higher_is_better | Null if financial report missing or not disclosed | Quarterly Profit Before Tax | `Computed-from-official` |

### 2.8 Ownership (22 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `mutual_fund_holding` | Mutual Fund Holding | % | higher_is_better | Null if quarterly shareholding filing is unavailable | Official quarterly shareholding pattern | `Official-direct` |
| `domestic_institutional_holding` | Domestic Institutional Holding | % | higher_is_better | Null if quarterly shareholding filing is unavailable | Official quarterly shareholding pattern (DII) | `Official-direct` |
| `foreign_institutional_holding` | Foreign Institutional Holding | % | higher_is_better | Null if quarterly shareholding filing is unavailable | Official quarterly shareholding pattern (FII) | `Official-direct` |
| `promoter_holding` | Promoter Holding | % | higher_is_better | Null if quarterly shareholding filing is unavailable | Official quarterly shareholding pattern | `Official-direct` |
| `pledged_promoter_holdings` | Pledged Promoter Holdings | % | lower_is_better | Null if promoter shares <= 0 or missing | Promoter pledged shares / total promoter shares * 100 | `Official-direct` |
| `retail_investor_holding` | Retail Investor Holding | % | neutral | Null if quarterly shareholding filing is unavailable | Public individual shareholders holding nominal capital <= Rs 2 lakh | `Official-direct` |
| `insurance_firms_holding` | Insurance Firms Holding | % | neutral | Null if quarterly shareholding filing is unavailable | Official quarterly shareholding pattern | `Official-direct` |
| `no_of_shareholders` | No. of Shareholders | - | neutral | Null if shareholding filing missing | Total count from quarterly shareholding pattern | `Official-direct` |
| `mf_holding_change_3m` | MF Holding Change – 3M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | MF%[Q0] - MF%[Q-1] (pp difference) | `Computed-from-official` |
| `mf_holding_change_6m` | MF Holding Change – 6M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | MF%[Q0] - MF%[Q-2] (pp difference) | `Computed-from-official` |
| `dii_holding_change_3m` | DII Holding Change – 3M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | DII%[Q0] - DII%[Q-1] (pp difference) | `Computed-from-official` |
| `dii_holding_change_6m` | DII Holding Change – 6M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | DII%[Q0] - DII%[Q-2] (pp difference) | `Computed-from-official` |
| `fii_holding_change_3m` | FII Holding Change – 3M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | FII%[Q0] - FII%[Q-1] (pp difference) | `Computed-from-official` |
| `fii_holding_change_6m` | FII Holding Change – 6M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | FII%[Q0] - FII%[Q-2] (pp difference) | `Computed-from-official` |
| `promoter_holding_change_3m` | Promoter Holding Change – 3M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | Promoter%[Q0] - Promoter%[Q-1] (pp difference) | `Computed-from-official` |
| `promoter_holding_change_6m` | Promoter Holding Change – 6M | % | higher_is_better | Null if comparative quarterly shareholding filings are unavailable | Promoter%[Q0] - Promoter%[Q-2] (pp difference) | `Computed-from-official` |
| `insider_trades_1m_cumulative` | Insider Trades - 1M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Net buy-sell shares in 1M / shares outstanding * 100 (SEBI PIT) | `Computed-from-official` |
| `insider_trades_3m_cumulative` | Insider Trades - 3M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Net buy-sell shares in 3M / shares outstanding * 100 (SEBI PIT) | `Computed-from-official` |
| `insider_trades_6m_cumulative` | Insider Trades - 6M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Net buy-sell shares in 6M / shares outstanding * 100 (SEBI PIT) | `Computed-from-official` |
| `bulk_deals_1m_cumulative` | Bulk Deals - 1M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Signed shares in bulk deals / shares outstanding * 100 | `Computed-from-official` |
| `bulk_deals_3m_cumulative` | Bulk Deals - 3M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Signed shares in bulk deals / shares outstanding * 100 | `Computed-from-official` |
| `bulk_deals_6m_cumulative` | Bulk Deals - 6M Cumulative | % | higher_is_better | Null if no disclosure data or shares outstanding missing | Signed shares in bulk deals / shares outstanding * 100 | `Computed-from-official` |

### 2.9 Price and Volume (20 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `market_cap` | Market Cap | Rs Cr | neutral | Null if close price or shares outstanding missing | Close * shares outstanding / 1e7 | `Computed-from-official` |
| `close_price` | Close Price | Rs | neutral | Null if stock unquoted or missing bhavcopy | Official bhavcopy closing price | `Official-direct` |
| `1d_return` | 1D Return | % | higher_is_better | Null if underlying data point is missing | P / P[-1] - 1 | `Computed-from-official` |
| `1w_return` | 1W Return | % | higher_is_better | Null if underlying data point is missing | P / P[-5] - 1 | `Computed-from-official` |
| `1m_return` | 1M Return | % | higher_is_better | Null if underlying data point is missing | P / P[20 days ago] - 1 | `Computed-from-official` |
| `6m_return` | 6M Return | % | higher_is_better | Null if underlying data point is missing | P / P[126 days ago] - 1 | `Computed-from-official` |
| `1y_return` | 1Y Return | % | higher_is_better | Null if underlying data point is missing | P / P[250 days ago] - 1 | `Computed-from-official` |
| `5y_cagr` | 5Y CAGR | % | higher_is_better | Null if underlying data point is missing | (P / P[5y ago])^(1/5) - 1 (adjusted for corporate actions) | `Computed-from-official` |
| `1w_return_vs_nifty` | 1W Return vs Nifty | % | higher_is_better | Null if underlying data point is missing | Stock 1W Return - Nifty 50 1W Return (pp difference) | `Computed-from-official` |
| `1m_return_vs_nifty` | 1M Return vs Nifty | % | higher_is_better | Null if underlying data point is missing | Stock 1M Return - Nifty 50 1M Return (pp difference) | `Computed-from-official` |
| `6m_return_vs_nifty` | 6M Return vs Nifty | % | higher_is_better | Null if underlying data point is missing | Stock 6M Return - Nifty 50 6M Return (pp difference) | `Computed-from-official` |
| `1y_return_vs_nifty` | 1Y Return vs Nifty | % | higher_is_better | Null if underlying data point is missing | Stock 1Y Return - Nifty 50 1Y Return (pp difference) | `Computed-from-official` |
| `away_from_52w_high` | % Away From 52W High | % | lower_is_better | Null if 52-week high is missing or zero | (High52 / Close) - 1 (as documented in reference) | `Computed-from-official` |
| `away_from_52w_low` | % Away From 52W Low | % | higher_is_better | Null if 52-week low is missing or zero | (Close / Low52) - 1 | `Computed-from-official` |
| `daily_volume` | Daily Volume | - | neutral | Null if underlying data point is missing | Total traded quantity from bhavcopy | `Official-direct` |
| `1m_average_volume` | 1M Average Volume | - | neutral | Null if underlying data point is missing | Mean daily volume over 21 trading days | `Computed-from-official` |
| `3m_average_volume` | 3M Average Volume | - | neutral | Null if underlying data point is missing | Mean daily volume over 63 trading days | `Computed-from-official` |
| `1d_change_in_volume` | 1D Change in Volume | % | neutral | Null if underlying data point is missing | Volume / Volume[-1] - 1 | `Computed-from-official` |
| `1w_change_in_volume` | 1W Change in Volume | % | neutral | Null if underlying data point is missing | Volume / Volume[-5] - 1 | `Computed-from-official` |
| `face_value` | Face value | Rs | neutral | Null if underlying data point is missing | Official face value per share from security master | `Official-direct` |

### 2.10 Profitability (16 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `return_on_equity` | Return on Equity | % | higher_is_better | Null if avg2(common_equity) <= 0 or missing | Net profit / avg2(common equity) | `Computed-from-official` |
| `return_on_assets` | Return on Assets | % | higher_is_better | Null if avg2(total_assets) <= 0 or missing | Net profit / avg2(total assets) | `Computed-from-official` |
| `return_on_investment` | Return on Investment | % | higher_is_better | Null if average invested capital <= 0 or missing | Net income / avg2(equity + long-term debt + other long-term liabilities) | `Computed-from-official` |
| `roce` | ROCE | % | higher_is_better | Null if capital employed (total assets - current liabilities) <= 0 or missing | EBIT / (total assets - current liabilities) | `Computed-from-official` |
| `net_profit_margin` | Net Profit Margin | % | higher_is_better | Null if revenue <= 0 or missing | Net profit / revenue | `Computed-from-official` |
| `ebitda_margin` | EBITDA Margin | % | higher_is_better | Null if revenue <= 0 or missing | EBITDA / revenue | `Computed-from-official` |
| `operating_profit_margin` | Operating Profit Margin | % | higher_is_better | Null if revenue <= 0 or missing | Operating profit / revenue | `Computed-from-official` |
| `cash_flow_margin` | Cash Flow Margin | % | higher_is_better | Null if revenue <= 0 or missing | Operating cash flow / revenue | `Computed-from-official` |
| `cost_of_goods_sold` | Cost of Goods Sold | Rs Cr | lower_is_better | Null for financial institutions and lenders, or if missing | COGS reported in financial statements | `Official-direct` |
| `5y_avg_ebitda_margin` | 5Y Avg EBITDA Margin | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(EBITDA margin) | `Computed-from-official` |
| `5y_avg_net_profit_margin` | 5Y Avg Net Profit Margin | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(Net profit margin) | `Computed-from-official` |
| `5y_avg_return_on_equity` | 5Y Avg Return on Equity | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(ROE) | `Computed-from-official` |
| `5y_avg_return_on_assets` | 5Y Avg Return on Assets | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(ROA) | `Computed-from-official` |
| `5y_avg_return_on_investment` | 5Y Avg Return on Investment | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(ROI) | `Computed-from-official` |
| `5y_avg_cash_flow_margin` | 5Y Avg Cash Flow Margin | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(Cash flow margin) | `Computed-from-official` |
| `5y_avg_operating_profit_margin` | 5Y Avg Operating Profit Margin | % | higher_is_better | Null if fewer than 5 consecutive fiscal years of data are available | avg5(Operating margin) | `Computed-from-official` |

### 2.11 Special (5 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `price_momentum_rank` | Price Momentum Rank | rank | higher_is_better | Null if required historical data or fundamental ratios missing | 0.6 * pct(12M return) + 0.4 * pct(12M return - sub-sector median 12M return) | `Approximate` |
| `fundamental_score` | Fundamental Score | score | higher_is_better | Null if required historical data or fundamental ratios missing | 1 + 9 * sector percentile of composite (valuation, profitability, growth, financial health) | `Approximate` |
| `value_momentum_rank` | Value Momentum Rank | rank | higher_is_better | Null if required historical data or fundamental ratios missing | 0.5 * valuation percentile + 0.5 * Price Momentum Rank | `Approximate` |
| `earnings_quality_rank` | Earnings Quality Rank | rank | higher_is_better | Null if required historical data or fundamental ratios missing | Equal mix of pct(net margin), pct(asset turnover), pct(CFO / net income) | `Approximate` |
| `price_to_intrinsic_value_rank` | Price to Intrinsic Value Rank | rank | higher_is_better | Null if required historical data or fundamental ratios missing | Percentile rank of P / Intrinsic Value (IV = median of Graham, FCF perpetuity, dividend models) | `Approximate` |

### 2.12 Technical Indicators (33 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `1y_max_loss` | 1Y Max Loss | % | lower_is_better | Null if underlying data point is missing | Worst peak-to-trough drawdown over trailing 250 trading days | `Computed-from-official` |
| `sma_10d` | SMA 10D | Rs | neutral | Null if trading history is shorter than required lookback period | Simple Moving Average of 10 daily closes | `Computed-from-official` |
| `sma_50d` | SMA 50D | Rs | neutral | Null if trading history is shorter than required lookback period | Simple Moving Average of 50 daily closes | `Computed-from-official` |
| `sma_100d` | SMA 100D | Rs | neutral | Null if trading history is shorter than required lookback period | Simple Moving Average of 100 daily closes | `Computed-from-official` |
| `sma_200d` | SMA 200D | Rs | neutral | Null if trading history is shorter than required lookback period | Simple Moving Average of 200 daily closes | `Computed-from-official` |
| `ema_10d` | EMA 10D | Rs | neutral | Null if trading history is shorter than required lookback period | Exponential Moving Average, multiplier 2/(10+1) | `Computed-from-official` |
| `ema_50d` | EMA 50D | Rs | neutral | Null if trading history is shorter than required lookback period | Exponential Moving Average, multiplier 2/(50+1) | `Computed-from-official` |
| `ema_100d` | EMA 100D | Rs | neutral | Null if trading history is shorter than required lookback period | Exponential Moving Average, multiplier 2/(100+1) | `Computed-from-official` |
| `ema_200d` | EMA 200D | Rs | neutral | Null if trading history is shorter than required lookback period | Exponential Moving Average, multiplier 2/(200+1) | `Computed-from-official` |
| `alpha` | Alpha | % | higher_is_better | Null if underlying data point is missing | Stock return - benchmark return over 104 weekly closes | `Computed-from-official` |
| `beta` | Beta | - | neutral | Null if underlying data point is missing | cov(r_stock, r_bench) / var(r_bench) over 104 weekly closes | `Computed-from-official` |
| `sharpe_ratio` | Sharpe Ratio | - | higher_is_better | Null if underlying data point is missing | (Stock return - benchmark return) / stdev(weekly excess returns) | `Computed-from-official` |
| `relative_volume` | Relative Volume | - | neutral | Null if underlying data point is missing | Avg volume (10 days) / Avg volume (~91 days) | `Computed-from-official` |
| `volatility` | Volatility | % | lower_is_better | Null if underlying data point is missing | Annualized stdev of daily returns over 200 days * sqrt(252) | `Computed-from-official` |
| `volatility_vs_nifty` | Volatility vs Nifty | % | lower_is_better | Null if underlying data point is missing | Stock volatility - Nifty 50 volatility | `Computed-from-official` |
| `vwap` | Volume Weighted Average Price | Rs | neutral | Null if underlying data point is missing | Total traded value / total traded quantity from bhavcopy | `Official-direct` |
| `price_above_1m_sma` | % Price above 1M SMA | % | neutral | Null if trading history is shorter than required lookback period | Close / SMA(20) - 1 | `Computed-from-official` |
| `price_above_12m_sma` | % Price above 12M SMA | % | neutral | Null if trading history is shorter than required lookback period | Close / SMA(250) - 1 | `Computed-from-official` |
| `price_above_1m_ema` | % Price above 1M EMA | % | neutral | Null if trading history is shorter than required lookback period | Close / EMA(20) - 1 | `Computed-from-official` |
| `rsi_14d` | RSI 14D | - | neutral | Null if fewer than 15 trading days available | 100 - (100 / (1 + avg_gain / avg_loss)) over 14 days | `Computed-from-official` |
| `rsi_exponential_14d` | RSI Exponential 14D | - | neutral | Null if fewer than 15 trading days available | RSI with Wilder smoothing | `Computed-from-official` |
| `adx_rating` | ADX Rating | - | higher_is_better | Null if fewer than 28 trading days available | Average Directional Index (14) with +DI/-DI | `Computed-from-official` |
| `macd_line_1` | MACD Line 1 | - | neutral | Null if underlying data point is missing | EMA(12) - EMA(26) | `Computed-from-official` |
| `macd_line_2` | MACD Line 2 | - | neutral | Null if underlying data point is missing | MACD - EMA(9, MACD) [signal line] | `Computed-from-official` |
| `from_upper_bollinger_band` | % From Upper Bollinger Band | % | neutral | Null if underlying data point is missing | Close / (SMA(20) + 2 * sd(20)) - 1 | `Computed-from-official` |
| `from_lower_bollinger_band` | % From Lower Bollinger Band | % | neutral | Null if underlying data point is missing | Close / (SMA(20) - 2 * sd(20)) - 1 | `Computed-from-official` |
| `from_parabolic_sar` | % From Parabolic SAR | % | higher_is_better | Null if underlying data point is missing | Close / SAR - 1 (AF 0.02, step 0.02, max 0.2) | `Computed-from-official` |
| `williams_r` | Williams %R | % | neutral | Null if underlying data point is missing | (HH(14) - Close) / (HH(14) - LL(14)) * (-100) | `Computed-from-official` |
| `stochastic_k` | Stochastic %K | % | neutral | Null if underlying data point is missing | (Close - LL(14)) / (HH(14) - LL(14)) * 100 | `Computed-from-official` |
| `stochastic_d` | Stochastic %D | % | neutral | Null if underlying data point is missing | SMA(3, Stochastic %K) | `Computed-from-official` |
| `1w_change_in_obv` | 1W Change in On Balance Volume | % | higher_is_better | Null if underlying data point is missing | OBV / OBV[-5] - 1 | `Computed-from-official` |
| `1w_change_in_ad_line` | 1W Change in AD Line | % | higher_is_better | Null if underlying data point is missing | AD / AD[-5] - 1 | `Computed-from-official` |
| `super_trend` | Super Trend | - | higher_is_better | Null if underlying data point is missing | SuperTrend(ATR 10, mult 3): signed distance + buy/sell flag | `Computed-from-official` |

### 2.13 Valuation (27 filters)

| ID | Name | Unit | Direction | Null Rule | Formula | Availability |
|---|---|---|---|---|---|---|
| `pe_ratio` | PE Ratio | - | lower_is_better | Null if EPS <= 0 or missing | Close / EPS(FY0, before extraordinary items) | `Computed-from-official` |
| `ttm_pe_ratio` | TTM PE Ratio | - | lower_is_better | Null if EPS <= 0 or missing | Close / EPS(TTM) | `Computed-from-official` |
| `forward_pe_ratio` | Forward PE Ratio | - | lower_is_better | Null - forward earnings consensus unavailable from official exchange sources | Close / estimated EPS | `Unavailable` |
| `pb_ratio` | PB Ratio | - | lower_is_better | Null if book value per share <= 0 or missing | Close / book value per share | `Computed-from-official` |
| `ps_ratio` | PS Ratio | - | lower_is_better | Null if revenue per share <= 0 or missing | Close / (revenue(FY0) / shares) | `Computed-from-official` |
| `forward_ps_ratio` | Forward PS Ratio | - | lower_is_better | Null - forward sales consensus unavailable from official exchange sources | Close / estimated revenue per share | `Unavailable` |
| `dividend_yield` | Dividend Yield | % | higher_is_better | Null if close_price <= 0 or missing | DPS(FY0) / Close * 100 | `Computed-from-official` |
| `ev_ebitda_ratio` | EV/EBITDA Ratio | - | lower_is_better | Null if ebitda <= 0 or EV <= 0 or missing | EV / EBITDA(FY0) | `Computed-from-official` |
| `ev_ebit_ratio` | EV / EBIT Ratio | - | lower_is_better | Null if ebit <= 0 or EV <= 0 or missing | EV / EBIT(FY0) | `Computed-from-official` |
| `ev_revenue_ratio` | EV / Revenue Ratio | - | lower_is_better | Null if revenue <= 0 or EV <= 0 or missing | EV / Revenue(FY0) | `Computed-from-official` |
| `ev_free_cash_flow` | EV / Free Cash Flow | - | lower_is_better | Null if denominator cash flow <= 0 or missing | EV / FCF | `Computed-from-official` |
| `ev_invested_capital` | EV / Invested Capital | - | lower_is_better | Null if invested capital <= 0 or missing | EV / IC (total equity + total debt + minority interest) | `Computed-from-official` |
| `enterprise_value` | Enterprise Value | Rs Cr | neutral | Null if market cap or balance sheet components missing | MC + total debt + minority interest - cash & short-term investments | `Computed-from-official` |
| `price_free_cash_flow` | Price / Free Cash Flow | - | lower_is_better | Null if denominator cash flow <= 0 or missing | MC / FCF | `Computed-from-official` |
| `price_cfo` | Price / CFO | - | lower_is_better | Null if denominator cash flow <= 0 or missing | MC / Operating Cash Flow | `Computed-from-official` |
| `price_sales` | Price / Sales | - | lower_is_better | Null if revenue per share <= 0 or missing | Alias for PS Ratio | `Computed-from-official` |
| `pe_premium_vs_sector` | PE Premium vs Sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PE / Sector PE - 1) * 100 | `Computed-from-official` |
| `pb_premium_vs_sector` | PB Premium vs Sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PB / Sector PB - 1) * 100 | `Computed-from-official` |
| `ps_premium_vs_sector` | PS Premium vs Sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PS / Sector PS - 1) * 100 | `Computed-from-official` |
| `dividend_yield_vs_sector` | Dividend Yield vs Sector | % | higher_is_better | Null if stock yield or sector yield is missing | Stock Yield - Sector Yield (pp difference) | `Computed-from-official` |
| `pe_premium_vs_sub_sector` | PE Premium vs Sub-sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PE / Sub-sector PE - 1) * 100 | `Computed-from-official` |
| `pb_premium_vs_sub_sector` | PB Premium vs Sub-sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PB / Sub-sector PB - 1) * 100 | `Computed-from-official` |
| `ps_premium_vs_sub_sector` | PS Premium vs Sub-sector | % | lower_is_better | Null if stock multiple or sector benchmark is missing or non-positive | (PS / Sub-sector PS - 1) * 100 | `Computed-from-official` |
| `dividend_yield_vs_sub_sector` | Dividend Yield vs Sub-sector | % | higher_is_better | Null if stock yield or sector yield is missing | Stock Yield - Sub-sector Yield (pp difference) | `Computed-from-official` |
| `sector_dividend_yield` | Sector Dividend Yield | % | neutral | Null if fewer than 2 peers exist in the sector | Median of positive Dividend Yields across sector | `Computed-from-official` |
| `sector_pb` | Sector PB | - | neutral | Null if fewer than 2 peers exist in the sector | Median of positive PB ratios across sector | `Computed-from-official` |
| `sector_pe` | Sector PE | - | neutral | Null if fewer than 2 peers exist in the sector | Median of positive PE ratios across sector | `Computed-from-official` |

