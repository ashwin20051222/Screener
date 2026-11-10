# PROJECT_STATE.md — Continuity File

> **Current Phase:** Fix Prompt #1 — **Task F Complete** (`fix-1f`); proceeding to **Task G** (`Official Sector Classification`).
> **Last Updated:** 2026-11-10T11:44:45+05:30
> **Tags:** `baseline-prototype`, `ui-replica-v1`, `replica-v1`.

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

### Phase 4: Official Data Connectors 4.1–4.7 (Complete)
- **4.1–4.2 Security Masters, Split/Bonus Adjuster & Reconciliation:** Added SME master (`SME_EQUITY_L.csv`), `ingest/adjuster.py` backward split/bonus price adjustment (`px_daily_adjusted`), `ingest/master_enrichment.py`, and `ingest/reconcile.py` 10-stock exchange raw-file reconciliation.
- **4.3 F&O Metrics Engine:** Implemented BSE F&O UDiFF (`ingest/bse.py`) + 28 F&O metrics (`ingest/fno_metrics.py`) with honest `Unavailable` fallback for Fair Value when FBIL MIBOR is absent.
- **4.4 Ownership & Deals:** Implemented SHP XBRL parser (`* 100` fractional normalization), Promoter Pledged %, Bulk/Block Deals, and SEBI PIT Insider Trades (`ingest/ownership.py`).
- **4.5 Ind-AS XBRL Financials:** Implemented consolidated-first/standalone-fallback Ind-AS parser (`ingest/xbrl.py`, `ingest/financials.py`) with INR `/ 1e7 -> Rs Cr` scaling, 4 sector templates, and `fin_quarantine` check.
- **4.6 Technical Indicators:** Completed all 33 indicators (`app/metrics/technicals.py`, `ingest/technicals_job.py`).
- **4.7 ETFs, Inbox & Live Endpoint Checks:** Implemented AMFI 8-column `NAVAll.txt` + TER + 1Y tracking error (`ingest/etf.py`), expanded `data/inbox/` dispatch (`ingest/inbox.py`), registered `quarterly_filings` cron (`app/scheduler.py`), and live-verified NSE/AMFI endpoints updating `config/endpoints.yaml` and `DATA_SOURCES.md`.

### Phase 5: Quant Scores, Hardening, Packaging (Complete — `replica-v1`)
- **Quant Scores Engine (`config/scores.yaml`, `app/metrics/scores.py`):** Implemented all 5 Section 11 Quant Special scores (`price_momentum_rank`, `earnings_quality_rank`, `price_to_intrinsic_value_rank`, `value_momentum_rank`, `fundamental_score`) badged `"Approximate - computed locally"`.
- **Database Snapshot & Full-Stack Serving (`app/query/db_store.py`, `app/api/routes.py`, `app/main.py`):** Joined DuckDB tables with provenance; added `/api/scores/weights`, `/api/screener/dataset`, `/api/scores/compute`; built Vite SPA (`apps/web/dist`) served from `/` on `http://127.0.0.1:8787` (`/status` retains diagnostic view).
- **UI Completion & Zero Third-Party Branding:** Renamed `"Special"` -> `"Quant Special"`, added honest `"Not available from official sources"` and `"Approximate - computed locally"` pills, expanded `SavedScreensModal.tsx` to all 8 built-in Section 7 screens, centered modal overlays, and wired infinite scroll (`pageSize = 20`) + backend dataset hydration.
- **6,500-Stock Benchmark (`tests/test_performance.py`):** Verified scoring + multi-filter query throughput across 6,500 synthetic rows.

---

## 2. Next Up

- **Task B (Fix Prompt #1) Complete (`fix-1b`):**
  - Added `GET /api/universes` (`app/api/routes.py`, `app/query/db_store.py`) returning the 9 canonical indices from latest `ref_index_constituent` snapshots + `"All NSE + BSE listed"`, with graceful DuckDB busy-lock fallback and `px_by_isin` fallback.
  - Replaced `"Industrials"` / `"General"` fallbacks with `"Unclassified"` in `db_store.py` and `App.tsx`.
  - Synced `feeds:` into `apps/web/src/data/filters.json`; updated `AddFiltersModal.tsx` to display specific `feeds` missing messages (`needs make sync-quarterly`, `needs make backfill`, `needs make sync-shp`, etc.) and coverage `%` tooltips when populated.
  - Wired real index checkboxes, honest live row & sector/sub-sector counts (removed hardcoded `5996` and `SECTORS_CONFIG`), and added offline sample-mode banner (`App.tsx`).
  - Visually verified `fix1_before_seed.png` (15 sample rows + banner + `needs sync`) and `fix1_after_nifty100.png` (Nifty 100 = exact `100` constituents, banner hidden, unticking returns `2645` all-listed).
- **Task C (Fix Prompt #1) Complete (`fix-1c`):**
  - Discovered official NSE Daily Press Release archive (`PR{ddmmyy}.zip` bundling `mcap{ddmmyyyy}.csv` with exact `Issue Size` shares outstanding for `3,257` NSE securities + `pd{ddmmyyyy}.csv` `Nifty 50` daily close) and added HTTP/2 `curl` transport in `ingest/http.py` (strictly keeping `>= 5s` interval and immediate `403`/`429` stop).
  - Added `ingest_progress(job, item_key, status, message, updated_at)` + `ref_security.shares_source`/`shares_as_of` in `app/schema.sql` & `app/db.py`.
  - Implemented bulk `sync_nse_pr_mcap` + inbox `PR*.zip`/`mcap*.csv` + `niftyindices.com` mirror fallback in `ingest/nse.py`, plus SHP shares extraction & resumable `sync_shp_batch` (`ingest/ownership.py`) + `make sync-shp UNIVERSE=nifty100`.
  - Exposed AMFI 6-month average market cap strictly under its own `amfi_avg_mcap_crs` card in `StockDetailDrawer.tsx` + Market Cap shares provenance tooltips in `App.tsx`.
  - Verified live `make sync-shp UNIVERSE=nifty100`: `2,644 / 2,645` securities have `shares_outstanding`, yielding **`100.0%` (`100/100`) Market Cap coverage on Nifty 100**.
- **Task D (Fix Prompt #1) Complete (`fix-1d`):**
  - Implemented `ingest/backfill.py`, `scripts/backfill.py`, and `make backfill DAYS=400` (`DAYS=1300` for 5Y CAGR, `FO_DAYS=10` for F&O delta history), skipping weekends, stored dates, and raw-cache archives, recording `404` holidays in `ingest_progress`, and aborting cleanly on `403`/`429`/reset with manual `data/inbox/` guidance.
  - Upgraded `ingest/technicals_job.py` (`run_technicals_job`) to bulk DataFrame loading + incremental symbol skip (`MAX(date)` vs `tech_daily` & `corp_action`) + `db.upsert_df` batch writes + `NIFTY50` (`NSE-INDEX`) benchmark support; enforced `None` (`insufficient history`, never `0`) on single-day/short histories.
  - Extended `ingest/inbox.py` for nested bhavcopy archives (`*bhav*.zip`) with automatic checkpoint + post-inbox technicals refresh; exposed `px_days` in `db_store.py` & `"insufficient history"` tooltips in `App.tsx`.
- **Task E (Fix Prompt #1) Complete (`fix-1e`):**
  - Updated `sync_financials_for_symbol` (`ingest/financials.py`) to sort Consolidated before Standalone and target `max_annual=6`, `max_quarterly=4`, checkpointing each filing (`xbrl_filing`) in `ingest_progress` and aborting cleanly on HTTP `403`/`429`.
  - Added `sync_deals_and_pit` (`ingest/ownership.py`), `scripts/sync_deals.py` (`make sync-deals`), and targeted resumable `run_quarterly(universe, max_symbols, resume)` (`ingest/sources.py`) + `scripts/sync_quarterly.py` (`make sync-quarterly UNIVERSE=nifty100|nifty500|all MAX=...`, auto-regenerating `docs/DATA_COVERAGE.md` and exposing `fin_quarantine_count` in `make status`).
  - Surfaced `n/a for this sector` / `n/a (sector)` hints and tooltips for bank/insurer-inapplicable ratios in `StockDetailDrawer.tsx` & `App.tsx`, and rebuilt `apps/web/dist`.
  - Live verified (`make sync-deals` + `make sync-quarterly UNIVERSE=nifty100 MAX=2`): `78` bulk/block deal rows, `ABB` & `ADANIENSOL` SHP (3Q) + Ind-AS XBRL filings synced in `143.33s` (`32` requests, `0` quarantined), populating `17/17` `shp`, `6/6` `deals`, and `126/137` `xbrl` filters (`103 passed`).
- **Task F (Fix Prompt #1) Complete (`fix-1f`):**
  - Added `screener_snapshot` + `screener_snapshot_meta` tables (`app/schema.sql`) and implemented `app/query/snapshot.py` (`build_screener_snapshot`, `load_snapshot_from_db`) + `scripts/build_snapshot.py` (`make snapshot`).
  - Eliminated N+1 DB queries (`D8`) via set-based `compute_all_ownership_snapshots_bulk` (`ingest/ownership.py`) and `compute_all_fundamental_metrics_bulk` (`ingest/financials.py`), sharing pure computation helpers (`_compute_fundamentals_from_rows`, `_ownership_snapshot_from_inputs`) and replacing `.fetchdf()` NaN pollution with clean cursor row dicts.
  - Hooked `build_screener_snapshot` onto completion of `run_daily`, `run_weekly`, `run_quarterly`, `backfill_prices`, `sync_shp_batch`, `sync_deals_and_pit`, and `process_inbox`, plus updated `scripts/coverage.py` to read from snapshot.
  - Added `GZipMiddleware` (`app/main.py`) and upgraded `GET /api/screener/dataset` (`app/api/routes.py`) with `?universe=`, `?fields=`, `ETag`, and `304 Not Modified`.
  - Measured speedup on live `2,645`-stock DB: `39.77s / 4.33 MB` -> **`0.333s` full market (`182 KB` GZipped, `119x` faster)** and **`0.065s` NIFTY100 (`15.1 KB` GZipped)**; offline suite `105 passed`.
- **Next:** Task G — Official all-listed sector/industry classification + expanded `sector_map.yaml`.

---

## 3. Decisions & Assumptions Recorded

1. **Dual Share Classes Ambiguity:** Indian dual-class equity (e.g. Tata Motors Ordinary `TATAMOTORS` vs DVR `TATAMTRDVR`) sharing the same company name is accurately classified as Ambiguous, allowing user selection rather than arbitrary guessing.
2. **Multi-Universe Union:** Users can select any combination of default and custom universes simultaneously; the active universe is the deduplicated union of all matching securities.
3. **P&L Column Auto-Enable:** When a custom universe with Quantity and Buy Price is saved, the screener automatically registers and enables Quantity, Buy Price, and P&L columns in the table picker.
4. **Offline Parity:** Client-side matching in TypeScript provides identical 5-tier matching behavior when operating offline without backend connectivity.

---

## 4. Verification Check

- Full pytest suite: `99 passed` (`.venv/bin/pytest -v tests/`).
- Frontend production build: `npm run build` (`vite build`) passed in `apps/web` (`2089` modules).
- Live FastAPI + SPA server verified on `http://127.0.0.1:8787` (`/`, `/health`, `/status`, `/api/filters`, `/api/scores/weights`, `/api/screener/dataset`).
- Tagged `replica-v1`.
