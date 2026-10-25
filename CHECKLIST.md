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
- [ ] **Step 3 — One filter registry + metrics engine**: `config/metrics_registry.yaml`,
      `app/metrics/` with tested golden-number cases (spec section 8), include CAGR,
      returns/premiums, EMA smoothing, OBV, Sharpe (1.34 reference), bank net-loans template;
      auto-generated glossary + column set.
- [ ] **Step 4 — Screener API + query engine**: DuckDB-backed filter engine (benchmark scope
      = full market; filtering = active universe), presets (tertiles, AMFI MC bands),
      winsorized display bounds, ranking, `/api/screener`, source+as-of badges on every value.
- [ ] **Step 5 — Excel stock-universe upload**: parse user's xlsx (ISIN/symbol/name matching
      chain), fuzzy fallback with threshold from settings, active-universe caching, slider
      bounds from universe, 300px filter-panel + filter cards + Low/Mid/High, add-filter HSE
      modal, results table (sticky header, column picker, 45px rows, 20-page infinite scroll):
      React frontend in step 5-6.
- [ ] **Step 6 — Official filings**: XBRL financials ingestion (quarterly), ownership, bulk
      deals; ingest + badges + balance-sheet/cash-flow filter families per templates (bank
      net loans, insurer).
- [ ] **Step 7 — Docs + glossary finalization**: DATA_SOURCES.md updates after live
      verification of all step-6 endpoints; final METRICS registry table; user guide; in-app
      glossary pages.
- [ ] **Step 8 — Golden tests + polish**: full spec-section-8 test battery green; UX checks
      against the reference screenshots in `Images/`; `make run` end-to-end pass.

Run every step with `make run` (server) and `make test` (offline suite). Data ops:
`make sync-daily` / `make sync-weekly` / `make synkinbox` / `make status`.
