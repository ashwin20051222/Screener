# PROJECT_STATE.md — Continuity File

> **Current Phase:** Phase 2 (Registry, Metrics Engine, Query Engine) complete. Stopped at STOP GATE 2 awaiting user review and approval to proceed to Phase 3.
> **Last Updated:** 2026-11-09T23:12:00+05:30
> **Tags:** `baseline-prototype` (at commit 0d3b083), `ui-replica-v1` (at commit eb6772b).

---

## 1. What Has Been Done

### Phase 0: Audit (Complete)
- Created `TOOLS.md` with REA tools and Antigravity tooling inventory.
- Created `SCREENSHOT_MAP.md` mapping all 21 reference screenshots exhaustively.
- Created `AUDIT.md` reviewing prototype `screener.html` against reference.
- Created `registry/filters.yaml` skeleton and `FILTER_CATALOG.md` (255 filters).
- Tagged `baseline-prototype`.

### Phase 1: Faithful UI Replica (Complete)
- Archived `screener.html` to `legacy/screener.html`.
- Scaffolded `apps/web` with Vite, React 18, TypeScript, and CSS variables for theme tokens.
- Built faithful modular frontend components (custom pointer-captured dual slider, accordion numeric filter widgets, 14-category Add Filters modal with canonical Screenshot 21 empty state, stock detail drawer, in-app glossaries, CSV/XLSX export, JSON share).
- Executed visual QA loop across all 21 reference screenshots with zero deviations (`VISUAL_QA.md`).
- Tagged `ui-replica-v1`.

### Phase 2: Registry, Metrics Engine, Query Engine (Complete)
- **Enriched `registry/filters.yaml` (255/255 filters):**
  - Full versioned metadata: inputs, null rules, direction-of-goodness, and original glossary text.
  - Synchronized directly to `apps/web/src/data/filters.json` and documented in `METRICS.md`.
- **Pure Math & Financial Ratios (`app/metrics/formulas.py`):**
  - Profitability (ROE, ROA, ROI, ROCE, Margins), Growth (CAGR, 1Y growth), Valuation (PE, PB, PS, Div Yield, EV, EV multiples, Price/CFO, Price/FCF).
  - Banking ratios (Net Loans = Gross Loans - NPA Provisions).
  - Balance sheet integrity validator (`Assets == Liabilities + Equity`).
- **Technical Indicators (`app/metrics/technicals.py`):**
  - SMA, EMA (with $2/(n+1)$ multiplier and SMA seeding), % above SMA/EMA.
  - RSI 14D (simple & Wilder), ADX, MACD, Bollinger Bands, Parabolic SAR, Williams %R, Stochastic %K/%D.
  - OBV running series with volume accumulation/distribution.
  - 1Y Max Drawdown, Annualized Volatility, Beta & Alpha (104 weekly closes), Sharpe Ratio.
- **Benchmark Engine (`app/metrics/benchmarks.py`):**
  - Group medians, trimmed means, aggregates for sectors and subsectors.
  - Relative multiple premiums vs sector/subsector, dividend yield spread.
  - Configurable `benchmark_scope = market | universe` (default `market`).
- **Safe AST Custom Filter Parser (`app/metrics/parser.py`):**
  - Safe mathematical expression compiler using Python's AST module (no `eval`).
  - Strict whitelist: `+`, `-`, `*`, `/`, `(`, `)`, numeric constants, and registered metric identifiers.
  - Enforces 2 to 5 metric constraints and provides zero-division / NaN safety.
- **Query Engine (`app/query/engine.py` & `app/query/presets.py`):**
  - Multi-filter AND combination across numeric ranges, enum sets, boolean flags, and custom expressions.
  - Deterministic sorting with `NULLS LAST` guarantee for both ascending and descending sorts.
  - Offset/limit pagination (`default_page_size: 20`).
  - Dynamic tertile boundaries (Low/Mid/High) computed on non-null values of the active universe.
  - AMFI Market Cap categorization (Largecap, Midcap, Smallcap).
  - Live sector and subsector stock counts.
- **FastAPI Endpoints (`app/api/routes.py` & `app/main.py`):**
  - `GET /api/filters`: Full registry metadata.
  - `POST /api/query`: Screener query engine endpoint.
  - `POST /api/custom-filter/validate`: Custom filter AST validation endpoint.
- **Golden Tests Suite (`tests/test_golden_metrics.py`):**
  - 100% pass on all 19 Section 12 Golden Tests:
    1. CAGR: 700 to 960 over 5 years = 6.5%.
    2. PE: 300 / 30 = 10.0.
    3. PE premium: 22.0 vs 17.6 = +25.0%; 12.3 vs 17.6 = -30.1%.
    4. PB premium: 3.8 vs 2.7 = +40.7%; 1.3 vs 2.7 = -51.9%.
    5. PS premium: 4.7 vs 3.1 = +51.6%.
    6. Dividend yield: 16 / 250 = 6.4%.
    7. EMA multiplier: n=20 -> 0.0952.
    8. % above 1M SMA: 30 vs 28 = 7.14%; above 12M SMA: 30 vs 22.7 = 32.2%.
    9. Interest coverage: 120 / 50 = 2.4.
    10. Quick ratio: (250 - 50) / 300 = 0.67.
    11. Cash conversion cycle: 28 + 13 - 32 = 9.
    12. Rollover cost: 95.45 / 94.35 - 1 = 1.2%.
    13. Percentage rollover: 3,430,000 / (55,083,000 + 3,430,000 + 28,000) = 5.9%.
    14. Put call ratio: 120 / 100 = 1.2.
    15. 1D OI change: 120 vs 100 = +20.0%.
    16. OBV series test: exact matching vector output `[-385730, -1062120, -733522, -244756, -566052, -233128]`.
    17. Sharpe ratio: (42.5% - 5%) / 28% = 1.34.
    18. Bank net loans: 100000 - 2000 = 98000.
    19. Williams %R (-28.57) and Stochastic %K (71.43) hand-computed tests.
- **Full Test Suite Status:** 75 passed in 1.95s across all test modules.

---

## 2. Next Up (Phase 3: Excel Universe)

Upon receiving approval at STOP GATE 2:
1. Drag-and-drop Excel/CSV upload (.xlsx, .xls, .csv) with multi-sheet selector.
2. Security Master Matcher cascade: ISIN -> NSE symbol -> BSE code -> exact normalized name -> fuzzy name (RapidFuzz threshold 88).
3. Match Report UI: matched / ambiguous / unmatched breakdown with inline correction dropdowns.
4. Multi-Universe Management (Default + Custom union).
5. Optional user custom columns and P&L calculation.
6. 30-row end-to-end test fixture (3 unmatched, 2 ambiguous).
7. Stop at STOP GATE 3.

---

## 3. Decisions & Assumptions Recorded

1. **AST Whitelist Security:** The custom filter compiler forbids all function calls, imports, comprehensions, and attribute accesses (`__class__`, etc.), evaluating bytecode with an empty `__builtins__` dictionary.
2. **Deterministic Nulls-Last:** Custom comparators ensure that `null` / `NaN` values always sort to the bottom of the table whether sorting in ascending or descending direction.
3. **Dual Benchmark Scope:** Supported through `benchmark_scope = market | universe` in both engine configuration and query API requests, defaulting to `market`.
4. **All Golden Tests Passed:** All 19 exact numbers from Prompt Section 12 pass with 100% precision.

---

## 4. Verification Check

- Full pytest suite: 75/75 passed (`.venv/bin/pytest tests/`).
- Frontend build: `npm run build` passed cleanly in `apps/web`.
- Ready for user review at **STOP GATE 2**.
