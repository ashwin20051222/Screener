# SCREENSHOT_MAP.md — Visual Reference Ground Truth

> Phase 0 deliverable. Exhaustive mapping of all 21 reference screenshots from `Images/`, taken from the original screener on 2026-10-21. This document serves as the visual ground truth for visual QA parity.

---

## Global Layout & Design Tokens (Measured from Screenshots)

### Dimensions & Grid
- **Main screen viewport:** ~1750 × 925 px (full browser window)
- **Modal viewport:** ~930 × 640 px (modal dialog overlaying the right pane)
- **Left filter panel width:** ~270–300 px (fixed width)
- **Right results pane:** Flexible, fills remaining width (~1450 px)
- **Modal width:** ~580–600 px total
  - Category rail (left): ~200–210 px
  - Filter checklist (right): ~370–390 px
- **Table row height:** ~38–40 px per row
- **Filter item row height (in modal):** ~32–36 px per row
- **Border radius:** 4–6 px on buttons and inputs

### Color Palette (Hex Values)
| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#FFFFFF` | Main page background, modal right panel background |
| `--panel-bg` | `#FFFFFF` / `#F7F8FA` | Left panel, table headers, category rail |
| `--border` | `#E5E7EB` / `#D1D5DB` | 1px dividers, button borders, input borders |
| `--text-primary` | `#111827` / `#1A1A2E` | Section titles, stock names, modal title, active items |
| `--text-secondary` | `#6B7280` | Subtitles, "No filters applied", inactive categories, table headers |
| `--primary-btn` | `#1E293B` / `#1A1A2E` | "+ Add Filter", "Done", "Save" buttons (dark navy/slate) |
| `--primary-btn-text` | `#FFFFFF` | Text on primary buttons |
| `--link-blue` | `#2563EB` | Active "Default" tab, "+ Create", "Show 2 More" |
| `--link-teal` | `#0D9488` | "Learn more about [Category]", "See how to create" footer links |
| `--slider-track-fill` | `#1E293B` / `#1A1A2E` | Filled portion of dual-thumb range slider |
| `--slider-track-bg` | `#E5E7EB` | Unfilled portion of range slider track |
| `--slider-thumb` | `#FFFFFF` | Round thumb handle with dark/gray border |
| `--checkbox-fill` | `#0891B2` / `#0D9488` | Checked checkbox background (teal-blue with white check) |
| `--lock-icon` | `#6B7280` / `#9CA3AF` | Padlock icon for locked/premium filters |

---

## Part 1: Main Application Screens (Screenshots 1–4)

All four main screens show 5,996 total results, sorted by **Market Cap** descending, with "No filters applied" and identical top 15 stocks.

### Top 15 Seed Stocks (Identical Across All Main Screens)
1. **Reliance Industries Ltd** | Oil & Gas - Refining & Marketi... | MC: 16,39,061.09 | PE: 20.29 | 1M: -2.60 | 1D: -0.76 | ROE: 7.71
2. **Bharti Airtel Ltd** | Telecom Services | MC: 11,88,457.35 | PE: 44.52 | 1M: 1.31 | 1D: -1.56 | ROE: 15.28
3. **HDFC Bank Limited** | Private Banks | MC: 11,23,775.87 | PE: 14.78 | 1M: -2.60 | 1D: -2.31 | ROE: 13.26
4. **ICICI Bank Limited** | Private Banks | MC: 10,03,030.89 | PE: 18.50 | 1M: 2.46 | 1D: -1.15 | ROE: 15.31
5. **Tata Consultancy Services Ltd** | IT Services & Consulting | MC: 8,91,858.57 | PE: 18.12 | 1M: 17.75 | 1D: -0.17 | ROE: 48.19
6. **State Bank of India** | Public Banks | MC: 8,88,553.61 | PE: 10.67 | 1M: -1.82 | 1D: 1.15 | ROE: 14.88
7. **Bajaj Finance Ltd** | Consumer Finance | MC: 6,11,249.60 | PE: 32.14 | 1M: -7.50 | 1D: -2.52 | ROE: 17.62
8. **Life Insurance Corporation Of India** | Insurance | MC: 5,03,153.57 | PE: 8.76 | 1M: -1.71 | 1D: -1.11 | ROE: 37.75
9. **Larsen and Toubro Ltd** | Construction & Engineering | MC: 4,99,050.87 | PE: 31.03 | 1M: -5.74 | 1D: 0.96 | ROE: 13.19
10. **Infosys Limited** | IT Services & Consulting | MC: 4,70,325.89 | PE: 15.98 | 1M: 8.56 | 1D: -2.63 | ROE: 31.07
11. **Kotak Mahindra Bank Ltd** | Private Banks | MC: 4,45,068.21 | PE: 23.08 | 1M: 6.53 | 1D: -1.14 | ROE: 11.39
12. **Hindustan Unilever Ltd** | FMCG - Household Products | MC: 4,44,965.59 | PE: 29.59 | 1M: -4.47 | 1D: -2.14 | ROE: 30.50
13. **National Stock Exchange of India Ltd** | Stock Exchanges & Ratings | MC: 4,32,988.88 | PE: 42.03 | 1M: -4.12 | 1D: -1.31 | ROE: 32.98
14. **Sun Pharmaceutical Industries Ltd** | Pharmaceuticals | MC: 4,21,995.03 | PE: 36.76 | 1M: -4.87 | 1D: -0.90 | ROE: 14.68
15. **Adani Ports and Special Economic ...** | Ports | MC: 4,03,377.16 | PE: 31.50 | 1M: -1.54 | 1D: 0.87 | ROE: 15.59

---

### Screenshot 1: `Screenshot From 2026-10-21 09-37-13.png`
- **View:** Main Screen with top of left panel visible
- **Left Panel Header:** "No filters applied" | outlined "Reset all" button
- **Expanded Section 1: Stock Universe (∧)**
  - Tabs: `Default` (active, blue #2563EB with underline) | `Custom` (inactive, gray)
  - Action link: `+ Create` (blue, right-aligned)
  - Checkboxes (all unchecked):
    - ☐ Nifty Smallcap 100
    - ☐ Nifty 500
    - ☐ Nifty Midcap 100
  - Link: `Show 2 More` (blue)
- **Expanded Section 2: Sector (∧)**
  - Search input: "Search by sector name" with 🔍 icon
  - Checklist with counts and sub-sector expand chevrons (all unchecked):
    - ☐ Consumer Discretionary (24) ∨
    - ☐ Communication Services (11) ∨
    - ☐ Consumer Staples (12) ∨
    - ☐ Energy (4) ∨
    - ☐ Financials (12) ∨
    - ☐ Health Care (5) ∨
    - ☐ Industrials (37) ∨
    - ☐ Information Technology (7) ∨
    - ☐ Materials (24) ∨
    - ☐ Real Estate (2) ∨
    - ☐ Utilities (7) ∨
    - ☐ ETF (4) ∨
- **Left Panel Bottom:** Full-width dark button `+ Add Filter`
- **Right Pane Header:** "Stock Screener", note input placeholder: `Add a note to remember why you created this - e.g., "Large-cap, low PE", "Auto sector picks" or "Tracking renewable energy".`, edit (✏️) icon, share (↗️) icon, dark "Save" button
- **Sub-bar:** "Showing **1 - 20** of **5996** results", "last updated at 6:30 AM IST" (ⓘ), outlined "🔒 Export" button, blue dot
- **Table Columns:** `⊕` | `Name` | `Sub-Sector` | `↓ Market Cap` | `PE Ratio` | `1M Return` | `1D Return` | `Return on Equity`

---

### Screenshot 2: `Screenshot From 2026-10-21 09-37-34.png`
- **View:** Main Screen scrolled to show Market Cap and Close Price filter widgets
- **Collapsed Sections (∨):** Stock Universe, Sector, PE Ratio, 1M Return (%), 1D Return (%), Return on Equity (%), PB Ratio
- **Expanded Section 1: Market Cap (∧)**
  - Dual-thumb range slider: left at 0%, right at ~85%
  - Inputs: `0.00` to `1639061.1`
  - Pill buttons: `Smallcap` | `Midcap` | `Largecap` (outlined, none selected)
- **Expanded Section 2: Close Price (Rs) (∧)**
  - Dual-thumb range slider: left at 0%, right at 100%
  - Inputs: `0.00` to `1125000.0`
  - Pill buttons: `Low` | `Mid` | `High` (outlined, none selected)
- **Table Columns (Note Close Price added):** `⊕` | `Name` | `Sub-Sector` | `↓ Market Cap` | **`Close Price`** | `PE Ratio` | `1M Return` | `1D Return` | `Retur...` (truncated)
- **Table Close Price values:** 1,202.00; 1,875.20; 712.00; 1,381.00; 2,460.90; 973.70; 957.35; 393.35; 3,661.90; 1,130.70; 442.30; 1,853.20; 1,726.55; 1,743.00; 1,766.00

---

### Screenshot 3: `Screenshot From 2026-10-21 09-37-53.png`
- **View:** Main Screen showing PE Ratio, 1M Return, and 1D Return filter widgets
- **Collapsed Sections (∨):** Market Cap, Close Price (Rs), Return on Equity (%), PB Ratio
- **Expanded Section 1: PE Ratio (∧)**
  - Slider: left at 0%, right at ~75%
  - Inputs: `-529.60` to `793.90`
  - Pills: `Low` | `Mid` | `High`
- **Expanded Section 2: 1M Return (%) (∧)**
  - Slider: full width 0% to 100%
  - Inputs: `-93.13` to `693.78`
  - Pills: `Low` | `Mid` | `High`
- **Expanded Section 3: 1D Return (%) (∧)**
  - Slider: left at 0%, right at ~85%
  - Inputs: `-19.84` to `20.00`
  - Pills: `Low` | `Mid` | `High`

---

### Screenshot 4: `Screenshot From 2026-10-21 09-38-05.png`
- **View:** Main Screen showing Return on Equity and PB Ratio filter widgets
- **Collapsed Sections (∨):** Stock Universe, Sector, Market Cap, Close Price (Rs), PE Ratio, 1M Return (%), 1D Return (%)
- **Expanded Section 1: Return on Equity (%) (∧)**
  - Slider: left at 0%, right at ~80%
  - Inputs: `-4016.59` to `883.96`
  - Pills: `Low` | `Mid` | `High`
- **Expanded Section 2: PB Ratio (∧)**
  - Slider: left at 0%, right at ~75–80%
  - Inputs: `-9.47` to `32.57`
  - Pills: `Low` | `Mid` | `High`

---

## Part 2: Add Filters Modal (Screenshots 5–21)

### Modal Common Layout
- **Left category rail** (14 categories in fixed order, top to bottom):
  1. `Profitability`
  2. `Growth`
  3. `Valuation`
  4. `Ownership`
  5. `Futures & Options`
  6. `Price and Volume`
  7. `Financial Ratios`
  8. `Tickertape Special`
  9. `Analyst Ratings`
  10. `Technical Indicators`
  11. `Balance Sheet & Cash Flow`
  12. `ETFs`
  13. `Income Statement`
  14. `Your Filters`
- **Header:** "Add Filters" (bold) | "Pick from over 200 filters" | outlined "Custom" button | "Search for Filters" input with 🔍
- **Footer:** 📗 "Learn more about [Category]" (teal link) | dark "Done" button
- **Right panel:** Scrollable list of checkboxes or lock (🔒) icons

---

### Screenshot 5: `Screenshot From 2026-10-21 09-38-31.png` — Profitability
- **Active Category:** `Profitability >`
- **Footer:** `Learn more about Profitability`
- **Filters visible (all unchecked, 0 locks):**
  1. ☐ 5Y Avg EBITDA Margin
  2. ☐ Return on Equity
  3. ☐ EBITDA Margin
  4. ☐ 5Y Avg Net Profit Margin
  5. ☐ Return on Investment
  6. ☐ 5Y Avg Return on Equity
  7. ☐ Return on Assets
  8. ☐ 5Y Avg Return on Assets
  9. ☐ Net Profit Margin
  10. ☐ 5Y Avg Return on Investment
  11. ☐ 5Y Avg Cash Flow Margin
  12. ☐ Cost of Goods Sold
  13. ☐ Cash Flow Margin
  14. ☐ ROCE

---

### Screenshot 6: `Screenshot From 2026-10-21 09-38-40.png` — Growth
- **Active Category:** `Growth >`
- **Footer:** `Learn more about Growth`
- **Filters visible (13 total, 4 locked):**
  1. 🔒 1Y Forward Revenue Growth
  2. ☐ 1Y Hist Op. Cash Flow Growth
  3. 🔒 1Y Forward EBITDA Growth
  4. ☐ 1Y Historical EPS Growth
  5. ☐ 1Y Historical Revenue Growth
  6. 🔒 1Y Fwd Op. Cash Flow Growth
  7. ☐ 5Y Historical EBITDA Growth
  8. ☐ 5Y Hist Op. Cash Flow Growth
  9. ☐ 3Y Historical Dividend Growth
  10. ☐ 5Y Historical EPS Growth
  11. ☐ 5Y Historical Revenue Growth
  12. ☐ 1Y Historical EBITDA Growth
  13. 🔒 1Y Forward EPS Growth

---

### Screenshot 7: `Screenshot From 2026-10-21 09-38-59.png` — Valuation (Top)
- **Active Category:** `Valuation >`
- **Footer:** `Learn more about Valuation`
- **Filters visible (top scroll position, 8 locked, 2 checked):**
  1. 🔒 PB Premium vs Sector
  2. 🔒 Dividend Yield vs Sector
  3. ☑ **PB Ratio** (checked)
  4. 🔒 PS Premium vs Sector
  5. ☐ PS Ratio
  6. ☐ EV/EBITDA Ratio
  7. ☑ **PE Ratio** (checked)
  8. 🔒 Forward PE Ratio
  9. 🔒 Forward PS Ratio
  10. ☐ Dividend Yield
  11. 🔒 PE Premium vs Sector
  12. ☐ EV / EBIT Ratio
  13. 🔒 PS Premium vs Sub-sector
  14. ☐ EV / Revenue Ratio
  15. 🔒 PE Premium vs Sub-sector
  16. (cut off at bottom)

---

### Screenshot 8: `Screenshot From 2026-10-21 09-39-13.png` — Valuation (Scrolled)
- **Active Category:** `Valuation >`
- **Footer:** `Learn more about Valuation`
- **Filters visible (bottom scroll position, 4 locked):**
  1. ☐ EV / EBIT Ratio (overlap)
  2. 🔒 PS Premium vs Sub-sector (overlap)
  3. ☐ EV / Revenue Ratio (overlap)
  4. 🔒 PE Premium vs Sub-sector (overlap)
  5. ☐ Price / Free Cash Flow
  6. ☐ EV / Invested Capital
  7. ☐ EV / Free Cash Flow
  8. ☐ Enterprise Value
  9. 🔒 PB Premium vs Sub-sector
  10. ☐ Price / CFO
  11. ☐ Price / Sales
  12. 🔒 Dividend Yield vs Sub-sector
  13. ☐ Sector Dividend Yield
  14. ☐ Sector PB
  15. ☐ Sector PE
  16. ☐ TTM PE Ratio

---

### Screenshot 9: `Screenshot From 2026-10-21 09-39-25.png` — Ownership (Top)
- **Active Category:** `Ownership >`
- **Footer:** `Learn more about Ownership`
- **Filters visible (top scroll position, 2 locked):**
  1. ☐ Mutual Fund Holding
  2. ☐ Domestic Institutional Holding
  3. ☐ MF Holding Change – 6M
  4. ☐ Promoter Holding Change – 3M
  5. ☐ Foreign Institutional Holding
  6. ☐ DII Holding Change – 6M
  7. ☐ FII Holding Change – 6M
  8. ☐ DII Holding Change – 3M
  9. ☐ Promoter Holding Change – 6M
  10. ☐ MF Holding Change – 3M
  11. ☐ Promoter Holding
  12. ☐ Pledged Promoter Holdings
  13. ☐ FII Holding Change – 3M
  14. 🔒 Insider Trades - 1M Cumulative
  15. 🔒 Insider Trades - 3M Cumulative
  16. (Retail Investor Holding partially visible at bottom)

---

### Screenshot 10: `Screenshot From 2026-10-21 09-39-42.png` — Ownership (Scrolled)
- **Active Category:** `Ownership >`
- **Footer:** `Learn more about Ownership`
- **Filters visible (bottom scroll position, 6 locked):**
  1. ☐ FII Holding Change – 6M (overlap)
  2. ☐ DII Holding Change – 3M (overlap)
  3. ☐ Promoter Holding Change – 6M (overlap)
  4. ☐ MF Holding Change – 3M (overlap)
  5. ☐ Promoter Holding (overlap)
  6. ☐ Pledged Promoter Holdings (overlap)
  7. ☐ FII Holding Change – 3M (overlap)
  8. 🔒 Insider Trades - 1M Cumulative (overlap)
  9. 🔒 Insider Trades - 3M Cumulative (overlap)
  10. ☐ Retail Investor Holding
  11. 🔒 Bulk Deals - 1M Cumulative
  12. 🔒 Bulk Deals - 6M Cumulative
  13. ☐ Insurance Firms Holding
  14. 🔒 Bulk Deals - 3M Cumulative
  15. 🔒 Insider Trades - 6M Cumulative
  16. ☐ No. of Shareholders

---

### Screenshot 11: `Screenshot From 2026-10-21 09-39-51.png` — Futures & Options (Top)
- **Active Category:** `Futures & Options >`
- **Footer:** `Learn more about Futures & Options`
- **Filters visible (top scroll position, 11 locked):**
  1. ☐ Lot Size
  2. ☐ Future Close Price
  3. 🔒 Fair Value
  4. 🔒 1D Change in Future OI
  5. 🔒 Rollover Cost
  6. 🔒 Highest Put OI Strike
  7. 🔒 1D Change in Future Volume
  8. ☐ Basis
  9. 🔒 Put Call Ratio
  10. 🔒 Cash & Carry Profit
  11. 🔒 1W Change in Put OI
  12. ☐ Future Open Interest
  13. 🔒 Highest 1D OI Change CE Strike
  14. 🔒 Highest 1D OI Change PE Strike
  15. 🔒 Highest 1W OI Change CE Strike

---

### Screenshot 12: `Screenshot From 2026-10-21 09-40-08.png` — Futures & Options (Scrolled)
- **Active Category:** `Futures & Options >`
- **Footer:** `Learn more about Futures & Options`
- **Filters visible (bottom scroll position, 13 locked):**
  1. 🔒 Highest 1D OI Change CE Strike (overlap)
  2. 🔒 Highest 1D OI Change PE Strike (overlap)
  3. 🔒 Highest 1W OI Change CE Strike (overlap)
  4. 🔒 1W Change in Future Volume
  5. 🔒 1W Change in Future OI
  6. 🔒 Fair Value Spread
  7. ☐ Future Volume
  8. 🔒 Highest Call OI Strike
  9. 🔒 Highest 1W OI Change PE Strike
  10. 🔒 1 D Change in Call OI *(note space: "1 D")*
  11. 🔒 1D Change in Put OI
  12. ☐ Call Open Interest
  13. 🔒 1W Change in Call OI
  14. 🔒 Percentage Rollover
  15. 🔒 Calendar Spread
  16. ☐ Put Open Interest

---

### Screenshot 13: `Screenshot From 2026-10-21 09-40-23.png` — Price and Volume (Top)
- **Active Category:** `Price and Volume >`
- **Footer:** `Learn more about Price and Volume`
- **Filters visible (top scroll position, 0 locked, 3 checked):**
  1. ☐ 1M Average Volume
  2. ☑ **1M Return** (checked)
  3. ☐ Daily Volume
  4. ☐ 1Y Return vs Nifty
  5. ☑ **Close Price** (checked)
  6. ☐ 1M Return vs Nifty
  7. ☐ 1W Change in Volume
  8. ☐ 3M Average Volume
  9. ☐ 1W Return
  10. ☐ 6M Return vs Nifty
  11. ☐ % Away From 52W High
  12. ☑ **1D Return** (checked)
  13. ☐ 6M Return
  14. ☐ 1Y Return
  15. ☐ 1W Return vs Nifty
  16. (1D Change in Volume partially cut off)

---

### Screenshot 14: `Screenshot From 2026-10-21 09-40-32.png` — Price and Volume (Scrolled)
- **Active Category:** `Price and Volume >`
- **Footer:** `Learn more about Price and Volume`
- **Filters visible (bottom scroll position, 0 locked, 2 checked):**
  1. ☐ 1Y Return vs Nifty (overlap)
  2. ☑ **Close Price** (checked)
  3. ☐ 1M Return vs Nifty (overlap)
  4. ☐ 1W Change in Volume (overlap)
  5. ☐ 3M Average Volume (overlap)
  6. ☐ 1W Return (overlap)
  7. ☐ 6M Return vs Nifty (overlap)
  8. ☐ % Away From 52W High (overlap)
  9. ☑ **1D Return** (checked)
  10. ☐ 6M Return (overlap)
  11. ☐ 1Y Return (overlap)
  12. ☐ 1W Return vs Nifty (overlap)
  13. ☐ 1D Change in Volume
  14. ☐ % Away From 52W Low
  15. ☐ Face value *(note lowercase 'v')*
  16. ☐ 5Y CAGR

---

### Screenshot 15: `Screenshot From 2026-10-21 09-40-39.png` — Financial Ratios
- **Active Category:** `Financial Ratios >`
- **Footer:** `Learn more about Financial Ratios`
- **Special UI State:** Left panel PB Ratio widget shows a **"Remove"** link next to chevron ∧
- **Filters visible (14 total, 3 locked):**
  1. ☐ Current Ratio
  2. ☐ Cash Conversion Cycle
  3. ☐ Long Term Debt to Equity
  4. ☐ Interest Coverage Ratio
  5. ☐ Debt to Equity
  6. ☐ Quick Ratio
  7. ☐ Net Income / Liabilities
  8. ☐ Working Capital Turnover Ratio
  9. ☐ Inventory Turnover Ratio
  10. ☐ Asset Turnover Ratio
  11. 🔒 Days of Inventory Outstanding
  12. 🔒 Days of Sales Outstanding
  13. ☐ Earning Power
  14. 🔒 Days Payable Outstanding

---

### Screenshot 16: `Screenshot From 2026-10-21 09-40-48.png` — Tickertape Special (Quant Scores)
- **Active Category:** `Tickertape Special >` *(Note: labeled "Tickertape Special" in original, we use "Special" / "Quant Scores")*
- **Footer:** `Learn more about Tickertape Special`
- **Filters visible (all 5 locked, 0 checkboxes):**
  1. 🔒 Price Momentum Rank
  2. 🔒 Fundamental Score
  3. 🔒 Value Momentum Rank
  4. 🔒 Earnings Quality Rank
  5. 🔒 Price to Intrinsic Value Rank

---

### Screenshot 17: `Screenshot From 2026-10-21 09-40-57.png` — Analyst Ratings
- **Active Category:** `Analyst Ratings >`
- **Footer:** `Learn more about Analyst Ratings`
- **Filters visible (all 6 locked, 0 checkboxes):**
  1. 🔒 Percentage Upside
  2. 🔒 Percentage Buy Reco's
  3. 🔒 No. of analysts with buy reco
  4. 🔒 Percentage Sell Reco's
  5. 🔒 Percentage Hold Reco's
  6. 🔒 Total no. of analysts

---

### Screenshot 18: `Screenshot From 2026-10-21 09-42-11.png` — ETFs
- **Active Category:** `ETFs >`
- **Footer:** `Learn more about ETFs`
- **Filters visible (2 total, 0 locked):**
  1. ☐ Expense Ratio
  2. ☐ Tracking Error

---

### Screenshot 19: `Screenshot From 2026-10-21 09-42-19.png` — Income Statement (Top)
- **Active Category:** `Income Statement >`
- **Footer:** `Learn more about Income Statement`
- **Filters visible (top scroll position, 0 locked):**
  1. ☐ EBITDA
  2. ☐ Net Income
  3. ☐ Payout Ratio
  4. ☐ Earnings Per Share
  5. ☐ Taxes & Other Items
  6. ☐ Dividend Per Share
  7. ☐ PBIT
  8. ☐ Interest & Other Items
  9. ☐ Total Revenue
  10. ☐ Depreciation & Amortization
  11. ☐ PBT
  12. ☐ Power & Fuel Cost
  13. ☐ Raw Materials
  14. ☐ Operating & Other expenses *(note lowercase 'e')*
  15. ☐ Employee Cost
  16. ☐ Selling & Administrative Expenses (partially cut off)

---

### Screenshot 20: `Screenshot From 2026-10-21 09-42-29.png` — Income Statement (Scrolled)
- **Active Category:** `Income Statement >`
- **Footer:** `Learn more about Income Statement`
- **Filters visible (bottom scroll position, 0 locked):**
  1. ☐ Interest & Other Items (overlap)
  2. ☐ Total Revenue (overlap)
  3. ☐ Depreciation & Amortization (overlap)
  4. ☐ PBT (overlap)
  5. ☐ Power & Fuel Cost (overlap)
  6. ☐ Raw Materials (overlap)
  7. ☐ Operating & Other expenses (overlap)
  8. ☐ Employee Cost (overlap)
  9. ☐ Selling & Administrative Expenses
  10. ☐ Net Income (Q)
  11. ☐ Total revenue (Q) *(note lowercase 'r')*
  12. ☐ EPS (Q)
  13. ☐ EBITDA (Q)
  14. ☐ Operating and Other Expenses (Q) *(note 'and' vs '&', uppercase 'E')*
  15. ☐ PBIT (Q)
  16. ☐ PBT (Q)

---

### Screenshot 21: `Screenshot From 2026-10-21 09-42-37.png` — Your Filters (Empty State / CTA)
- **Active Category:** `Your Filters >`
- **NOT A DUPLICATE** — distinct custom filter onboarding view!
- **Right Panel Content:**
  - Informational text (centered):
    `Create your custom filter by using`
    `existing filters and operators like + , - ,`
    `* and /`
  - Button: Outlined **`Create Custom Filter`** (centered, rounded border, dark text)
- **Footer:** 📗 `See how to create Your Filters` *(note different phrasing: "See how to create" instead of "Learn more about")*

---

## Part 3: Missing Categories in Screenshots (Per Prompt Section 2 & 10)

The following two categories have **no screenshot in the reference set**:
1. **Technical Indicators** (32 filters from section 10.9): SMA/EMA variants, RSI, ADX, MACD, Bollinger Bands, Parabolic SAR, Williams %R, Stochastic, OBV, AD Line, Super Trend, Max Loss, Volatility, Beta, Alpha, Sharpe, Relative Volume
2. **Balance Sheet & Cash Flow** (38 filters from section 10.10): Book Value, Cash, Receivables, Inventory, Assets, Liabilities, Debt, Equity, Operating/Investing/Financing Cash Flows, Capex, FCF

Both will be implemented faithfully from section 10 specifications in `registry/filters.yaml` and the UI replica.

