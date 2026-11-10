# LIVE_DATA_DIAGNOSIS.md — Current Runtime Coverage & Root-Cause Reproduction

> **Inspected Git Commit:** `a39ca46` (`HEAD -> main, tag: replica-v1.1, origin/main`, fetched cleanly on `2026-11-10T12:27+05:30`)
> **Inspected Environment:** Project `.venv` (Python 3.12), DuckDB `data/screener.db`, FastAPI ASGI router (`app/main.py`), `docs/DATA_COVERAGE.md` (`2026-11-10T11:56:42+05:30`).

---

## 1. Reproduced Database Counts & Watermarks

Direct read-only queries against `data/screener.db` (`2026-11-10`):

| Table | Actual Row Count | Detail / Watermark |
|---|---|---|
| `ref_security` | **2,645** | `shares_populated = 2,644`, `fno_eligible = 0`, `is_etf = 0` |
| `ref_index_constituent` | **1,502** | 9 canonical Nifty indices (`NIFTY100 = 100`, `NIFTY500 = 501`, `as_of = 2026-11-10`) |
| `px_daily` | **2,744** | Single trade date only (`2026-11-09`: `2,743` NSE EQ + `1` `NSE-INDEX` `NIFTY50`) |
| `corp_action` | **0** | Not populated in current DB |
| `tech_daily` | **0** | **0** computed indicator rows |
| `fin_annual` | **17** | Covers only **2 / 100** Nifty 100 symbols (`ABB`, `ADANIENSOL`), plus polluted quarterly rows (see §4.1) |
| `fin_quarterly` | **17** | Covers only **2 / 100** Nifty 100 symbols (`ABB`, `ADANIENSOL`) |
| `fin_quarantine` | **0** | None quarantined |
| `ownership_quarterly` | **6** | Covers only **2 / 100** Nifty 100 symbols (`ABB`, `ADANIENSOL`, 3 quarters each) |
| `bulk_block_deals` | **78** | 1 daily snapshot (`2026-11-09`) |
| `insider_trades` | **0** | API returned empty list for default window |
| `fno_daily` | **0** | No F&O bhavcopies ingested |
| `ref_fno_lot` | **0** | No lot size master ingested |
| `fno_metrics_daily` | **0** | No F&O derived metrics computed |
| `ref_amfi_classification` | **0** | No AMFI classification workbook ingested |
| `etf_meta` / `etf_nav_daily` | **0 / 0** | No AMFI NAV or TER ingested |
| `ref_fbil_mibor` | **0** | Manual `data/inbox/fbil_mibor.json` absent |
| `screener_snapshot` / `_meta` | **2,645 / 1** | Built `2026-11-10 06:26:38Z`, `etag: 03bdf4ae7d7367b5089ea0ca`, watermark: `price=2026-11-09, masters=2026-11-10, filings=2024-12-31, amfi=None, max_px_days=1` |

### Historical Price Distribution across the 100 Nifty 100 Members
- `total = 100`, `min_days = 1`, `max_days = 1`
- `>= 10d`: `0` | `>= 50d`: `0` | `>= 100d`: `0` | `>= 200d`: `0` | `>= 252d`: `0` | `>= 1250d`: `0`

---

## 2. Reproduced Live API Responses

Tested via FastAPI ASGI (`app/main.py`):

| Endpoint | HTTP Status | Observed Payload Summary |
|---|---|---|
| `GET /health` | `200` | `{"ok":true,"app":"ScreenerDesk","note":"offline-first; no login; nothing locked"}` |
| `GET /status` | `200` | HTML renders **broken job labels** (`None — running`) because `app/main.py:150` reads `j.get("kind")` & `j.get("finished_at")` while `sources.status_report()` returns `job`, `on`, `status`, `msg`. |
| `GET /api/universes` | `200` | Returns all 9 indices (`NIFTY50=50` .. `NIFTY100=100` .. `NIFTYSMALLCAP250=251`) + `ALL=2645`. |
| `GET /api/filters` | `200` | All `255` filter definitions loaded (`157,489` bytes). |
| `GET /api/screener/dataset` | `200` | `row_count=2645, total_market_count=2645, synced=True`. `ABB` `pe_ratio = 649.9060` (corrupted due to bug §4.1!). |
| `GET /api/screener/dataset?universe=NIFTY100` | `200` | `row_count=100, total_market_count=2645`. Only `ABB` and `ADANIENSOL` have XBRL/SHP fields populated; remaining 98 symbols have `null`. |
| `GET /api/coverage?universe=NIFTY100` | **`404`** | **Missing endpoint (`{"detail":"Not Found"}`).** |
| `POST /api/data/ensure` | **`404`** | **Missing endpoint.** |
| `GET /api/data/jobs/{job_id}` | **`404`** | **Missing endpoint.** |

---

## 3. Reproduced Per-Family Data Coverage (`docs/DATA_COVERAGE.md`)

Out of 255 filters on Nifty 100 (`100` members):
- `daily` (`3/3`): Close, Daily Volume, VWAP (`100/100` Nifty 100; `2,385/2,645` all listed — remaining ~260 SME/BSE-only rows lack NSE CM 2026-11-09 trade).
- `weekly` (`1/2`): `face_value` (`100/100`), `lot_size` (`0/100` — weekly F&O lots never synced).
- `shp` (`17/17`): Market Cap (`100/100` via PR `mcap`), while all 16 ownership holdings/deltas are populated for ONLY **`2/100`** (`ABB`, `ADANIENSOL`).
- `deals` (`6/6`): Bulk/insider cumulatives report `0.0` for all `2,644` symbols with shares (Note: `0.0` here means zero reported net deals on the `1`-day bulk snapshot / empty PIT, whereas missing SHP quarters are `null`).
- `xbrl` (`97/137` with `>= 1` value): **Only `2/100`** Nifty 100 stocks have values; **`40/137`** XBRL fields (`total_receivables`, `accounts_payable`, `total_long_term_debt`, `capital_expenditures`, `total_cash_dividends_paid`, `dividend_per_share`, `retained_earnings`, etc.) are **`0/2,645` (`0.0%`)** even on synced companies!
- `history` (`0/49`): All returns, SMAs, EMAs, RSI, ADX, MACD, Beta, Alpha, Sharpe = **`0/100` (`0.0%`)**.
- `fno` (`0/24`): All F&O OI/Basis/Rollover/PCR/Strike fields = **`0/100` (`0.0%`)**.
- `amfi` (`0/2`): `expense_ratio`, `tracking_error` = **`0/2,645` (`0.0%`)**.
- `manual` (`0/3`), `unavailable` (`0/12`): Correctly absent / unavailable.

---

## 4. Exact Root Causes Identified in Source Files

### 4.1 Critical XBRL Filing Selection & Period Pollution (`ingest/xbrl.py`, `ingest/financials.py`)
1. **Quarterly filings written into `fin_annual` (`ingest/xbrl.py:368`):** `parse_indas_xbrl` unconditionally emitted an `annual` row for every XBRL file—including `period="Quarterly"` filings! Thus Q1/Q2 `2022` consolidated filings for `ABB` (`EPS=10.64`, 6-month interim) were stored inside `fin_annual`.
2. **`consolidated` sort broke chronological recency (`ingest/financials.py:126`):** `sync_financials_for_symbol` sorted API results ONLY by `consolidated` without sorting by `toDate DESC` / `filingDate DESC`. Because `ABB` switched from consolidated to standalone after Jun 2022, `Quarterly` synced stale `2019`/`2022` Q1–Q2 consolidated quarters instead of `2024` quarters!
3. **`_select_annual_history` picked stale `2022-06-30` consolidated over `2024-12-31` standalone (`ingest/financials.py:190`):** Finding an old consolidated entry caused ABB's `pe_ratio` to compute `close / 10.64 = 649.91` instead of `close / 88.32`.
4. **Missing Ind-AS XBRL Tag Aliases (`ingest/xbrl.py:209-260`):** Inspected `data/raw/nse-xbrl/FIN_ABB_Annual_31-Dec-2024.xml` and `FIN_ADANIENSOL_Annual_31-Mar-2024.xml` directly:
   - Real XML uses `TradeReceivablesCurrent` + `TradeReceivablesNoncurrent` (not `TradeReceivables`)
   - `TradePayablesCurrent` + `TradePayablesNoncurrent` (not `TradePayables`)
   - `BorrowingsNoncurrent` (lowercase `c` — parser had `BorrowingsNonCurrent`)
   - `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` (not `PurchaseOfPropertyPlantAndEquipment`)
   - `DividendsPaidClassifiedAsFinancingActivities` (not `DividendsPaid`)
   - `BankBalanceOtherThanCashAndCashEquivalents` + `CurrentInvestments`, `ReserveExcludingRevaluationReserves`, `IncreaseDecreaseInCashAndCashEquivalents`, `EffectOfExchangeRateChangesOnCashAndCashEquivalents`, working-capital cash flow adjustment tags.
5. **Bounded Test Smoke Run Left 98/100 Nifty 100 Unsynced:** Task E executed `MAX=2` (`ABB`, `ADANIENSOL`), leaving 98 Nifty 100 members empty in `fin_annual`, `fin_quarterly`, and `ownership_quarterly`.

### 4.2 Historical Backfill Pre-UDiFF Cutoff (`ingest/backfill.py`, `ingest/udiff.py`, `ingest/technicals_job.py`)
- `make backfill` was never run (`px_daily` has `1` date).
- Additionally, NSE launched UDiFF (`BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`) on **2024-07-08**. Prior dates (`DAYS=1300` -> 2021–2024) return `404` on the UDiFF URL and would be wrongly marked `holiday` cleanly in `ingest_progress`, whereas verified live legacy official archive `https://nsearchives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip` returns `HTTP 200`!

### 4.3 Unsynced Masters & Live Parsing Mismatches (`ingest/nse.py`, `ingest/amfi.py`, `ingest/etf.py`, `ingest/fno_metrics.py`)
- **`eq_etfseclist.csv` (`ingest/nse.py:173-175`):** Live file uses headers `Symbol,Underlying Asset,SecurityName,...,ISINNumber` while `_parse_etf_master` checked `"NAME"` and `"ISIN"` — falling back to column 1 (`Underlying Asset`) instead of `"SECURITYNAME"`! Plus `sync_etf_master` & `sync_amfi_nav` had not been run (`is_etf = 0`, `etf_nav_daily = 0`).
- **F&O (`fo_mktlots.csv` + `BhavCopy_NSE_FO`):** `sync_fno_lots` & `sync_fo_bhavcopy` + `compute_fno_metrics_for_date` had not been run since DB rebuild (`fno_eligible = 0`, `fno_metrics_daily = 0`), even though live endpoints return `225` lots and `41,392` F&O contracts (`2026-11-09`).
- **AMFI Categorisation (`ingest/amfi.py`):** `resolve_latest_xlsx()` now resolves `AverageMarketCapitalization30Jun2026.xlsx` live, but `sync_categorisation` was not executed cleanly against `data/screener.db` (`ref_amfi_classification = 0`).

### 4.4 Missing On-Demand Filter-Check/Sync UX & Endpoints (`App.tsx`, `AddFiltersModal.tsx`, `NumericFilterWidget.tsx`, `routes.py`)
- Checking a filter in [`AddFiltersModal.tsx`](file:///home/silicondoc/Documents/Fun%20Project/TickerTapeScreening/apps/web/src/components/AddFiltersModal.tsx) (`handleToggleFilter` in [`App.tsx`](file:///home/silicondoc/Documents/Fun%20Project/TickerTapeScreening/apps/web/src/App.tsx#L638)) mutates UI state only — zero API call is made to check/derive/sync missing dependencies.
- `AddFiltersModal` permanently renders static `needs make ...` strings instead of queueing a deduplicated feed job, displaying live progress (`Syncing x/100`), distinguishing `Not applicable` / `Insufficient history` / `Manual source required` / `Unavailable`, and auto-refreshing `liveRows` & slider bounds without removing/re-adding the filter.
- `NumericFilterWidget.tsx:112` displays misleading `"Add a column named ... to your Excel"` even for API-backed official metrics.

### 4.5 Live Market Data Provider Absence & `/status` Template Defect
- No pluggable `MarketDataProvider` / `LiveMarketDataProvider` / optional `GrowwQuoteProvider` interface exists yet (`px_daily` is purely EOD).
- `app/main.py:150` misreads `j.get("kind")` and `j.get("finished_at")` in `/status` HTML output.

