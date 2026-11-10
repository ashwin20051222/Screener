# ScreenerDesk — offline-first Indian stock screener

A local, offline-first Indian stock-screening workbench — original
branding ("ScreenerDesk"), no login, nothing locked/premium — built strictly on
**official data sources**: NSE, BSE, AMFI, FBIL, SEBI/exchange filing formats. Nothing is
scraped from aggregators; anything not publicly available is **badged "Not available from
official sources"** rather than estimated. Quant ranks use transparent local approximations badged
**"Approximate - computed locally"**.

## Quick start

```bash
make install      # creates .venv (python 3.12) + installs Python requirements
make web-build    # builds the React SPA into apps/web/dist/
make sync-weekly  # first-time data pull (masters + classifications); needs network ONCE
make sync-daily   # pulls yesterday's exchange bhavcopies + corporate actions
make run          # serves both the React SPA and API at http://127.0.0.1:8787
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
| `make sync-daily` | previous published bhavcopies (NSE CM + FO, BSE CM) + corp actions; walks back between holidays automatically |
| `make sync-weekly` | security masters (NSE eq/ETF, F&O lots), index constituents, AMFI market-cap classification, manual FBIL rate check, inbox-processing first |
| `make synkinbox` | only processes manual drops in `data/inbox/` (read its README) |
| `make status` | prints per-source as-of dates, security counts, recent job results |
| `make web-build` | installs/builds production frontend bundle (`apps/web/dist`) |
| `make test` | offline pytest suite (no network) |

Official-site blocks? BSE's master API and FBIL download portal deny bots. The designed
answer is the **manual-import inbox** — download the official file in your browser, drop it
in `data/inbox/`. Full route list + rationale in [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Layout

```
registry/     filters.yaml — single source of truth for all 255 filters across 13 categories + custom formulas
config/       endpoints.yaml, settings.yaml, sector_map.yaml, scores.yaml
app/          FastAPI app serving built SPA (/), /status, /health, /api/filters, /api/screener/*, /api/scores/*
              metrics/ (formulas, technicals, benchmarks, custom parser, quant scores)
              query/ (DuckDB snapshot builder & filter/sort engine), universe/ (Excel upload & 5-tier matcher)
apps/web/     Vite + React 18 + TypeScript SPA (dist/ served directly by FastAPI)
ingest/       http, udiff, nse, bse, amfi, fbil, inbox, adjuster, reconcile, fno_metrics,
              ownership, xbrl, financials, technicals_job, etf, sources
scripts/      sync_daily.py, sync_weekly.py, sync_inbox.py, db_info.py
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

All build phases (Phases 0–5, Steps 1–8 in [`CHECKLIST.md`](CHECKLIST.md)) are **complete** and tagged `replica-v1`.

## Dev notes

- SQLite-less: **DuckDB** single-file DB; schema in `app/schema.sql`; upserts idempotent.
- Python 3.12 venv at `.venv`; run through `make` to always use it.
- `tests/` never hits the network (fixtures built in); the venv install includes `pytest`.
- The `Images/` folder is user-reference material (not part of the code) and intentionally
  untracked.
