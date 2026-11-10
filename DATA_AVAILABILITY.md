# DATA_AVAILABILITY.md — Official Data Posture & Filter Availability

> Single source of truth for the availability classification of all 255 filters in `registry/filters.yaml`.
> Governed by Operating Rules 4 ("No fabricated data") and 5 ("Honest labels").

---

## 1. Classification Categories

Every metric in the screener is classified into exactly one of four availability tiers:

| Status | Badge in UI | Description | Filter Count |
|--------|-------------|-------------|--------------|
| **`Official-direct`** | Green badge / standard | Raw values taken directly from exchange/regulatory publications without alteration | **65** |
| **`Computed-from-official`** | Blue badge / info tooltip | Deterministic formulas computed strictly from official direct inputs (e.g., ratios, returns, moving averages) | **172** |
| **`Approximate`** | Amber badge: "Approximate - computed locally" | Locally calculated quant ranks/scores where the proprietary formula is approximated transparently | **5** |
| **`Unavailable`** | Gray badge: "Not available from official sources" | Metrics requiring proprietary consensus or commercial data feeds not published by official bodies | **13** |

---

## 2. Category-by-Category Availability Breakdown

### 2.1 Profitability (16 filters)
- **Official-direct (1):** Cost of Goods Sold
- **Computed-from-official (15):** Return on Equity, Return on Assets, Return on Investment, ROCE, Net Profit Margin, EBITDA Margin, Operating Profit Margin, Cash Flow Margin, 5Y Avg EBITDA Margin, 5Y Avg Net Profit Margin, 5Y Avg Return on Equity, 5Y Avg Return on Assets, 5Y Avg Return on Investment, 5Y Avg Cash Flow Margin, 5Y Avg Operating Profit Margin

### 2.2 Growth (13 filters)
- **Computed-from-official (9):** 1Y Hist Op. Cash Flow Growth, 1Y Historical EPS Growth, 1Y Historical Revenue Growth, 5Y Historical EBITDA Growth, 5Y Hist Op. Cash Flow Growth, 3Y Historical Dividend Growth, 5Y Historical EPS Growth, 5Y Historical Revenue Growth, 1Y Historical EBITDA Growth
- **Unavailable (4):** 1Y Forward Revenue Growth, 1Y Forward EBITDA Growth, 1Y Fwd Op. Cash Flow Growth, 1Y Forward EPS Growth *(Reason: Requires analyst consensus forward estimates not published officially)*

### 2.3 Valuation (27 filters)
- **Computed-from-official (25):** PE Ratio, TTM PE Ratio, PB Ratio, PS Ratio, Dividend Yield, EV/EBITDA Ratio, EV / EBIT Ratio, EV / Revenue Ratio, EV / Free Cash Flow, EV / Invested Capital, Enterprise Value, Price / Free Cash Flow, Price / CFO, Price / Sales, PE Premium vs Sector, PB Premium vs Sector, PS Premium vs Sector, Dividend Yield vs Sector, PE Premium vs Sub-sector, PB Premium vs Sub-sector, PS Premium vs Sub-sector, Dividend Yield vs Sub-sector, Sector Dividend Yield, Sector PB, Sector PE
- **Unavailable (2):** Forward PE Ratio, Forward PS Ratio *(Reason: Requires forward analyst consensus estimates)*

### 2.4 Ownership (22 filters)
- **Official-direct (8):** Mutual Fund Holding, Domestic Institutional Holding, Foreign Institutional Holding, Promoter Holding, Pledged Promoter Holdings, Retail Investor Holding, Insurance Firms Holding, No. of Shareholders
- **Computed-from-official (14):** MF Holding Change (3M/6M), DII Holding Change (3M/6M), FII Holding Change (3M/6M), Promoter Holding Change (3M/6M), Insider Trades (1M/3M/6M Cumulative), Bulk Deals (1M/3M/6M Cumulative)

### 2.5 Futures & Options (28 filters)
- **Official-direct (7):** Lot Size, Future Close Price, Future Volume, Future Open Interest, Call Open Interest, Put Open Interest
- **Computed-from-official (21):** Fair Value, Fair Value Spread, Basis, Rollover Cost, Percentage Rollover, Calendar Spread, Cash & Carry Profit, Put Call Ratio, 1D/1W Change in Future OI, 1D/1W Change in Future Volume, 1D/1W Change in Call OI, 1D/1W Change in Put OI, Highest Call/Put OI Strikes, Highest 1D/1W OI Change CE/PE Strikes

### 2.6 Price and Volume (20 filters)
- **Official-direct (4):** Close Price, Daily Volume, Face value, VWAP
- **Computed-from-official (16):** Market Cap, 1D/1W/1M/6M/1Y Return, 5Y CAGR, 1W/1M/6M/1Y Return vs Nifty, % Away From 52W High, % Away From 52W Low, 1M/3M Average Volume, 1D/1W Change in Volume

### 2.7 Financial Ratios (14 filters)
- **Computed-from-official (14):** Current Ratio, Quick Ratio, Debt to Equity, Long Term Debt to Equity, Interest Coverage Ratio, Cash Conversion Cycle, Net Income / Liabilities, Working Capital Turnover Ratio, Inventory Turnover Ratio, Asset Turnover Ratio, Days of Inventory Outstanding, Days of Sales Outstanding, Days Payable Outstanding, Earning Power

### 2.8 Special / Quant Scores (5 filters)
- **Approximate (5):** Price Momentum Rank, Fundamental Score, Value Momentum Rank, Earnings Quality Rank, Price to Intrinsic Value Rank *(All labeled "Approximate - computed locally", full formulas documented in METRICS.md)*

### 2.9 Analyst Ratings (6 filters)
- **Unavailable (6):** Percentage Upside, Percentage Buy Reco's, Percentage Hold Reco's, Percentage Sell Reco's, No. of analysts with buy reco, Total no. of analysts *(Reason: Proprietary sell-side broker aggregation; not published in regulatory filings. Users can supply their own values via Excel upload)*

### 2.10 Technical Indicators (33 filters)
- **Official-direct (1):** Volume Weighted Average Price (bhavcopy)
- **Computed-from-official (32):** 1Y Max Loss, SMA (10/50/100/200D), EMA (10/50/100/200D), Alpha, Beta, Sharpe Ratio, Relative Volume, Volatility, Volatility vs Nifty, % Price above 1M/12M SMA, % Price above 1M EMA, RSI 14D, RSI Exponential 14D, ADX Rating, MACD Lines 1 & 2, Bollinger Band distances, Parabolic SAR distance, Williams %R, Stochastic %K & %D, 1W Change in OBV, 1W Change in AD Line, Super Trend

### 2.11 Balance Sheet & Cash Flow (39 filters)
- **Official-direct (39):** Book Value, Cash and Short-term Investments, Total Receivables, Total Inventory, Other Current Assets, Total Current Assets, Net Loans, Net PPE, Goodwill and Intangibles, Long Term Investments, Other Assets, Total Assets, Accounts Payable, Total Deposits, Other Current Liabilities, Total Current Liabilities, Total Long Term Debt, Total Debt, Deferred Income Tax, Minority Interest, Other Liabilities, Total Liabilities, Common Stock, Additional Paid-in Capital, Retained Earnings, Other Equity, Total Equity, Total Liabilities & Shareholders Equity, Common Shares Outstanding, Preferred Shares Outstanding, Policy Liabilities, Changes in Working Capital, Cash Flow from Operating Activities, Capital Expenditures, Cash from Investing Activities, Total Cash Dividends Paid, Cash from Financing Activities, Foreign Exchange Effects, Net Change in Cash

### 2.12 ETFs (2 filters)
- **Official-direct (1):** Expense Ratio (AMFI / AMC TER files)
- **Computed-from-official (1):** Tracking Error (annualized std dev of NAV return minus index return)

### 2.13 Income Statement (30 filters)
- **Official-direct (23):** Total Revenue, Cost of Revenue, Depreciation & Amortization, Interest & Other Items, Taxes & Other Items, Net Income, Earnings Per Share, Dividend Per Share, Power & Fuel Cost, Raw Materials, Operating & Other expenses, Employee Cost, Selling & Administrative Expenses, Research & Development, Interest Income, Total Interest Expense, Loan Loss Provision, Total revenue (Q), Net Income (Q), EPS (Q), Operating and Other Expenses (Q)
- **Computed-from-official (7):** Gross Profit, EBITDA, PBIT, PBT, Payout Ratio, Net Interest Income, EBITDA (Q), PBIT (Q), PBT (Q)

---

## 3. Official Source Endpoints Discovery Matrix

| Publishing Authority | Datasets | Publication Cadence | Automated / Manual |
|----------------------|----------|---------------------|-------------------|
| **NSE (National Stock Exchange)** | CM + F&O UDiFF bhavcopy, `EQUITY_L.csv`, `SME_EQUITY_L.csv`, `ind_nifty*list.csv`, `corporate-actions`, `snapshot-capital-market-largedeal`, `corporates-pit`, `corporate-share-holdings-master` (SHP XBRL), `corporates-financial-results` (Ind-AS XBRL) | Daily at EOD / Monthly / Quarterly | Automated with polite session rate limits + `data/inbox/` manual fallback (`SHP_*.xml`, `INDAS_*.xml`, `bulk_deals*.csv`, `block_deals*.csv`, `*insider*.csv`, `SME_EQUITY_L.csv`) |
| **BSE (Bombay Stock Exchange)** | CM + F&O UDiFF bhavcopy, `EQ_ISINCODE.csv` / `ScripMaster` | Daily at EOD | Automated UDiFF download; stops immediately on 403/WAF and accepts `data/inbox/` drop |
| **AMFI** | Half-yearly Market Cap classification XLSX (`CATEGORIZATION` header), `NAVAll.txt` (8-column semicolon daily ETF/MF NAVs), monthly TER CSV | Half-yearly (Jan/Jul), Daily (NAVs), Monthly (TER) | Automated parsers + `data/inbox/NAVAll.txt` & `data/inbox/TER_*.csv` fallback |
| **FBIL** | 3-Month Term MIBOR rate (`F&O Fair Value` benchmark) | Daily | Manual entry via `data/inbox/fbil_mibor.json` (browser/WAF gated; F&O Fair Value degrades gracefully to `Unavailable` if absent) |
| **SEBI / Exchange Filings** | PIT insider trades & Bulk/Block institutional deals | Daily / event-driven | Automated via NSE corporate filings endpoints (`corporates-pit`, `snapshot-capital-market-largedeal`) + `data/inbox/` fallback |

---

## 4. Feeding Jobs (`feeds`), Sector Applicability & Live Coverage Audit (`replica-v1.1`)

Every filter in [`registry/filters.yaml`](registry/filters.yaml) (and `apps/web/src/data/filters.json`) declares its exact producing feed (`feeds`), allowing the Add Filters modal and Table headers to show exact remediation commands instead of generic placeholders when empty:

| `feeds` Key | Target Sync Command | Filters | Notes |
|---|---|---|---|
| `weekly` | `make sync-weekly` | 2 | `face_value` (equity master) & Nifty Total Market 754 sector/industry map (`Unclassified` if unmapped/unlisted) |
| `daily` | `make sync-daily` | 3 | EOD Close, Daily Volume, Market Cap (`close * shares_outstanding / 1e7` unblocked via NSE `PR.zip` `mcap*.csv`) |
| `shp` | `make sync-shp` / `make sync-quarterly` | 17 | Promoter/DII/FII/MF/Retail/Insurance %, Pledge %, Shareholder count, 3M/6M deltas |
| `xbrl` | `make sync-quarterly` | 137 | Consolidated-first Annual (6Y) & Quarterly (4Q) financials, profitability, growth, valuation & ratios (`fin_quarantine` validated) |
| `deals` | `make sync-deals` | 6 | 1M/3M/6M cumulative Bulk/Block deals & SEBI PIT insider trades (% of issued shares) |
| `history` | `make backfill DAYS=400` | 49 | Multi-month/5Y returns (`DAYS=1300`), VWAP, SMA/EMA, RSI/ADX/MACD/SuperTrend/SAR (`"insufficient history"` until window filled) |
| `fno` | `make sync-daily` / `make backfill FO_DAYS=10` | 24 | NSE/BSE F&O basis, rollover, PCR, OI/volume changes, top call/put strikes |
| `amfi` | `make sync-weekly` | 2 | ETF Expense Ratio (TER) & Tracking Error (AMFI 6-month avg market cap kept separate as `amfi_avg_mcap_crs`) |
| `manual` | `data/inbox/` | 3 | FBIL 3M MIBOR F&O Fair Value, Fair Value Spread & ETF TER CSV drops |
| `unavailable` | N/A | 12 | Analyst sell-side consensus ratings & forward estimates (`"Not available from official sources"`) |

- **Bank & Insurer Exclusions:** Ratios inapplicable to banking/insurance filings (`current_ratio`, `quick_ratio`, `debt_to_equity`, `long_term_debt_to_equity`, `working_capital_turnover_ratio`, `inventory_turnover_ratio`, `days_of_inventory_outstanding`, `days_of_sales_outstanding`, `days_payable_outstanding`, `cash_conversion_cycle`) display `"n/a for this sector"` / `"n/a (sector)"` rather than implying missing sync.
- **Unmapped / Unlisted Sectors:** Equities outside Nifty indices / Nifty Total Market CSVs (and without a manual BSE `ListofScripData*.csv` inbox drop) always render as `"Unclassified"` — never defaulted to `"Industrials"` or `"General"`. Run `make coverage` anytime to refresh [`docs/DATA_COVERAGE.md`](docs/DATA_COVERAGE.md).
