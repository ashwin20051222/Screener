# DATA_SYNC_RUNBOOK.md — Operational Guide for ScreenerDesk Data Pipelines

## 1. Architecture & Refresh Cadence Model
ScreenerDesk strictly separates **authoritative EOD/periodic exchange filings** from **optional intraday quote feeds**, and never fabricates missing data:

| Domain | Official Primary Source | Refresh Cadence | CLI / API Trigger |
|---|---|---|---|
| **Security Master, SME, ETFs, F&O Lots, Indices** | NSE CSVs (`EQUITY_L`, `SME_EQUITY_L`, `eq_etfseclist`, `fo_mktlots`, `ind_*list`, AMFI XLSX) | Weekly / Listing Event | `make sync-weekly` or filter check |
| **Daily Prices, Volume, VWAP, PR MCAP & F&O OI/Basis** | NSE UDiFF CM & F&O Bhavcopies + NSE PR ZIP (`PRddmmyy.zip`) | Daily EOD (after ~18:30 IST) | `make sync-daily` |
| **Historical OHLCV + Technical Indicators (5Y)** | NSE UDiFF CM (`>= 2024-07-08`) + Legacy CM (`< 2024-07-08`) | Resumable / Daily incremental | `make backfill DAYS=260` |
| **Fundamentals, Ratios, Growth, Margins, Cash Flow** | NSE Corporate Financial Results Ind-AS XBRL (`corporates-financial-results`) | Quarterly (45–60d post quarter) | `make sync-quarterly UNIVERSE=nifty100` |
| **Shareholding Pattern & 3M/6M Holdings Delta** | NSE SEBI Reg. 31 SHP XBRL | Quarterly (21d post quarter) | `make sync-shp UNIVERSE=nifty100` |
| **Bulk / Block Deals & Insider Trades** | NSE Capital Market Archives & SEBI PIT Disclosures | Daily EOD / Event-driven | `make sync-deals` |
| **ETF Daily NAV & Tracking Error** | AMFI `NAVAll.txt` + NSE ETF Master | Daily NAV / Monthly TER CSV | `make sync-weekly` + `data/inbox/TER_*.csv` |
| **F&O Fair Value Risk-Free Rate** | FBIL Overnight MIBOR CSV (`data/inbox/`) | Daily Manual Drop (6.5% proxy fallback) | `make synkinbox` |
| **Analyst Consensus / Forward Estimates** | Not available in public official feeds | Unavailable (Requires paid vendor) | Marked `Not available from official sources` |

---

## 2. Polite Exchange Access Policy
- Sequential requests ONLY to `www.nseindia.com` and `nsearchives.nseindia.com` (`>= 5.0s` interval per host).
- Immediate stop on HTTP `403` / `429` — never bypass WAF/CAPTCHAs or rotate headers.
- Every long-running job stores resumable symbol/date checkpoints in DuckDB `ingest_progress` and active UI jobs in `data_jobs`.

---

## 3. Running Syncs Cleanly

```bash
# 1. Build frontend & verify tests
make web-build
make test

# 2. Masters + Indices + AMFI + ETF NAV
make sync-weekly

# 3. Daily CM/F&O Bhavcopy + PR Market Cap + Technicals + Snapshot
make sync-daily

# 4. Historical OHLCV backfill (UDiFF + Legacy pre-Jul-2024)
.venv/bin/python -c "from ingest.backfill import backfill_prices; from app import db; c=db.connect(); print(backfill_prices(c, trading_days=260, fo_days=10))"

# 5. Nifty 100 Ind-AS XBRL Financials & SHP (resumable)
make sync-quarterly UNIVERSE=nifty100
make sync-shp UNIVERSE=nifty100

# 6. Rebuild precomputed screener snapshot & regenerate coverage/missing reports
make snapshot
make coverage
```

---

## 4. Manual Official Inbox Drop (`data/inbox/`)
If NSE returns HTTP `403`/`429`, or for monthly AMFI TER / daily FBIL MIBOR:
1. Download the official file in your browser and save into `data/inbox/`:
   - `BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip` (or Legacy `cmDDMMMYYYYbhav.csv.zip`)
   - `BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip`
   - `PRddmmyy.zip` (NSE PR Market Cap + NIFTY50 close)
   - `TER_YYYYMM.csv` (AMFI Monthly Expense Ratio CSV)
   - `FBIL_MIBOR_YYYYMMDD.csv` (FBIL Overnight MIBOR)
   - `INDAS_<SYMBOL>.xml` / `SHP_<SYMBOL>.xml`
2. Run `make synkinbox` or `POST /api/data/rebuild`.

---

## 5. Optional Intraday / Broker Quote Providers
By default ScreenerDesk uses **Official NSE EOD** (`NSEOfficialEODProvider`). Optional providers never activate unless credentials are set in `.env` (git-ignored):
- **NSE Authorized Vendor (`NSELiveVendorProvider`)**: set `NSE_LIVE_VENDOR_NAME`, `NSE_LIVE_VENDOR_BASE_URL`, `NSE_LIVE_VENDOR_API_KEY`, `NSE_LIVE_VENDOR_MODE` (`live` | `delayed_1_3m` | `delayed_15m`).
- **Groww Trade API (`GrowwQuoteProvider`)**: set `GROWW_ACCESS_TOKEN` (personal single-user workstation only).

