# ScreenerDesk — offline-first Indian stock screener

A local, offline-first Indian stock-screening workbench — original
branding ("ScreenerDesk"), no login, nothing locked/premium — built strictly on
**official data sources**: NSE, BSE, AMFI, FBIL, SEBI/exchange filing formats. Nothing is
scraped from aggregators; anything not publicly available is **badged "Not available from
official sources"** rather than estimated. Quant ranks use transparent local approximations badged
**"Approximate - computed locally"**.

## Quick start

```bash
make install          # creates .venv (python 3.12) + installs Python requirements
make web-build        # builds the React SPA into apps/web/dist/
make sync-weekly      # first-time data pull (masters, 9 index lists + Total Market 754 sectors)
make sync-daily       # pulls yesterday's exchange bhavcopies + corporate actions + PR MCAP shares
make backfill DAYS=400# historical CM bhavcopies + adjusted technicals (resumable; DAYS=1300 for 5Y CAGR)
make sync-shp         # unblock Market Cap (bulk PR MCAP + resumable SHP XBRL; UNIVERSE=nifty100)
make sync-quarterly   # targeted resumable SHP (3Q) + Ind-AS XBRL (6Y/4Q) (UNIVERSE=nifty100)
make sync-deals       # bulk/block deals + 6M SEBI PIT insider disclosures
make sync-all         # end-to-end resumable sync -> snapshot -> docs/DATA_COVERAGE.md
make run              # serves React SPA + fast ETag/GZip API at http://127.0.0.1:8787
```

After the first sync the app runs **fully offline**: price/master data is cached in
`data/raw/<source>/` (byte-exact official files) and loaded into the local DuckDB at
`data/screener.db`. Every value shown carries its **source + as-of date**; no ghosts of
speculation.

> **Strict-offline mode:** set `scheduler.auto_sync: false` in `config/settings.yaml`.
> Then `make sync-*` are the only data paths, run them when you choose.

## Daily operations

| Command | What it does |
|---|---|
| `make sync-all` | resumable full pipeline (`weekly -> daily -> backfill -> shp -> quarterly -> deals -> snapshot -> coverage`, `UNIVERSE=nifty100\|nifty500\|all`) |
| `make sync-daily` | previous published bhavcopies (NSE CM + FO, BSE CM), PR `mcap*.csv` shares, bulk deals, and vectorised technicals |
| `make sync-weekly` | inbox first, equity/SME/ETF masters, F&O lots, 9 index lists, Nifty Total Market 754 industries, AMFI, manual FBIL rate check |
| `make backfill` | resumable historical NSE CM (`DAYS=400\|1300`) + 10D FO bhavcopies + split/bonus adjustment + vectorised technicals |
| `make sync-shp` | Market Cap unblock via bulk PR MCAP + targeted resumable SHP shares extraction |
| `make sync-quarterly` | targeted resumable 3Q SHP + 6Y/4Q Ind-AS XBRL filings ordered by `UNIVERSE`, refreshing `docs/DATA_COVERAGE.md` |
| `make sync-deals` | bulk/block deals + 6 months (`DEAL_DAYS=183`) of SEBI PIT insider disclosures |
| `make snapshot` | precompute full-market benchmarks, Quant Special scores & row JSON into `screener_snapshot` (`< 0.5s` GZip API) |
| `make coverage` | audit per-filter DB coverage & unmapped industries into `docs/DATA_COVERAGE.md` |
| `make synkinbox` | process manual official drops in `data/inbox/` and refresh technicals + snapshot |
| `make status` | print per-source as-of dates, security counts, `fin_quarantine`, and `ingest_progress` resume state |
| `make web-build` | install/build production frontend bundle (`apps/web/dist`) |
| `make test` | offline pytest suite (fixtures only, zero network) |

Official-site blocks? BSE's master API and FBIL download portal deny bots. The designed
answer is the **manual-import inbox** — download the official file in your browser, drop it
in `data/inbox/`. Full route list + rationale in [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Layout

```
registry/     filters.yaml — single source of truth for all 255 filters (with `feeds` tags) across 13 categories
config/       endpoints.yaml, settings.yaml, sector_map.yaml (22 NSE industries), scores.yaml
app/          FastAPI app serving built SPA (/), /status, /health, /api/universes, /api/filters, /api/screener/dataset (snapshot + GZip + ETag), /api/scores/*
              metrics/ (formulas, technicals, benchmarks, custom parser, quant scores)
              query/ (DuckDB bulk loader, screener_snapshot builder/slicer & filter engine), universe/ (Excel upload & 5-tier matcher)
apps/web/     Vite + React 18 + TypeScript SPA (dist/ served directly by FastAPI)
ingest/       http, udiff, nse, bse, amfi, fbil, inbox, adjuster, reconcile, fno_metrics,
              ownership, xbrl, financials, technicals_job, backfill, master_enrichment, etf, sources
scripts/      sync_all.py, sync_daily.py, sync_weekly.py, sync_shp.py, sync_quarterly.py, sync_deals.py,
              backfill.py, sync_inbox.py, build_snapshot.py, coverage.py, db_info.py
docs/         DATA_COVERAGE.md (live per-filter, per-feed, and sector/unmapped audit report)
tests/        offline pytest suite (golden metrics, matcher, XBRL, F&O, ownership, technicals, quant scores, 6,500-stock perf)
data/         raw/<source>/ (official files, traceable), cache/, inbox/, processed/, screener.db (DuckDB)
docs          README, DATA_SOURCES, DATA_AVAILABILITY, METRICS, ASSUMPTIONS, CHANGELOG, CHECKLIST, VISUAL_QA
```

## Product stance

- **Official sources only.** NSE/BSE CM + F&O bhavcopies, NSE masters/SME/index lists, AMFI
  categorisation & NAV/TER, FBIL manual entry, NSE Shareholding & Ind-AS XBRL filings. See `DATA_SOURCES.md`.
- **Provenance on every value.** Raw files cached + sha-256'd; every number carries a source
  tooltip + as-of date in the stock drawer and API dataset; jobs are traceable in `ingest_status`.
- **Benchmarks vs. filters.** All sector medians / percentiles / quant scores are computed
  over the **full listed market** (`benchmark_scope: market`); your Excel stock universe
  governs what's filtered. Sliders bound to your universe; Low/Mid/High presets are
  tertiles (or AMFI's official MC ranks).
- **Local-only.** No login, no telemetry, nothing locked; localhost by default on port
  8787 (`http://127.0.0.1:8787`, diagnostics at `/status`).
- **Personal-use compliance.** We identify our client, rate-limit generously, respect 403s,
  cache rather than re-fetch, and redistribute nothing.

## Roadmap

All build phases (Phases 0–5, [`CHECKLIST.md`](CHECKLIST.md)) and Fix Prompt #1 hardening (`Tasks A–H`) are **complete** and tagged `replica-v1.1`.

## Dev notes

- SQLite-less: **DuckDB** single-file DB; schema in `app/schema.sql`; upserts idempotent.
- Python 3.12 venv at `.venv`; run through `make` to always use it.
- `tests/` never hits the network (fixtures built in); the venv install includes `pytest`.
- The `Images/` folder is user-reference material (not part of the code) and intentionally
  untracked.
