# AUDIT.md — Prototype Code Audit vs Reference Screenshots

> Phase 0 deliverable. Systematic gap analysis comparing `screener.html` against the 21 reference screenshots and the build specification (sections 6–8).

---

## Executive Summary

The prototype `screener.html` (130 lines, single-file vanilla HTML/CSS/JS) is an impressive working prototype that captures the basic structure of the screener. However, it relies on client-side shortcuts, hardcoded data, and simplified styling. This audit catalogues every match, deviation, bug, and missing feature.

---

## 1. Visual & Layout Audit

### 1.1 Left Filter Panel

| Element | In Reference Screenshots | In `screener.html` | Status / Gap |
|---------|-------------------------|-------------------|--------------|
| Panel width | ~270–300px fixed | `300px; min-width:300px` | **Match** |
| Panel background | White (`#FFFFFF`) with light border | `var(--p)` (`#f7f8fa`) | **Deviation:** Prototype uses light gray; screenshot uses white with border |
| Top header | "No filters applied" + outlined "Reset all" | Identical text & button | **Match** |
| Stock Universe tabs | `Default` (blue underline) \| `Custom` (gray) | Identical structure | **Match** |
| "+ Create" link | Blue text, top-right of universe section | Exists (`#up`) | **Match** |
| Default Universe checkboxes | Nifty Smallcap 100, Nifty 500, Nifty Midcap 100 | Only 1 generic sample universe checkbox | **Deviation:** Missing standard Indian index universes |
| "Show 2 More" link | Blue link under index checkboxes | Not implemented | **Missing** |
| Sector search box | "Search by sector name" with 🔍 icon | Present (`#sq`), lacks 🔍 icon | **Minor Deviation** |
| Sector checklist | 12 sectors with counts + chevron ∨ per row | Has counts, NO expandable chevrons | **Deviation:** Sub-sector expansion is not built |
| Sub-sector expansion | Each sector row expands to show sub-sectors | Not implemented | **Missing** |
| Numeric filter widgets | Dual-handle slider + inputs + presets | Implemented with HTML range inputs | **Functional match, visual deviation** |
| Slider styling | Thin dark track, white round handles, filled region between | Two overlapping native range inputs, thumb styling basic | **Visual Deviation** |
| Input fields | Two bordered inputs separated by "to" | Implemented (`.ni` class) | **Match** |
| Preset buttons | Smallcap/Midcap/Largecap (MC) or Low/Mid/High | Implemented (`.pb` button group) | **Functional match, styling deviation** |
| "Remove" link | Appears on hover in section header of added filters | Present (`data-rm`), visible only when expanded | **Deviation:** Should appear on hover / for added filters |
| Bottom button | Full-width dark `+ Add Filter` pinned at bottom | Present (`#af`), sticky at bottom | **Match** |

### 1.2 Add Filters Modal

| Element | In Reference Screenshots | In `screener.html` | Status / Gap |
|---------|-------------------------|-------------------|--------------|
| Layout | Anchored right of left panel, overlays results | `left:300px; width:min(660px, ...)` | **Match** |
| Header title | "Add Filters" (bold) | Present (`<b>Add Filters</b>`) | **Match** |
| Subtitle | "Pick from over 200 filters" | "Pick from [N] filters" (dynamic count) | **Minor Deviation** |
| "Custom" button | Outlined button, top-right | Present (`#cb`) | **Match** |
| Search box | "Search for Filters" with 🔍 icon | Present (`#mq`), lacks icon | **Minor Deviation** |
| Category rail order | 14 categories in specific order | 14 categories present, order mostly matches | **Minor Deviation:** "Tickertape Special" vs "Quant Scores" |
| Active category styling | Bold text + `>` chevron on right | Bold text + highlight background, no chevron | **Deviation** |
| Filter checklist | Square checkboxes, scrollable list | Present, scrollable | **Match** |
| Lock icons (🔒) | Present on premium filters (~30+ filters locked) | Not implemented (all show checkboxes) | **Intentional per spec:** nothing locked in our replica |
| "no data" badges | Not in original (original has all data) | Present in prototype (`<span class="tag">no data</span>`) | **Good feature to keep & formalize** |
| "Your Filters" view | Empty state with CTA + "Create Custom Filter" button | Custom filter form replaces modal body | **Deviation:** Should show onboarding card first |
| Footer "Learn more" | 📗 "Learn more about [Category]" (teal) | "Learn more about [Category]" (toggle inline) | **Deviation:** Prototype toggles inline formulas; original links to glossary |
| Footer "Done" button | Dark primary button, bottom right | Present (`#dn`) | **Match** |

### 1.3 Right Results Pane & Table

| Element | In Reference Screenshots | In `screener.html` | Status / Gap |
|---------|-------------------------|-------------------|--------------|
| Screener title | "Stock Screener" (bold) | Present (`<h1>Stock Screener</h1>`) | **Match** |
| Note input | Editable text with placeholder | Present (`#note`) | **Match** |
| Header actions | Edit (✏️), Share (↗️), Save | Edit (`#ed`), Share (`#sh`), Save (`#sa`), plus a `<select>` | **Deviation:** Prototype uses a `<select>` dropdown for saved screens |
| Save button state | Disabled until changes are made | Always enabled | **Deviation** |
| Results count | "Showing **1 - 20** of **5996** results" | "Showing **1 - 15** of **15** results" | **Match** (dynamic) |
| Update timestamp | "last updated at 6:30 AM IST" (ⓘ) | Not present | **Missing** |
| Export button | Outlined with lock icon | Outlined "Export (copy CSV)" | **Deviation:** Clipboard only, no file download |
| Help button | Blue dot / info icon | Question mark `?` button toggling `#hp` | **Minor Deviation** |
| Column picker `⊕` | Sticky far-left header column | Present (`⊕`), opens popup `#cp` | **Match** |
| Default columns | Name, Sub-Sector, Market Cap, PE, 1M Ret, 1D Ret, ROE | Same 6 default metric columns | **Match** |
| Sort indicator | Arrow `↓` / `↑` next to column name | Text arrow appended to header | **Minor Deviation** |
| Number formatting | Indian format (16,39,061.09), 2 decimals | `toLocaleString('en-IN', ...)` | **Match** |
| Return colors | All values dark/neutral in screenshot | Positive green (`.pos`), negative red (`.neg`) | **Deviation:** Original screener doesn't color returns in table |
| Stock row hover | Highlight background | Present (`tr:hover td { background:var(--hv) }`) | **Match** |
| Infinite scroll | Loads 20 rows per page on scroll | Simple scroll listener, loads all 15 rows | **Needs real pagination** |
| Stock detail drawer | Expected on clicking a row | Not implemented | **Missing** |

---

## 2. Functional & Behavioural Audit

### 2.1 Filter Engine
- **AND-combination:** Implemented correctly via `Array.every` in `ok(r)`.
- **Range filtering:** Works for min/max on loaded rows.
- **Null handling:** Implemented — null values are excluded when filter active.
- **Derived metrics:** Derives sector/sub-sector PE/PB/PS premium and dividend yield vs sector from loaded rows via `derive()`. Good baseline!
- **Missing:**
  - Official-data-based benchmarks (market-wide, not just active universe)
  - Configurable benchmark scope (`market` vs `universe`)
  - Tertile preset calculation over full universe non-null values
  - AMFI market cap categorisation (Large: 1–100, Mid: 101–250, Small: 251+)

### 2.2 Custom Filter Builder
- **Expression compiler:** Implemented in `compile()` (lines 99–103). Safe recursive descent parser, tokenizes `[Metric Name]`, numbers, `+ - * / ( )`. No `eval`. **Excellent design!**
- **Constraints:** Enforces 2 to 5 data items.
- **Missing:** Integration with the "Your Filters" category view shown in Screenshot 21.

### 2.3 Data Loading & Universe Management
- **SheetJS integration:** Implemented via CDN script (line 2). Handles `.xlsx`, `.xls`, `.csv` upload via file input (`#fi`).
- **Column auto-detection:** Maps known filter names and aliases (Name, Company, Symbol, Sub-Sector, Sector). Unrecognized numeric columns become "Your Data" filters.
- **Missing:**
  - Security master matching (ISIN, NSE symbol, BSE code, fuzzy name)
  - Match report (matched / ambiguous / unmatched with manual fix dropdowns)
  - Multiple universe selection (union)
  - P&L calculation for sheets with quantity and buy price
  - Template header download/copy

### 2.4 Saved Screens & Sharing
- **localStorage persistence:** Implemented in prototype (`localStorage.getItem('scr')`).
- **Share as JSON:** Copies JSON to clipboard (`#sh`).
- **Export:** Copies CSV to clipboard (`#ex`).
- **Missing:**
  - Real file download for Export (both `.csv` and `.xlsx`)
  - Screen import from JSON file
  - Pre-built screens catalog ("All Screens" page)
  - Proper screen management modal (rename, delete, duplicate)

---

## 3. Bugs Identified in `screener.html`

1. **Slider Range Sync Bug (line 125):** The dual-range slider uses two overlapping `<input type="range">`. When min exceeds max or vice versa, the clamp logic `if(d.k=='min'&&v>+o.value) { v=+o.value; t.value=v }` locks the sliders together, making it difficult to drag them apart.
2. **Missing Close Price in Screenshot 1:** The prototype includes `close_price` in the default `cols` array, but in reference Screenshot 1, Close Price is NOT in the table (it appears in Screenshots 2–4). The default column list should match Screenshot 1.
3. **Number input parsing (line 123):** `f[d.k] = v==='' || isNaN(+v) ? null : +v` doesn't properly handle scientific notation or negative numbers with spaces.
4. **Export CSV Quoting (line 116):** Simple CSV escaping without handling newlines in cell values.
5. **No build step / minified code:** The entire application is 130 lines of minified, single-character-variable code, making maintenance and modular expansion impossible without refactoring.

---

## 4. Refactoring & Modularization Plan (Phase 1 Target)

To transition from the 130-line prototype to a production-grade Vite + React + TypeScript application:

```
apps/web/
├── src/
│   ├── components/
│   │   ├── layout/          # AppShell, TwoPaneLayout
│   │   ├── left-panel/      # FilterPanel, UniverseSection, SectorSection, NumericFilterWidget
│   │   ├── modal/           # AddFiltersModal, CategoryRail, FilterChecklist, YourFiltersOnboarding
│   │   ├── table/           # ScreenerTable, TableHeader, TableRow, ColumnPicker, Pagination
│   │   ├── drawer/          # StockDetailDrawer (shell)
│   │   └── glossary/        # GlossaryModal / "Learn more about" views
│   ├── engine/              # Client-side filtering, sorting, presets (ported from prototype)
│   ├── custom-filter/       # Safe expression compiler (ported and tested)
│   ├── types/               # TypeScript interfaces for filters, stocks, screens
│   ├── hooks/               # useScreenerState, useFilters, useUniverse
│   └── styles/              # CSS variables, typography, reset, dark theme
```

---

## 5. Fix Prompt #1 Baseline Reproduction & Diagnosis Verification (`D1–D8`)

### Baseline State Observed (`2026-11-10`, tag `replica-v1`)
- **`make status`:** `securities.total = 0`, `px_per_source = []`, `fno_as_of = "n/a"`, `amfi_period = "n/a"`, `corp_actions_as_of = "n/a"`, `fbil_as_of = "n/a"`, `recent_jobs = []`.
- **`GET http://127.0.0.1:8787/api/screener/dataset`:** `synced = False`, `row_count = 0`, `universes_count = 0`, `universes = {}`.
- **`make coverage` (`docs/DATA_COVERAGE.md`):** Across all `255` filters in `registry/filters.yaml`, non-null coverage is `0 (0.0%)` over all rows and `0 (0.0%)` over `NIFTY100`.

### Verified Diagnosis Table (`D1–D8`)

| ID | Status | File & Lines | Verified Evidence |
|---|---|---|---|
| **D1** | **Confirmed** | `apps/web/src/App.tsx` (L96–123, L230–255, L766–810); `app/query/db_store.py` (L86–90, L218) | Checkboxes toggle `'default_seed'` / `'nifty_500'` / `'nifty_midcap'` / `'nifty_50'` / `'nifty_100'`; only `'default_seed'` (`INITIAL_SEED_ROWS`) or `'live_duckdb'` exists in `universes`. When selected IDs don't match, `activeRows` (L111) falls back to `universes[0]?.rows`. `data.universes` (`NIFTY100`, etc.) returned by `db_store.py` is never read. |
| **D2** | **Confirmed** *(exact sample is 15 rows)* | `apps/web/src/App.tsx` (L102, L424–427, L899–915, L935–947, L1055); `apps/web/src/data/seed.ts` (L204–309) | `totalMarketCount: 5996` is hardcoded on `default_seed` and displayed at L1055 whenever no numeric/sector filter is active (`INITIAL_SEED_ROWS` actually holds 15 sample rows, 10 of which happen to be large caps). Sector & sub-sector lists/counts read static `SECTORS_CONFIG` constants (e.g., Consumer Discretionary 24, Industrials 37) instead of computing counts dynamically from `activeRows`. |
| **D3** | **Confirmed** | `apps/web/src/App.tsx` (L228–260) | When `/api/screener/dataset` returns `synced: false` / `rows: []` (L233–234) or fails (`catch` L256–258, `// Offline / seed mode: silent no-op`), the app keeps `default_seed` without displaying any sample-mode banner or sync prompt. |
| **D4** | **Confirmed** | `app/query/db_store.py` (L98); `ingest/financials.py` (L72–77) | `db_store.py` computes `mc = close_px * sh_out / 1e7`, while `ref_security.shares_outstanding` is only updated inside `ingest_financial_xbrl_bytes()` (XBRL financials). Neither NSE/BSE masters nor bhavcopies populate `shares_outstanding`, leaving `market_cap = None` until filings/SHP run. |
| **D5** | **Confirmed** | `config/settings.yaml` (L27); `ingest/sources.py` (L53–68) | `backfill_lookback_business_days: 7` limits `run_daily()` to scanning back at most 7+1 days until the latest date is stored (`break`). No multi-month/year historical backfill command exists, keeping returns, 5Y CAGR, 52W high/low, SMAs/EMAs (50/100/200), beta, alpha, and volatility null. |
| **D6** | **Confirmed** | `ingest/sources.py` (L139–164); `Makefile`; `config/settings.yaml` (L23) | `run_quarterly(max_symbols=50)` selects arbitrary `SELECT DISTINCT nse_symbol FROM ref_security ... LIMIT 50` (not Nifty-first), pulls only `max_quarters=2` (3 needed for 6M change) and `max_filings=2` (6 annual + 4 quarterly needed for 5Y CAGRs/TTM), runs only via cron on the 10th of quarter months, and has no `Makefile` target. |
| **D7** | **Confirmed** | `app/query/db_store.py` (L106–107); `apps/web/src/App.tsx` (L238–239) | Both `db_store.py` and `App.tsx` default empty sectors/sub-sectors to `'Industrials'` and `'General'`, masking missing official classification. |
| **D8** | **Confirmed** | `app/query/db_store.py` (L195–216) | Inside the `for s in sec_rows:` loop, `db_store.py` executes per-symbol `compute_ownership_snapshot(con, sym)` + `compute_fundamental_metrics(con, sym, ...)` (`2N+` sequential DuckDB queries per HTTP request) plus full-market `BenchmarkEngine` + `compute_all_quant_scores` recalculation on every request. |

