# CHECKLIST.md — build plan status (8 tracked steps)

- [x] **Step 1 — Data-source discovery**: official endpoints located, verified live
      (2026-10-25), statuses + ToS notes recorded in `config/endpoints.yaml` and
      `DATA_SOURCES.md`. Findings summary delivered to the owner at the end of step 2.
- [x] **Step 2 — Repo skeleton + ingestion core**: FastAPI app shell (`/health`,
      `/api/meta/status`, graceful degraded `/` status page), DuckDB schema (prices, masters,
      classification, actions, status), polite fetcher (respects publisher controls; retried
      timeouts), UDiFF parser, NSE/BSE/AMFI/FBIL/inbox ingest jobs (AMFI now also parses the
      renamed `CATEGORIZATION` header of the 30Jun2026 sheet — 5,427 rows landed), daily +
      weekly schedulers, Makefile, offline test suite (34/34), README + docs.
      2026-10-25 first live sync results: AMFI OK (categorisation page + 30Jun2026 XLSX);
      NSE bhavcopies/masters/corp-actions: network read-timeouts from this box (retries
      exhausted; DNS blip observed) -> per design, manual inbox drop is the fallback;
      BSE: 403 (publisher blocked, stops immediately — never evaded); FBIL: manual JSON
      inbox only.
- [x] **Step 3 — One filter registry + metrics engine**: `registry/filters.yaml` (255 filters),
      `app/metrics/` (`formulas.py`, `technicals.py`, `benchmarks.py`, `parser.py`, `scores.py`)
      with tested golden-number cases (Section 12), including CAGR, returns/premiums, EMA smoothing,
      OBV, Sharpe (`1.34` reference), bank net-loans template, and Section 11 Quant Scores;
      auto-generated glossary + column set (`METRICS.md`).
- [x] **Step 4 — Screener API + query engine**: DuckDB-backed snapshot builder & query engine
      (`app/query/engine.py`, `app/query/db_store.py`, benchmark scope = full market; filtering =
      active universe), presets (tertiles, AMFI MC bands), `/api/screener/dataset`, `/api/scores/*`,
      source + as-of badges on every value.
- [x] **Step 5 — Excel stock-universe upload**: parse user `.xlsx`/`.xls`/`.csv` via 5-tier
      ISIN/NSE/BSE/Normalized-Name/RapidFuzz cascade (`app/universe/matcher.py`), active-universe
      management, Portfolio P&L calculator, 300px-class left filter panel + sliders + presets,
      Add Filters modal, sticky results table with infinite scroll (page size 20) & column picker (`⊕`).
- [x] **Step 6 — Official filings & connectors (Phases 4.1–4.7)**: NSE/BSE CM + F&O UDiFF
      bhavcopy, security masters + SME master, corporate actions + split/bonus price adjuster,
      F&O derived metrics (28 metrics), Ownership XBRL + Bulk/Block + PIT insider trades, Ind-AS
      XBRL financials with 4 sector templates + quarantine integrity check, 33 technical indicators
      EOD job, AMFI ETF NAV + TER + 1Y tracking error, `data/inbox/` fallback handlers, and 10-stock
      exchange reconciliation.
- [x] **Step 7 — Docs + glossary finalization**: `DATA_SOURCES.md` live-verified across all Phase 4
      endpoints (2026-11-10), `DATA_AVAILABILITY.md` honest availability breakdown, final
      `METRICS.md` (with Section 11 weights/formulas), `ASSUMPTIONS.md`, `CHANGELOG.md`,
      `README.md`, and in-app category glossary pages.
- [x] **Step 8 — Golden tests + polish (`replica-v1`)**: Full pytest suite, 6,500-stock performance
      benchmark (`tests/test_performance.py`), Vite SPA built & served on `:8787`, headless visual
      QA verified at `1750 × 925` (`VISUAL_QA.md`), tagged `replica-v1`.

Run every step with `make run` (server) and `make test` (offline suite). Data ops:
`make sync-daily` / `make sync-weekly` / `make synkinbox` / `make status`.
