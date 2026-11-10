# CHANGELOG.md

All notable milestones for **ScreenerDesk** (Indian Stock Screener Replica).

## [Unreleased — Fix Prompt #1]

### Task D — Historical Bhavcopy Backfill & Vectorised Technicals (`2026-11-10`)
- Added `ingest/backfill.py`, `scripts/backfill.py`, and `make backfill DAYS=400` (`DAYS=1300`, `FO_DAYS=10`), resumable via `ingest_progress`, skipping weekends/cached/stored dates, recording `404` holidays, and stopping immediately on `403`/`429`/network reset with `data/inbox/` instructions.
- Rewrote `run_technicals_job` (`ingest/technicals_job.py`) for bulk DataFrame loading, incremental skipping, `NIFTY50` index benchmark preference, and `db.upsert_df` batch writes.
- Added nested bhavcopy archive & post-inbox technicals support (`ingest/inbox.py`) and `px_days` / `"insufficient history"` provenance tooltips (`app/query/db_store.py`, `apps/web/src/App.tsx`).

### Task C — Market Cap Unblock & Resumable Checkpointing (`2026-11-10`)
- Added `ingest_progress` checkpoint table (`app/schema.sql`, `app/db.py`) and enforced `>= 5.0s` NSE throttling + clean HTTP/2 `curl` fallback for `nsearchives.nseindia.com` (`ingest/http.py`).
- Discovered & wired NSE bulk Press Release archive (`PR{ddmmyy}.zip` -> `mcap{ddmmyyyy}.csv` `Issue Size` for 3,257 securities + `pd*.csv` `Nifty 50` daily close) in `ingest/nse.py` and `ingest/inbox.py` (cache-first, zero per-symbol scraping needed for Market Cap).
- Implemented SHP `shares_outstanding` extraction & resumable `sync_shp_batch` (`ingest/ownership.py`, stopping cleanly on `403`/`429`), plus `scripts/sync_shp.py` and `make sync-shp UNIVERSE=nifty100`.
- Surfaced `amfi_avg_mcap_crs` separately as `"AMFI 6-month average market cap"` and dynamic shares provenance in `StockDetailDrawer.tsx`, `App.tsx`, `config/endpoints.yaml`, and `DATA_SOURCES.md`.
- Verified `100.0%` (`100/100`) Market Cap coverage on live Nifty 100 constituents.

### Task B — Truthful UI & Real Index Universes (`2026-11-10`)
- Added `GET /api/universes` and latest-snapshot index membership lookup in `app/query/db_store.py` (with `px_by_isin` price fallback and graceful busy-lock handling).
- Replaced hardcoded `5996`, `default_seed` binding, and static `SECTORS_CONFIG` in `apps/web/src/App.tsx` with dynamic backend universes (`Nifty 50` .. `Nifty Smallcap 250` + `All NSE + BSE listed`), real filtered counts, and dynamic sector/sub-sector counts.
- Added offline sample-mode banner (`15 sample rows`) with disabled `needs sync` index tags when unsynced, and live `as_of` dates in header tooltip when synced.
- Replaced `"Industrials"`/`"General"` empty-sector defaults with `"Unclassified"`, replaced `"awaiting sync"` with specific `feeds`-driven command hints (`AddFiltersModal.tsx`, synced `filters.json`), and added source + as-of tooltips on numeric table cells.
- Captured `fix1_before_seed.png` and `fix1_after_nifty100.png` (`1750 × 925`).

### Task A — Baseline Reproduction, Coverage Tooling & Diagnosis Audit (`2026-11-10`)
- Verified live app serving and baseline DB state (`synced: False`, `row_count: 0`, `universes_count: 0`).
- Added explicit `feeds:` provenance job tags (`amfi`, `daily`, `deals`, `fno`, `history`, `manual`, `shp`, `unavailable`, `weekly`, `xbrl`) across all `255` filters in `registry/filters.yaml`.
- Added `scripts/coverage.py` and `make coverage` target generating per-filter All vs `NIFTY100` coverage reports in `docs/DATA_COVERAGE.md`.
- Confirmed diagnosis items `D1–D8` with exact code locations and evidence in `AUDIT.md` Section 5 and drafted the Tasks B–H implementation plan.

## [replica-v1] — 2026-11-10 (Phases 4 & 5 Complete)

### Added — Phase 5 (Quant Scores, Hardening, Packaging)
- **Quant Scores Engine (`config/scores.yaml`, `app/metrics/scores.py`):** Open-approximation local calculations for all 5 Quant Special scores (`price_momentum_rank`, `earnings_quality_rank`, `price_to_intrinsic_value_rank`, `value_momentum_rank`, `fundamental_score` 1–10 with banking/financial-institution health rules), explicitly labeled `"Approximate - computed locally"`.
- **Database Snapshot & API (`app/query/db_store.py`, `app/api/routes.py`):** Added DuckDB-backed market snapshot loader with field-level source + as-of provenance, plus `/api/scores/weights`, `/api/screener/dataset`, and `/api/scores/compute` endpoints.
- **Full-Stack Serving (`app/main.py`, `Makefile`):** Built React production bundle (`apps/web/dist`) served directly from FastAPI at `/` on `http://127.0.0.1:8787` with status dashboard moved to `/status`; added `make web-build`.
- **UI Polish & Zero Third-Party Branding:** Renamed `"Special"` category to `"Quant Special"`, added honest `"Not available from official sources"` and `"Approximate - computed locally"` pills across modal/drawer, expanded built-in screens to all 8 Section 7 templates in `SavedScreensModal.tsx`, centered Excel Upload / Match Report modal CSS, and added infinite scroll pagination (`visibleLimit` page size 20) with `/api/screener/dataset` hydration.
- **Performance Benchmark (`tests/test_performance.py`):** Verified 6,500-stock scoring + multi-filter query benchmark.

### Added — Phase 4 (Official Data Connectors 4.1–4.7)
- **4.1–4.2 Security Masters, Split/Bonus Adjuster, Reconciliation:** Added NSE SME master (`SME_EQUITY_L.csv`), `ingest/adjuster.py` backward adjustment series (`px_daily_adjusted`), `ingest/master_enrichment.py` (`config/sector_map.yaml`), and `ingest/reconcile.py` 10-stock raw exchange file reconciliation.
- **4.3 F&O Metrics Engine (`ingest/fno_metrics.py`, BSE F&O UDiFF):** Computed all 28 F&O metrics (Basis, Rollover, Calendar Spread, Cash & Carry, PCR, OI/Volume deltas, Highest Call/Put OI & Change strikes) with honest `Unavailable` degradation for `Fair Value` when FBIL MIBOR is absent.
- **4.4 Ownership & Deals (`ingest/ownership.py`):** Shareholding Pattern XBRL parser (with fractional percentage `x 100` normalization), Promoter Pledged %, Bulk/Block Deals, and SEBI PIT Insider Trades.
- **4.5 Ind-AS XBRL Financials (`ingest/xbrl.py`, `ingest/financials.py`):** Consolidated-first with Standalone fallback, INR -> Rs Crores (`/ 1e7`) scaling, 4 sector templates (`industrials`, `utilities`, `banks`, `insurers`), and `fin_quarantine` Assets = Liabilities + Equity validation.
- **4.6 Technical Indicators (`app/metrics/technicals.py`, `ingest/technicals_job.py`):** Completed all 33 indicators (Wilder RSI/ADX, MACD, Bollinger distances, Parabolic SAR, SuperTrend, Stochastic %K/%D, OBV/AD weekly changes, Nifty relative metrics) + EOD DuckDB batch job.
- **4.7 ETFs & Manual Inbox (`ingest/etf.py`, `ingest/inbox.py`):** AMFI 8-column `NAVAll.txt`, TER CSV, 1Y annualized Tracking Error, full `data/inbox/` dispatch rules, and `quarterly_filings` APScheduler cron job.
- **Live Endpoint Verification:** Verified live HTTP schemas against AMFI (`NAVAll.txt`, `TER`), NSE (`SME_EQUITY_L.csv`, `largedeal`, `pit`, `share-holdings` XML, `financial-results` Ind-AS XML) and updated `config/endpoints.yaml` and `DATA_SOURCES.md`.

## [Phase 3] — 2026-11-09 (Excel Universe)
- 5-tier universe matcher cascade (`ISIN -> NSE Symbol -> BSE Code -> Normalized Name -> RapidFuzz`), Excel/CSV sheet importer, Portfolio P&L calculator, ambiguous/unmatched resolution UI, and 30-row golden fixture test suite.

## [Phase 2] — 2026-11-09 (Registry, Metrics & Query Engine)
- Populated all 255 filters in `registry/filters.yaml`, implemented versioned formulas (`app/metrics/`), safe AST custom formula parser (`app/metrics/parser.py`), DuckDB-compatible query engine (`app/query/engine.py`), and passed all 19 Section 12 golden tests.

## [ui-replica-v1] — 2026-11-09 (Phase 1 Faithful UI Replica)
- Archived prototype `screener.html` -> `legacy/screener.html`; scaffolded React + TypeScript UI (`apps/web`), Add Filters modal (14 categories), glossary modal, detail drawer, light/dark themes, real `.csv`/`.xlsx` exports, and verified visual parity against 21 reference screenshots (`VISUAL_QA.md`).

## [baseline-prototype] — 2026-11-09 (Phase 0 Audit & Ingestion Core)
- Audited `screener.html` (`AUDIT.md`, `SCREENSHOT_MAP.md`), inventoried REA tools (`TOOLS.md`), scaffolded DuckDB schema and polite HTTP ingestion core (`ingest/http.py`, `app/db.py`, `app/scheduler.py`).

