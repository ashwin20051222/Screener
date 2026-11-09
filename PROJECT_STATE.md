# PROJECT_STATE.md — Continuity File

> **Current Phase:** Phase 3 (Excel Universe) complete. Stopped at STOP GATE 3 awaiting user review and approval to proceed to Phase 4.
> **Last Updated:** 2026-11-09T23:40:00+05:30
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
- Enriched all 255 filters in `registry/filters.yaml` with inputs, null rules, direction of goodness, and glossary text.
- Implemented core mathematical formulas in `app/metrics/formulas.py` and technical indicators in `app/metrics/technicals.py`.
- Implemented benchmark calculations in `app/metrics/benchmarks.py` with dual scope (`market` vs `universe`).
- Implemented safe AST custom filter compiler in `app/metrics/parser.py`.
- Implemented query engine (`app/query/engine.py`) with multi-filter AND logic, nulls-last sorting, pagination, and dynamic presets.
- Passed 100% of all 19 Section 12 Golden Tests in `tests/test_golden_metrics.py`.

### Phase 3: Excel Universe (Complete)
- **5-Tier Matcher Cascade (`app/universe/matcher.py` & `app/universe/master.py`):**
  - Tier 1: ISIN 12-character exact match.
  - Tier 2: NSE Symbol exact uppercase match.
  - Tier 3: BSE Code exact numeric match.
  - Tier 4: Exact normalized company name match.
  - Tier 5: Fuzzy name matching using RapidFuzz (`token_set_ratio` with config threshold 88).
  - Categorizes rows into `matched`, `ambiguous` (multiple close candidates), and `unmatched` with zero silent drops.
- **Spreadsheet Importer (`app/universe/importer.py` & `apps/web/src/utils/excelParser.ts`):**
  - Multi-sheet workbook detection and sheet selector (.xlsx, .xls, .csv).
  - Auto-detection of identifier columns and custom user columns (Quantity, Buy Price, Notes, Date).
  - Template headers generator ("Copy template headers").
- **Portfolio P&L Calculator (`app/universe/pnl.py` & `apps/web/src/utils/matcherClient.ts`):**
  - Computes Invested Value, Current Value, Net P&L Amount (Rs), and P&L % from user quantity and buy price.
- **Golden 30-Row End-to-End Test Fixture (`tests/fixtures/universe_30rows.xlsx` & `.csv`):**
  - 25 matched rows across ISIN, symbol, code, and name.
  - 2 ambiguous rows: Tata Motors (Ordinary vs DVR) and L&T (L&T Tech vs L&T Finance).
  - 3 unmatched rows: fictional entity, invalid ISIN, non-existent firm.
  - 100% pass across all 7 test cases in `tests/test_universe_matcher.py`.
- **Frontend Match Report & Universe Management (`apps/web`):**
  - `ExcelUploadModal.tsx`: Drag & drop upload, sheet selector, ID column picker, template helpers.
  - `MatchReportModal.tsx`: Summary metric chips (Matched 25, Ambiguous 2, Unmatched 3), candidate selection dropdown for ambiguous rows, manual resolution for unmatched rows, and Portfolio P&L summary.
  - `UniverseSelector` in left panel: Custom tab with "+ Create", list of custom universes, rename, delete, and multi-universe union selection.
  - Custom user columns (Quantity, Buy Price, P&L Amount, P&L %) integrated into Column Picker (`⊕`) and rendered in table.
- **Visual Verification:**
  - Captured `phase3_upload_modal.png` and `phase3_match_report.png` at 1750x925.

---

## 2. Next Up (Phase 4: Official Data Connectors)

Upon receiving approval at STOP GATE 3:
- **Sub-step 4.1: Security master + daily EOD prices (bhavcopy) + corporate actions:**
  - Write `DATA_SOURCES.md` first (URL, format, ToS/robots note, refresh rate, as discovered with REA).
  - Implement connector with retries, exponential backoff, rate limits, raw-file cache, schema validation, idempotent upsert into DuckDB, and reconciliation check against exchange files for 10 stocks.
  - **STOP and pause at STOP GATE 4.1.**

---

## 3. Decisions & Assumptions Recorded

1. **Dual Share Classes Ambiguity:** Indian dual-class equity (e.g. Tata Motors Ordinary `TATAMOTORS` vs DVR `TATAMTRDVR`) sharing the same company name is accurately classified as Ambiguous, allowing user selection rather than arbitrary guessing.
2. **Multi-Universe Union:** Users can select any combination of default and custom universes simultaneously; the active universe is the deduplicated union of all matching securities.
3. **P&L Column Auto-Enable:** When a custom universe with Quantity and Buy Price is saved, the screener automatically registers and enables Quantity, Buy Price, and P&L columns in the table picker.
4. **Offline Parity:** Client-side matching in TypeScript provides identical 5-tier matching behavior when operating offline without backend connectivity.

---

## 4. Verification Check

- Full pytest suite: 84/84 passed (`.venv/bin/pytest tests/`).
- Frontend build: `npm run build` passed cleanly in `apps/web`.
- Ready for user review at **STOP GATE 3**.
