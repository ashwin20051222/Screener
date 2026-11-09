<USER_REQUEST>
# Stock Screener Replica: Antigravity Build Prompt (v1)

## 0. How to use this file

1. Save this file in the project root: `Documents/Fun Project/TickerTapeScreening/` (next to `screener.html` and `Images/`).
2. Open that exact folder in Antigravity (File > Open Folder). Start in **Planning mode**.
3. Make sure the REA MCP server is enabled (Agent pane > "..." > MCP Servers).
4. Send ONE message at a time:
   - `Read ./ANTIGRAVITY_BUILD_PROMPT.md fully. Execute Phase 0 only, then stop.`
   - After you review: `Approved. Execute Phase 1 only, then stop.` and so on.
5. After the replica is finished (tag `replica-v1`), send customization requests one by one using the template in section 14.

The agent must run exactly the phase named in your message and then stop at the gate. It must never run ahead.

---

## 1. Role, mission, success

You are a senior full-stack and data engineer working inside Antigravity.

**Mission:** build a complete, working, offline-first replica of a Tickertape-style Indian stock screener: the same layout, the same filter system, the same behaviours, with one twist: the stock universe comes from an Excel file I upload.

**Success means:**
- The UI matches my reference screenshots (section 6).
- Every filter in the catalog (section 10) exists. Each one works with real data, or shows an honest "Not available from official sources" badge. Nothing is faked.
- All market data comes from official sources only (section 9).
- I can then ask for customizations one at a time without anything breaking (section 14).

Do not copy Tickertape's name, logo, copy, code or assets. Replicate layout and behaviour only. Write all glossary and help text yourself.

---

## 2. What already exists (project state)

Folder: `TickerTapeScreening/`

- `screener.html`: a single-file prototype UI built earlier. Vanilla JS, no build step. It already has:
  - two-pane layout, left filter panel, Add Filters modal, table with sortable columns and column picker (+)
  - registry of about 250 filter names in 14 categories, with a few formula tooltips
  - dual-handle sliders, number inputs, Low/Mid/High presets, Market Cap Smallcap/Midcap/Largecap presets
  - sector checklist with counts, universe tabs (Default/Custom), Excel/CSV upload through SheetJS
  - custom-filter builder (2 to 5 metrics, safe expression parser), saved screens in localStorage, copy-as-CSV export
  - derived metrics: PE/PB/PS premium vs sector and sub-sector, dividend yield vs sector (computed over the loaded rows only)
  - sample data: 15 rows transcribed from my screenshots (name, sub-sector, market cap, close price, PE, 1M return, 1D return, ROE)
- `Images/`: 21 PNG screenshots of the original screener, named `Screenshot From 2026-10-21 HH-MM-SS.png`.

**Known limits of the prototype (to fix in the phases below):** it is one file; data is a 15-row sample; only 6 metrics have values; no real downloads (clipboard only); no backend; no official-data connectors; no technical-indicator or quant-score engine; no security-master matching for uploaded Excel; no stock detail drawer; sector rows have no sub-sector expansion; "Show N more" universes and "Learn more about..." glossary pages are not built.

**Screenshot hints (verify yourself, do not trust blindly).** In timestamp order, the first four show the main screen with different left-panel sections open (Stock Universe + Sector; Market Cap + Close Price; PE + 1M Return + 1D Return; Return on Equity + PB Ratio). The next ones show the Add Filters modal, one category at a time: Profitability, Growth, Valuation (2 images), Ownership (2), Futures & Options (2), Price and Volume (2), Financial Ratios, Special (quant ranks), Analyst Ratings, ETFs, Income Statement (2). There are **no** screenshots for Technical Indicators or Balance Sheet & Cash Flow (build those from section 10). The 21st image may be a duplicate or something new; identify it.

---

## 3. Operating rules (non-negotiable)

1. **One phase per instruction.** Stop at every `STOP GATE` and wait for me.
2. **Plan first.** At the start of each phase, produce an Implementation Plan artifact and a Task List artifact. At the end, a Walkthrough artifact with screenshots.
3. **Single source of truth.** All filter definitions (id, label, category, unit, formula, source, frequency, null rule, locked-in-original flag) live in one registry file (`registry/filters.yaml`). The UI, API, glossary, column picker and tests all read from it.
4. **No fabricated data.** Never invent, estimate or hardcode market numbers. Test fixtures must be labelled `fixture` and live only under `tests/`. If a value cannot be sourced officially, show "Not available from official sources".
5. **Honest labels.** Every metric is tagged: `Official-direct`, `Computed-from-official`, `Approximate`, or `Unavailable`. Keep `DATA_AVAILABILITY.md` in sync.
6. **Traceability.** Every displayed number has source + as-of date (tooltip).
7. **Small, reversible changes.** `git init` on day one. One commit per task. Tag `baseline-prototype` before touching `screener.html`.
8. **Continuity file.** After every task, update `PROJECT_STATE.md` (current phase, done, next, decisions, open questions). A fresh agent session must be able to resume from it alone.
9. **Token economy.** After Phase 0, do not re-open all 21 screenshots again. Use `SCREENSHOT_MAP.md`. Open a single image only when checking that one screen.
10. **Ask rarely.** Make a reasonable assumption, write it in `ASSUMPTIONS.md`, and continue. Ask me only when truly blocked.
11. **Scope guard.** Do not add features I did not ask for. Do not refactor unrelated code.

---

## 4. REA usage policy

REA ("Reverse Engineer Anything") is an MCP server for inspecting binaries, web/Electron apps, browser pages and data files. First, list the REA tools that are actually available and record them in `TOOLS.md` (name, what it does, how you will use it). Never assume a tool exists.

**Allowed uses**
- **Verify our own build:** inspect the running local app (DOM, console errors, network calls, performance), and compare its rendering with the reference screenshots.
- **Discover official data:** inspect the public pages of NSE, BSE, SEBI, AMFI and FBIL to find legitimate downloadable files and their schemas (CSV/ZIP/XLS/XBRL/PDF), file naming, publication times and rate limits.
- **Inspect downloaded official files** to learn their structure before writing parsers.

**Forbidden uses**
- Do not decompile, deobfuscate or copy Tickertape's JavaScript, private APIs, assets or data. Do not call Tickertape endpoints. (Its public Learn pages were already used for definitions; formulas in section 10 are complete. Do not copy its prose.)
- Do not bypass logins, paywalls, bot protection or rate limits on any site.

If an official site blocks automated download, add a **manual import inbox** (`data/inbox/`): I download the official file by hand, drop it there, and the parser ingests it.

---

## 5. Phases and stop gates

### Phase 0: Audit (no code changes)
1. Create `TOOLS.md` (REA tools, and any Antigravity browser tool you can use for screenshots).
2. View all 21 screenshots. Write `SCREENSHOT_MAP.md`: for each file, what it shows, every visible label/text read verbatim, element states (checked, locked, hover, selected category), and measured layout (panel widths, row heights, spacing, colours as hex).
3. Read `screener.html` fully. Write `AUDIT.md`: what matches the screenshots, what deviates, bugs, and missing features (use the lists in sections 6 to 8 as the checklist).
4. Create `registry/filters.yaml` skeleton and `FILTER_CATALOG.md`: union of the filters visible in screenshots and section 10, with flags `in_screenshot`, `locked_in_original`, `needs_official_source`, `availability`.
5. Propose the target architecture and folder structure (section 5.1) with reasons.

**STOP GATE 0:** show me the plan and wait.

### Phase 1: Faithful UI replica (the first priority)
1. Scaffold the project (section 5.1). Move `screener.html` logic into modules without changing behaviour. Keep the original file as `legacy/screener.html`.
2. Reach visual parity with the reference screenshots, using the loop in section 6.4. Cover: the 4 main states, all modal categories (including empty states for Technical Indicators and Balance Sheet & Cash Flow), hover/selected states, "Show N more", Remove link, Reset all, Save disabled/enabled.
3. Replace prototype shortcuts with real behaviour that needs no data engine: real file download for Export (CSV + XLSX), share as JSON file + copy, import saved screen, infinite scroll with page size 20, sector sub-sector expansion, in-app glossary pages ("Learn more about ..." per category), stock detail drawer (shell only), keyboard accessibility, responsive layout, light/dark theme via CSS variables.
4. Data in this phase is the 15-row seed from the prototype (labelled "fixture/seed"). Do not pad it with invented rows.
5. Produce `VISUAL_QA.md` with side-by-side screenshot comparisons and a deviation list (target: zero known deviations).

**STOP GATE 1:** I review the UI. Tag `ui-replica-v1`.

### Phase 2: Registry, metrics engine, query engine
1. Complete `registry/filters.yaml` for every filter in section 10 (formula, inputs, units, null rules, direction-of-goodness, glossary text in your own words).
2. Implement the metrics module (versioned formulas) and a query engine: AND-combined range / enum / boolean / formula filters; sorting (nulls last); pagination; Low/Mid/High tertile presets; market-cap category presets; sector and sub-sector counts that follow the active universe.
3. Benchmarks (sector PE etc.) use the full listed market; filtering and sorting use the active universe (config `benchmark_scope = market | universe`, default `market`).
4. Custom filter builder: 2 to 5 data items, safe parser (no `eval`), verify on sample stocks, saved under "Your Filters".
5. Pass all golden tests in section 12.

**STOP GATE 2.**

### Phase 3: Excel universe (the twist)
Implement everything in section 8. Include the match report UI and the 30-row end-to-end test sheet (3 unmatched, 2 ambiguous rows).

**STOP GATE 3.**

### Phase 4: Official data connectors (one connector per sub-step, stop after step 4.1)
- 4.1 Security master + daily EOD prices (bhavcopy) + corporate actions. Write `DATA_SOURCES.md` first (URL, format, ToS/robots note, refresh rate, as discovered with REA). **STOP and show me before continuing.**
- 4.2 Index constituents and market-cap categorisation (AMFI).
- 4.3 F&O data (futures, options OI, lot sizes) and MIBOR (FBIL).
- 4.4 Shareholding patterns, pledges, bulk/block deals, insider (SEBI PIT) disclosures.
- 4.5 Financial statements (XBRL results, annual reports) for income statement, balance sheet, cash flow, with sector templates (banks, insurers, industrials).
- 4.6 Technical indicators computed from the stored price history.
- 4.7 ETF expense ratio and tracking error (AMFI / AMC official files).
Each connector: retries with backoff, polite rate limits, raw-file cache, schema validation, idempotent upserts, reconciliation checks against the exchange's own published files for 10 stocks, and a scheduler entry.

**STOP GATE 4 after each sub-step.**

### Phase 5: Quant scores, hardening, docs, packaging
Quant scores (section 11), full test run, performance check on 6,000+ stocks, README, `METRICS.md`, `DATA_AVAILABILITY.md`, one-command start, optional desktop packaging. Tag `replica-v1`.

**STOP GATE 5.** Customization mode begins (section 14).

### 5.1 Default architecture (change only with a written reason)
- Front end: Vite + React + TypeScript, CSS variables for themes.
- Back end: Python 3.12 + FastAPI.
- Storage: DuckDB + Parquet cache; raw downloads cached under `data/raw/`.
- Run: `make run` starts everything. No login. Works offline after the first sync.
- Layout: `apps/web`, `apps/api`, `registry/`, `connectors/`, `config/` (sector map, presets, scores), `data/` (raw, inbox, db), `tests/`, `docs/`, `legacy/`.

---

## 6. Design spec (ground truth = my screenshots)

Reference viewport for the main screens is about 1750 x 925; the Add Filters modal crops are about 930 x 640.

### 6.1 Layout and tokens
- Full-height two-pane card with a thin light border. Left filter panel about 300px wide; right results pane flexible.
- Colours (CSS variables, light default): white content; very light grey (`#f7f8fa`) panel and table header; 1px light dividers; near-black navy for primary buttons ("Add Filter", "Done"); blue links ("+ Create", "Show 2 More", active "Default" tab with underline, "Learn more about X"); disabled grey "Save". Measure exact hex values in Phase 0 and record them.
- Typography: clean grotesque sans (Inter or Figtree); tabular, right-aligned numbers; 4 to 6px radius.

### 6.2 Left panel (top to bottom)
- Header row: "No filters applied" or "N filters applied" + outlined "Reset all".
- Collapsible sections with chevrons:
  - **Stock Universe**: tabs `Default | Custom`, "+ Create"; checkboxes Nifty Smallcap 100, Nifty 500, Nifty Midcap 100; link "Show 2 More".
  - **Sector**: search box "Search by sector name"; checklist with counts, for example "Consumer Discretionary (24)", each row with a chevron that expands sub-sectors. Sectors: Consumer Discretionary, Communication Services, Consumer Staples, Energy, Financials, Health Care, Industrials, Information Technology, Materials, Real Estate, Utilities, ETF.
  - Default numeric filters: **Market Cap, Close Price (Rs), PE Ratio, 1M Return (%), 1D Return (%), Return on Equity (%), PB Ratio**.
- Numeric filter body: dual-handle slider (thin dark track, white round handles with grey border), two bordered right-aligned inputs separated by "to", then a 3-segment button group **Low | Mid | High** (Market Cap: **Smallcap | Midcap | Largecap**). A "Remove" link appears in the section header of added filters.
- Pinned bottom: full-width dark **"+ Add Filter"** button.
- Slider bounds are the min/max of the active universe for that metric. The reference shows trimmed-looking bounds (for example 1D Return max 20.00), so default to true min/max and offer optional percentile trimming for display only; the inputs accept any value.

### 6.3 Add Filters modal and right pane
- Modal anchored to the right of the left panel, overlaying results. Title "Add Filters", subtitle "Pick from over 200 filters", top-right outlined **Custom** button and search box **"Search for Filters"**.
- Two columns: category rail (active category bold with ">" chevron) and a scrollable checkbox list (dark filled box when selected; checked = already added). Footer: green book icon + "Learn more about <Category>" link, and dark **Done** button. Lock icons in the original mark premium filters; **in this build nothing is locked**.
- Category rail order: Profitability, Growth, Valuation, Ownership, Futures & Options, Price and Volume, Financial Ratios, Special (quant scores), Analyst Ratings, Technical Indicators, Balance Sheet & Cash Flow, ETFs, Income Statement, Your Filters.
- Right pane: title "Stock Screener"; note line ("Add a note to remember why you created this - e.g., "Large-cap, low PE", "Auto sector picks" or "Tracking renewable energy""); icon buttons for edit and share; **Save** (disabled until something changes).
- Sub-bar: "Showing **1 - 20** of **N** results"; "last updated at <time> IST" with info icon; outlined **Export**; round **?** help button.
- Table: sticky header; "(+)" column picker at the far left; columns `#`, `Name` (semi-bold), `Sub-Sector` (ellipsis), then metrics. Default columns: **Market Cap** (default sort, descending arrow), Close Price, PE Ratio, 1M Return, 1D Return, Return on Equity. Each newly added filter appends a column on the right. Row height about 45px, hover highlight, horizontal scroll, Indian digit grouping (16,39,061.09), Market Cap in Rs Cr, 2 decimals.

### 6.4 Visual QA loop (use for every screen)
1. Start the app. Use the Antigravity browser agent (or REA's browser tools) at the reference viewport.
2. Reproduce the exact state of one reference screenshot (same sections open, same filters, same data).
3. Capture, compare side by side, list deviations (position, size, colour, text, state), fix, repeat.
4. Log results in `VISUAL_QA.md`. A screen passes only when no deviation is left.

---

## 7. Screener behaviour spec

- Filters combine with AND. Range: `min <= value <= max`. A null value is excluded when that filter is active.
- Setting a range adds a column. Per-filter Reset clears the range. Remove deletes the filter and its column.
- Sort asc/desc on any column (server-side), nulls last. Pagination 20 rows, infinite scroll.
- **Presets:** Low/Mid/High = tertiles of the active universe's non-null values (`config/presets.yaml` can override per metric). Market-cap presets use the AMFI half-yearly categorisation: Large = rank 1 to 100, Mid = 101 to 250, Small = 251+.
- Sector counts = stocks per sector in the active universe, updating live.
- **Saved screens:** name + note + universe + filters + columns + sort. Save, load, duplicate, delete. "All Screens" page with built-in screens made only from implemented filters (Low-Debt Midcaps, Near 52W Lows, High Dividend Yield, High ROE + Low PE, Promoter Buying, Strong Momentum, F&O Long Buildup, Debt-free Smallcaps).
- **Share:** export/import a screen as JSON.
- **Export:** CSV and XLSX of the current result with visible columns, units and as-of date.
- **Custom filter:** 2 to 5 data items with `+ - * / ( )`, name it, "Verify" dry-run on sample stocks, saved under "Your Filters".
- Hover on a filter shows its definition and formula. "Learn more about <Category>" opens an in-app glossary page (definition, formula, source, frequency, and availability label for each filter).

---

## 8. Excel universe (core feature)

- Upload `.xlsx`, `.xls`, `.csv` (drag-drop). Choose the sheet. Auto-detect the identifier column (ISIN / Symbol / Ticker / Company Name / Scheme Name) and let me confirm or remap it.
- Match order: ISIN, then NSE symbol, then BSE code, then exact normalised name, then fuzzy name (threshold in config).
- **Match report:** matched / ambiguous / unmatched, with manual-fix dropdowns. Never silently drop a row.
- Save as a named Custom universe (Stock Universe > Custom > "+ Create"). Rename, delete, re-upload/refresh. Several universes can be selected at once (union), and combined with the default ones (Nifty 50/100/500, Midcap 100, Smallcap 100, All NSE+BSE listed).
- Keep my extra Excel columns (quantity, buy price, notes) as optional table columns. If quantity and buy price exist, compute optional P&L.
- Support stocks, ETFs and fund-holding style lists (a security-type column).
- A header-template helper ("Copy template headers") lists all filter names so I can prefill my own sheet.

---

## 9. Data policy and official sources

Use official sources only. Discover current endpoints yourself (do not guess URLs) and record them in `DATA_SOURCES.md` with format, ToS/robots note and refresh time. Respect rate limits; cache raw files; idempotent upserts; schema validation; reconciliation checks.

- **NSE:** UDiFF common bhavcopy (cash + F&O: futures and options prices, OI, volume, strikes), securities master, F&O lot sizes, bulk and block deals, corporate filings (financial results XBRL, shareholding patterns, promoter pledge data, SEBI PIT insider disclosures), index constituents and factsheets (NSE Indices).
- **BSE:** UDiFF bhavcopy, scrip master (ISIN, BSE-only stocks), XBRL results, shareholding patterns, bulk deals, announcements.
- **SEBI:** PIT/SAST disclosures, classification circulars.
- **AMFI:** half-yearly large/mid/small categorisation, monthly mutual-fund portfolio disclosures, ETF/scheme expense ratios.
- **FBIL:** 3-month MIBOR (fair value of futures).
- Company annual/quarterly reports published on exchange sites where XBRL lacks an item.

The screenshot header shows "last updated at 6:30 AM IST": schedule the daily job early morning IST; fundamentals quarterly; shareholding quarterly.

**Security master:** ISIN, NSE symbol, BSE code, name, listing status (exclude delisted), face value, sector, sub-sector, industry, F&O flag, ETF flag, shares outstanding. Map the official exchange industry classification to the 12 sector groups in the UI through `config/sector_map.yaml`. Consolidated statements first, standalone as fallback (flag which one was used). Market cap = close x shares outstanding / 1e7 (Rs Cr).

---

## 10. Conventions and the full filter catalog

### 10.1 Conventions
`FY0` = latest reported fiscal year, `FY-n` = n years earlier. `Q0` = latest quarter. `TTM` = last 4 quarters. `P` = latest close. `MC` = market cap (Rs Cr). `avg2(x) = (x[FY0] + x[FY-1]) / 2`. `avg5(x)` = mean of x over FY0 to FY-4. `CAGR_n(x) = (x[FY0] / x[FY-n])^(1/n) - 1` (needs n+1 yearly points; null if start or end <= 0).
Windows: 1W = 5 trading days; 1M = 4 weeks for returns (20 trading days for SMA/EMA); 6M = 26 weeks; 1Y = 52 weeks; 12M SMA = 250 trading days. "vs Nifty" = stock % change minus Nifty 50 % change (a difference). Division by zero or a negative denominator gives null (log the reason).

### 10.2 Profitability
- Return on Equity = Net profit / avg2(common equity)
- Return on Assets = Net profit / avg2(total assets)
- Return on Investment = Net income / avg2(equity + long-term debt + other long-term liabilities)
- ROCE = EBIT / (total assets - current liabilities)
- Net Profit Margin = Net profit / revenue; EBITDA Margin = EBITDA / revenue; Operating Profit Margin = operating profit / revenue; Cash Flow Margin = operating cash flow / revenue
- Cost of Goods Sold = absolute COGS (Rs Cr); null for lenders
- 5Y Avg variants (EBITDA margin, net profit margin, ROE, ROA, ROI, cash flow margin, operating margin) = avg5 of each annual ratio

### 10.3 Growth
- 1Y Historical Revenue / EBITDA / EPS / Operating Cash Flow Growth = X[FY0] / X[FY-1] - 1
- 5Y Historical Revenue / EBITDA / EPS / Operating Cash Flow Growth = CAGR_5
- 3Y Historical Dividend Growth = CAGR_3 of DPS
- 1Y Forward Revenue / EBITDA / EPS / Operating Cash Flow Growth = (consensus estimate for the current FY / actual FY0) - 1. **Unavailable** from official sources (needs analyst consensus). Keep schema and UI; allow an optional user-supplied column.

### 10.4 Valuation
- PE = P / EPS(FY0, before extraordinary items). TTM PE = P / EPS(TTM)
- PB = P / book value per share (total equity / shares outstanding)
- PS = P / (revenue(FY0) / shares). Price / Sales is the same quantity (alias)
- Dividend Yield (%) = DPS(FY0) / P x 100
- Enterprise Value = MC + total debt + minority interest - cash and short-term investments
- EV/EBITDA, EV/EBIT, EV/Revenue = EV / item(FY0)
- Price / CFO = MC / operating cash flow; Price / Free Cash Flow = MC / FCF; EV / Free Cash Flow = EV / FCF; FCF = operating cash flow - capex
- EV / Invested Capital = EV / IC. **Assumption:** IC = total equity + total debt + minority interest (configurable)
- Sector and sub-sector benchmarks (Sector PE / PB / PS / Dividend Yield, and sub-sector versions): over the whole listed market; default method = median of positive values (config: `median | trimmed_mean | aggregate`)
- PE / PB / PS Premium vs Sector and vs Sub-sector = stock multiple / benchmark - 1 (x100)
- Dividend Yield vs Sector = stock yield - sector yield (percentage points). The sub-sector version is documented ambiguously; use the same difference, and note it in `ASSUMPTIONS.md`
- Forward PE = P / estimated EPS; Forward PS = P / estimated revenue per share: **Unavailable**

### 10.5 Ownership (quarterly shareholding patterns; changes are percentage-point differences)
Mutual Fund Holding; Domestic Institutional Holding; Foreign Institutional Holding; Promoter Holding; Pledged Promoter Holdings (% of promoter shares pledged, plus % of total); Retail Investor Holding; Insurance Firms Holding; No. of Shareholders. Holding Change 3M / 6M (MF, DII, FII, Promoter) = current % minus the % one or two quarters earlier. Bulk Deals 1M / 3M / 6M Cumulative = sum(signed shares in bulk deals in the window) / shares outstanding x 100 (buy +, sell -; assumption). Insider Trades 1M / 3M / 6M Cumulative = the same from SEBI PIT disclosures (net buy minus sell).

### 10.6 Futures & Options (F&O-eligible stocks only; others null)
Lot Size; Future Close Price (near-month contract, previous traded day); Future Volume; Future Open Interest; 1D / 1W Change in Future OI and Future Volume = X / X[-1 or -5] - 1; Basis = futures price - spot; Fair Value = spot x (1 + r x days_to_expiry / 365) with r = 3M MIBOR (FBIL); Fair Value Spread = fair value - futures price; Cash & Carry Profit = futures price - fair value (assumption); Rollover Cost = next-month futures / near-month futures - 1; Percentage Rollover = OI(next) / OI(near + next + far); Calendar Spread = mid-month futures - near-month futures; Call Open Interest / Put Open Interest = sum across all strikes and expiries; Put Call Ratio = put OI / call OI; 1D / 1W Change in Call OI and Put OI; Highest Call OI Strike / Highest Put OI Strike = strike with the largest CE / PE OI; Highest 1D / 1W OI Change CE and PE Strike = strike with the largest % OI increase versus the previous day / 5 trading days earlier.

### 10.7 Price and Volume
Close Price; Market Cap; 1D / 1W / 1M / 6M / 1Y Return = P / P[window ago] - 1; 5Y CAGR = (P / P[5y ago])^(1/5) - 1 (adjusted for splits and bonuses from official corporate-action data); 1W / 1M / 6M / 1Y Return vs Nifty; % Away From 52W High = (High52 / Close) - 1 (as documented in the reference; configurable); % Away From 52W Low = (Close / Low52) - 1; Daily Volume; 1M / 3M Average Volume (mean over 21 / 63 trading days); 1D / 1W Change in Volume; Face Value; VWAP (day) = total traded value / total traded quantity from the bhavcopy.

### 10.8 Financial Ratios
Current Ratio = current assets / current liabilities; Quick Ratio = (current assets - inventory) / current liabilities; Debt to Equity = total debt / equity; Long Term Debt to Equity; Interest Coverage = EBIT / interest expense; Net Income / Liabilities; Earning Power = EBIT / total assets; Asset Turnover = revenue / avg2(total assets); Inventory Turnover = COGS / avg2(inventory); Working Capital Turnover = revenue / avg2(current assets - current liabilities); Days of Inventory Outstanding = avg2(inventory) / COGS x 365 (assumption); Days of Sales Outstanding = avg2(receivables) / revenue x 365 (assumption); Days Payable Outstanding = avg2(payables) / COGS x 365 (assumption); Cash Conversion Cycle = DIO + DSO - DPO. Show "n/a for this sector" where a ratio does not apply to banks or insurers.

### 10.9 Technical Indicators (no screenshot exists; build from official EOD OHLCV adjusted for corporate actions)
- SMA and EMA for 10, 50, 100, 200 days (EMA multiplier = 2/(n+1), seeded with the SMA)
- % Price above 1M SMA = Close / SMA(20) - 1; above 12M SMA = Close / SMA(250) - 1; above 1M EMA = Close / EMA(20) - 1
- RSI 14D (simple average of gains/losses) and RSI Exponential 14D (Wilder smoothing); ADX Rating (14) with +DI/-DI
- MACD Line 1 = EMA12 - EMA26; MACD Line 2 = MACD - EMA9(MACD)
- % From Upper Bollinger Band = Close / (SMA20 + 2 sd20) - 1; % From Lower Bollinger Band = Close / (SMA20 - 2 sd20) - 1
- % From Parabolic SAR = Close / SAR - 1 (AF 0.02, step 0.02, max 0.2)
- Williams %R (14) = (HH - Close) / (HH - LL) x (-100); Stochastic %K (14) = (Close - LL) / (HH - LL) x 100; %D = SMA3(%K)
- 1W Change in On Balance Volume = OBV / OBV[-5] - 1 (OBV adds volume on up-close days, subtracts on down-close days)
- 1W Change in AD Line = AD / AD[-5] - 1, where MFM = ((C-L) - (H-C)) / (H-L), MFV = MFM x Vol, AD = running sum of MFV
- Super Trend (ATR 10, multiplier 3; assumption) as signed distance + buy/sell flag
- 1Y Max Loss = worst peak-to-trough drawdown over the trailing year (the peak must come before the trough)
- Volatility = annualised standard deviation of daily returns over the last 200 trading days (x sqrt(252); assumption); Volatility vs Nifty = stock minus Nifty
- Beta = cov(r_stock, r_bench) / var(r_bench); Alpha = stock return - benchmark return (simple excess, as documented; label it clearly); Sharpe Ratio = (stock return - benchmark return) / st. dev. of weekly excess returns; all on 104 weekly closes; benchmark default Nifty 50
- Relative Volume = average volume of the last 10 trading days / average volume of the last ~91 days (window configurable)
- Extensions (mark "Extension"): CCI, ROC, MFI, Keltner/Donchian, Ichimoku, golden/death-cross flags, volume-spike flag, candlestick flags

### 10.10 Balance Sheet & Cash Flow (no screenshot exists; annual; sector-aware)
Book Value; Cash and Short-term Investments; Total Receivables; Total Inventory; Other Current Assets; Total Current Assets; Net Loans (banks); Net Property Plant Equipment; Goodwill and Intangibles; Long Term Investments; Other Assets; Total Assets; Accounts Payable; Total Deposits (banks); Other Current Liabilities; Total Current Liabilities; Total Long Term Debt; Total Debt; Deferred Income Tax; Minority Interest; Other Liabilities; Total Liabilities; Common Stock; Additional Paid-in Capital; Retained Earnings; Other Equity; Total Equity; Total Liabilities & Shareholders Equity; Total Common Shares Outstanding; Total Preferred Shares Outstanding; Policy Liabilities (insurers). Cash flow: Changes in Working Capital; Cash Flow from Operating Activities; Capital Expenditures; Cash from Investing Activities; Total Cash Dividends Paid; Cash from Financing Activities; Foreign Exchange Effects; Net Change in Cash; plus FCF = CFO - capex, FCF per share, FCF yield.
Integrity checks per stock: Assets = Liabilities + Equity; components reconcile; quarantine failures and flag them.

### 10.11 Income Statement (annual, plus quarterly "(Q)" variants with QoQ and YoY change)
Total Revenue; Cost of Revenue; Gross Profit = revenue - cost of revenue; EBITDA = gross profit - operating costs; Depreciation & Amortization; PBIT = EBITDA - D&A; Interest & Other Items; PBT = PBIT - interest & other; Taxes & Other Items; Net Income = PBT - taxes; Earnings Per Share = net income / shares; Dividend Per Share; Payout Ratio = DPS / EPS x 100; Power & Fuel Cost; Raw Materials; Employee Cost; Operating & Other expenses; Selling & Administrative Expenses; Research & Development; banks/NBFCs: Interest Income, Total Interest Expense, Net Interest Income, Loan Loss Provision. Quarterly: Total revenue (Q), Net Income (Q), EPS (Q), EBITDA (Q), Operating and Other Expenses (Q), PBIT (Q), PBT (Q).
Sector templates: industrials (operating costs = SG&A + R&D + unusual + FX items); utilities (add fuel and O&M to cost of revenue); insurers (revenue = earned premium; cost = claims, commissions, reinsurance); banks (revenue = interest + non-interest income; cost = interest expense + non-interest expense; loan loss provision inside operating expense).

### 10.12 ETFs and Analyst Ratings
- ETFs: Expense Ratio (AMFI / AMC official TER); Tracking Error = annualised st. dev. of (daily ETF NAV return - index return) over 1Y (assumption). ETF sector label "ETF".
- Analyst Ratings (Percentage Upside; Percentage Buy / Hold / Sell Reco's; No. of analysts with buy reco; Total no. of analysts): **Unavailable** from official sources. Keep schema and UI; allow an optional import from my own Excel columns.

---

## 11. Quant scores (the "Special" category): open approximations

Label every one "Approximate - computed locally". Never claim parity with Tickertape. Percentile ranks (0 to 100) are taken across the full listed market; weights live in `config/scores.yaml` and appear in an info popover.
- **Price Momentum Rank** = 0.6 x pct(12M return) + 0.4 x pct(12M return minus sub-sector median 12M return)
- **Earnings Quality Rank** = equal mix of pct(net profit margin), pct(asset turnover), pct(CFO / net income)
- **Price to Intrinsic Value Rank:** IV = median of the available estimates {EPS-based Graham formula, FCF-based perpetuity with growth, dividend-based}, documented in `METRICS.md`; low P/IV gives a high rank
- **Value Momentum Rank** = 0.5 x valuation percentile (growth-adjusted PE vs sector, using historical growth) + 0.5 x Price Momentum Rank
- **Fundamental Score (1 to 10)** = 1 + 9 x sector percentile of a composite of valuation (PE/PB premium vs sector), profitability (ROE, ROCE, net margin), growth (5Y revenue and EPS CAGR), financial health (debt to equity, interest coverage; bank-specific health metrics for financials)

---

## 12. Golden tests (must pass)

CAGR 700 to 960 over 5 years = 6.5%. PE 300/30 = 10. PE premium: 22.0 vs sector 17.6 = +25.0%; 12.3 vs 17.6 = -30.1%. PB premium: 3.8 vs 2.7 = +40.7%; 1.3 vs 2.7 = -51.9%. PS premium: 4.7 vs 3.1 = +51.6%. Dividend yield 16/250 = 6.4%. EMA multiplier for n=20 = 0.0952. % above 1M SMA: 30 vs 28 = 7.14%; above 12M SMA: 30 vs 22.7 = 32.2%. Interest coverage 120/50 = 2.4. Quick ratio (250-50)/300 = 0.67. Cash conversion cycle 28+13-32 = 9. Rollover cost 95.45/94.35-1 = 1.2%. Percentage rollover 3,430,000 / (55,083,000+3,430,000+28,000) = 5.9%. Put call ratio 120/100 = 1.2. 1D OI change 120 vs 100 = +20%. OBV for closes 7661.6, 7578.8, 7457.4, 7608.5, 7701.2, 7582.5, 7598.8 with volumes 385730, 676390, 328598, 488766, 321296, 332924 = -385730, -1062120, -733522, -244756, -566052, -233128. Sharpe (42.5% - 5%) / 28% = 1.34. Bank net loans 100000 - 2000 = 98000. Williams %R and Stochastic on hand-computed 14-day windows. Reconcile market cap, close price, volume and F&O OI against the exchange's own published files for 10 stocks.

---

## 13. Documents to create and keep updated

`PROJECT_STATE.md`, `TOOLS.md`, `SCREENSHOT_MAP.md`, `AUDIT.md`, `FILTER_CATALOG.md`, `VISUAL_QA.md`, `DATA_SOURCES.md`, `DATA_AVAILABILITY.md` (filter, status [Official-direct / Computed-from-official / Approximate / Unavailable], source), `METRICS.md` (every formula, unit and assumption), `ASSUMPTIONS.md`, `CHANGELOG.md`, `README.md`.

---

## 14. Customization mode (after tag `replica-v1`)

I will send one customization at a time. For each one:
1. Restate the request in 3 lines and list the files you will touch.
2. Produce a short plan. Do not start coding a change that conflicts with the baseline without telling me.
3. Implement behind a feature flag where practical. Keep the baseline replica behaviour reachable.
4. Run tests and the visual QA loop for affected screens.
5. Update `CHANGELOG.md`, `PROJECT_STATE.md`, docs; commit as `custom-<n>: <title>`.
6. Report: what changed, what was verified, anything I should decide. Then stop.

**Template I will use:**

```
CUSTOMIZATION #<n>: <title>
Change: <what I want, in plain words>
Scope: UI | engine | data | export | other
Acceptance: <how I will know it works>
Do not touch: <anything that must stay as is>
```

---

## 15. Definition of done (replica)

- Every screenshot state is reproduced with zero known deviations (`VISUAL_QA.md`).
- Every filter in section 10 exists in the registry; each works, or carries an honest Unavailable badge with the reason.
- Uploading an Excel list restricts every view, count, filter and export to those stocks.
- Slider, inputs, Low/Mid/High, Remove, Reset all, Save, Export, column picker, sort and infinite scroll all work.
- Every number is traceable (source, as-of date). Golden tests pass.
- One-command start, offline after first sync, no login, nothing locked.
- Git tag `replica-v1`, docs complete, `PROJECT_STATE.md` current.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-09T22:04:21+05:30.

The user's current state is as follows:
Active Document: /home/silicondoc/Documents/Fun Project/TickerTapeScreening/.venv/pyvenv.cfg (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Claude Opus 4.6 (Thinking). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>