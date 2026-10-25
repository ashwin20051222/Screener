# ScreenerDesk — offline-first Indian stock screener (Tickertape-style, own build)

A local, offline-first replica of the Tickertape stock-screening experience — original
branding ("ScreenerDesk"), no login, nothing locked/premium — built strictly on
**official data sources**: NSE, BSE, AMFI, FBIL, SEBI/exchange filing formats. Nothing is
scraped from aggregators; anything not publicly available is **badged "Not available from
official sources"** rather than estimated.

## Quick start

```bash
make install      # creates .venv (python 3.12) + installs requirements
make sync-weekly  # first-time data pull (masters + classifications); needs network ONCE
make sync-daily   # pulls yesterday's exchange bhavcopies + corporate actions
make run          # opens the app at http://127.0.0.1:8787
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
| `make test` | offline pytest suite (no network) |

Official-site blocks? BSE's master API and FBIL download portal deny bots. The designed
answer is the **manual-import inbox** — download the official file in your browser, drop it
in `data/inbox/`. Full route list + rationale in [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Layout

```
config/       endpoints.yaml (verified data endpoints + statuses/ToS), settings.yaml, sector_map.yaml
app/          FastAPI app, DuckDB schema + upsert layer, scheduler (IST), /health + /api/meta/status
ingest/       http (polite, throttled, caches to data/raw), udiff (34-col UDiFF parser),
              nse.py, bse.py, amfi.py, fbil.py, inbox.py, sources.py (daily/weekly orchestrator)
scripts/      sync_daily.py, sync_weekly.py, sync_inbox.py, db_info.py
tests/        offline pytest suite: parser, DB upserts, masters, AMFI, scheduler cron mapping
data/         raw/<source>/ (official files, traceable), cache/, inbox/ (manual imports),
              processed/ (archived inbox files), screener.db (DuckDB)
docs          README, DATA_SOURCES.md, DATA_AVAILABILITY.md, METRICS.md, ASSUMPTIONS.md, CHECKLIST.md
```

## Product stance

- **Official sources only.** NSE/BSE bhavcopies, NSE masters/index lists, AMFI
  categorisation, FBIL manual entry, NSE corporate filings (step 6). See DATA_SOURCES.
- **Provenance on every value.** Raw files cached + sha-256'd; every number carries a source
  tooltip + as-of date; jobs are traceable in `ingest_status`.
- **Benchmarks vs. filters.** All sector medians / percentiles / quant scores are computed
  over the **full listed market** (`benchmark_scope: market`); your Excel stock universe
  (step 5) governs what's filtered. Sliders bound to your universe; Low/Mid/High presets are
  tertiles (or AMFI's official MC ranks).
- **Local-only.** No login, no telemetry, nothing premium; localhost by default on port
  8787.
- **Personal-use compliance.** We identify our client, rate-limit generously, respect 403s,
  cache rather than re-fetch, and redistribute nothing.

## Roadmap

Tracked in [`CHECKLIST.md`](CHECKLIST.md). Currently at **step 2 of 8** (data ingestion
finished; registry/API/frontend steps land next, with stop-gate approvals between steps).

## Dev notes

- SQLite-less: **DuckDB** single-file DB; schema in `app/schema.sql`; upserts idempotent.
- Python 3.12 venv at `.venv`; run through `make` to always use it.
- `tests/` never hits the network (fixtures built in); the venv install includes `pytest`.
- The `Images/` folder is user-reference material (not part of the code) and intentionally
  untracked.
