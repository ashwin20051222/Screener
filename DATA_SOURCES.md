# DATA_SOURCES.md — every dataset's official origin, verified status, and our access stance

**Project rule (non-negotiable):** data comes ONLY from official publishers — the exchanges
(NSE/BSE), AMFI, SEBI, FBIL, and exchange filing formats (UDiFF/XBRL). We never scrape
aggregators or mirror sites. Where an official publisher denies automated access, we do not
evade; the designed fallback is a **manual import of the official file** into `data/inbox/`.
Anything we cannot obtain is badged **"Not available from official sources"** in the UI —
never estimated or fabricated.

All "verified" notes below were confirmed live on **2026-10-25** from this machine with a
plain HTTP client (desktop UA identifying as ScreenerDesk/0.1, generous per-host rate
limiting, single request at a time). The machine-readable twin of this file lives in
`config/endpoints.yaml`.

---

## 1. Daily prices — exchange bhavcopies (UDiFF format)

### NSE cash market — `nsearchives.nseindia.com`
- **URL pattern:** `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`
- **Status: ✅ OK (verified 2026-10-25, HTTP 200** for trade date 2026-10-23; zip containing a
  34-column UDiFF CSV, 3,730 rows).
- Published after market close; fetched once per exchange day at 06:30 IST next morning
  (walk-back skips weekends/holidays by the file simply being absent).

### NSE F&O — same host
- **URL pattern:** `https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip`
- **Status: ✅ OK (verified 2026-10-25, HTTP 200**; 40,212 rows for 2026-10-23; STF/STO rows
  with expiry, strike, option type).

### BSE cash market — `www.bseindia.com`
- **URL pattern:** `https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_YYYYMMDD_F_0000.CSV`
- **Status: ✅ OK (verified 2026-10-25, HTTP 200**; plain CSV, identical 34-column header,
  ~882 KB for 2026-10-23). BSE's page notes the file "will be made available for download
  after 4.45 p.m." and is "subject to acceptance of Disclaimer".

**UDiFF column contract (both venues, 34 cols):**
`TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1..Rsvd4`

> **Day VWAP note:** the CM bhavcopy has **no VWAP column**. Per the mission spec, VWAP is
> **derived** as `TtlTrfVal / TtlTradgVol` (traded value Rs ÷ traded qty). Traces in
> `ingest/udiff.py`; assumption documented in `ASSUMPTIONS.md`.

**ToS / fairness stance:** neither `nsearchives.nseindia.com` nor `bseindia.com` publishes an
effective `robots.txt` for these paths (requests return HTML error pages / the SPA shell
instead). Both runs are: identified desktop UA, one request at a time, min 4 s per host with
jitter, fetched once per exchange day, cached verbatim to `data/raw/`, displayed locally only
(no redistribution — both exchanges' terms restrict redistribution; personal/authorized
display in a local tool is the intended and compliant use). On **403/429 we stop immediately**
— never loop, never rotate IPs.

## 2. Security masters (weekly)

| Dataset | URL | Status (2026-10-25) | Notes |
|---|---|---|---|
| NSE equity master | `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv` | ✅ OK | header has spaces after commas; columns SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, FACE VALUE, ISIN NUMBER |
| NSE SME master | `https://nsearchives.nseindia.com/content/equities/SME_EQUITY_L.csv` | ✅ OK (verified 2026-11-10) | same columns as `EQUITY_L.csv` with series `SM`; parsed with `is_sme: True` |
| NSE ETF list | `https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv` | ✅ OK | drives the `is_etf` flag + ETF pseudo-sector |
| NSE F&O lot sizes | `https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv` | ✅ OK | drives `fno_eligible` (7.6) |
| NSE index constituents | `https://nsearchives.nseindia.com/content/indices/ind_{slug}list.csv` (mirror `https://www.niftyindices.com/IndexConstituent/ind_{slug}list.csv`) | ✅ OK | verified live: all 9 canonical slugs (`nifty50`, `niftynext50`, `nifty100`, `nifty200`, `nifty500`, `niftymidcap100`, `niftymidcap150`, `niftysmallcap100`, `niftysmallcap250`). Automatic `niftyindices.com` official mirror fallback if `nsearchives` times out |
| **NSE Total Market industry classification** | `https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv` (mirror `https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv`) | ✅ OK (verified 2026-11-10) | **754** official NSE equities with NSE Macro/Industry strings (covering Nifty 500 + Nifty Microcap 250). Mapped via `config/sector_map.yaml` onto the 11 UI sectors; all 22 official NSE industries mapped (`Automobile and Auto Components`, `Metals & Mining`, `Oil Gas & Consumable Fuels`, `Media Entertainment & Publication` -> `Communication Services`, etc.); equities without official classification stay honestly `"Unclassified"` |
| **NSE Bulk Shares & Nifty 50 Index Close (`PR.zip`)** | `https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{ddmmyy}.zip` | ✅ OK (verified 2026-11-10) | Bundles `mcap{ddmmyyyy}.csv` (`Issue Size` = shares outstanding for `3,257+` NSE equities in a single HTTP request, preferred over per-symbol SHP XBRL loops for Market Cap) and `pd{ddmmyyyy}.csv` (`Nifty 50` daily index OHLCV); also accepted via `data/inbox/` |
| BSE scrip master | `https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Industry=&Sector=&Scripcode=&export=CSV` & `https://www.bseindia.com/corporates/List_Scrips.html` | 🚫 **blocked (403 Access Denied)** (re-verified via REA Chromium capture & polite HTTP on `2026-11-10`; same for bulk `/api/quote-equity` which returns `403` on non-browser clients) | by policy we do NOT evade. Fallback 1 (automatic): partial BSE master derived from the BSE bhavcopy itself (ISIN + numeric scrip code + instrument name) + Nifty Total Market CSV for 754 NSE stocks. Fallback 2 (manual): user downloads the official "List of Scrips" CSV export in a browser and drops `ListofScripData*.csv` into `data/inbox/` (also extracts official BSE `Industry` / `Sector Name` if present) |

## 3. Market-cap classification — AMFI (half-yearly, checked weekly)

- **Page:** `https://www.amfiindia.com/otherdata/categorisation-of-stocks`
- **Data file:** the page links the current list as
  `https://portal.amfiindia.com/spages/AverageMarketCapitalization<DDMonYYYY>.xlsx`
  — e.g. **AverageMarketCapitalization30Jun2026.xlsx, status ✅ OK (HTTP 200, 582 KB,
  verified 2026-10-25)**. The ingest job regex-resolves the newest link from the page itself,
  so period filenames are never hardcoded.
- Used for: Large (rank 1–100) / Mid (101–250) / Small (251+) presets, and the AMFI
  classification column. Attribution "AMFI, period ending <date>" accompanies every value.
- FBIL-style note: AMFI publishes this list for free public/industry use; we fetch the file
  whole (one request) rather than hammering it, with attribution in tooltips.

## 4. Benchmark rates — FBIL (manual-entry path by design)

- **Site:** `https://www.fbil.org.in/` — **🚫 no automated path**
  (Angular SPA behind reCAPTCHA; meaningful downloads require an alphanumeric access key.
  Verified 2026-10-25.) FBIL licenses bulk/machine consumption of its benchmarks; individual
  display of the headline rate is public.
- **Our approach:** the user reads the officially published daily value (FBIL 3M Term MIBOR)
  and enters it once — either via a dropped `data/inbox/fbil_mibor.json`
  (`{"as_of": "2026-10-23", "rate_pct": 6.48}`), or the settings path configured in
  `config/settings.yaml::rates`. It is stored with its as-of date and **badged
  "manual entry — official FBIL published rate"** everywhere it is used. If absent, any
  fair-value filter that needs it shows **"Not available from official sources"** — never a
  substituted or stale guess.

## 5. NSE `www.nseindia.com` API surface (session-bootstrapped)

- **Behaviour (verified 2026-10-25):** a plain homepage GET may answer 403, while an API call
  on the same session (cookies from a homepage attempt, desktop UA, `Referer`, and
  `X-Requested-With: XMLHttpRequest`) succeeds — e.g.
  `/api/corporates-corporateActions?index=equities&from_date=&to_date=` → HTTP 200 JSON.
- **Corporate actions** (ex-date, record date, purpose, face value): ✅ working — daily job at
  06:30 IST, window −45/+10 days. This feeds dividend/split/bonus awareness.
- **Verified live 2026-11-10 (all returning HTTP 200 JSON + XBRL links under polite session):**
  - **Bulk & Block deals:** `/api/snapshot-capital-market-largedeal` (`BULK_DEALS_DATA`, `BLOCK_DEALS_DATA`; fields `buySell`, `clientName`, `date`, `qty`, `symbol`, `watp`, `remarks`) — ✅ OK
  - **Insider Trading (SEBI PIT):** `/api/corporates-pit?index=equities&from_date=...&to_date=...` — ✅ OK
  - **Shareholding patterns:** `/api/corporate-share-holdings-master?index=equities&symbol=<SYM>` → returns `xbrl` XML URL on `nsearchives.nseindia.com` (`SHP_*_WEB.xml` with fraction decimals like `0.5044` = `50.44%`, exact contexts `MutualFundsOrUTI_ContextI`, `InstitutionsDomestic_ContextI`, `InstitutionsForeign_ContextI`, `InsuranceCompanies_ContextI`, `ShareholdingOfPromoterAndPromoterGroup_ContextI`, and `NumberOfShareholders`) — ✅ OK
  - **Financial results (Ind-AS XBRL):** `/api/corporates-financial-results?index=equities&symbol=<SYM>&period=Quarterly|Annual` → returns metadata (`consolidated` vs `Non-Consolidated`, `bank` flag) + `xbrl` XML link (`OneD`, `FourD`, `OneI` contexts; monetary items in raw INR divided by `1e7` into Rs Cr) — ✅ OK
- **ETF NAV & TER (AMFI, verified live 2026-11-10):**
  - **Daily NAVs (`NAVAll.txt`):** `https://www.amfiindia.com/spages/NAVAll.txt` → ✅ OK (HTTP 200, 8 semicolon-delimited columns including `Plan;Option;Net Asset Value;Date`)
  - **Total Expense Ratio (TER):** `https://www.amfiindia.com/ter-of-mf-schemes` (interactive web table; official CSV drops `TER_*.csv` ingested automatically via `data/inbox/`)
- Fairness: 1 request / ≥5 s on `www.nseindia.com`, never parallelised, no retries on 403. All endpoints have matching manual `data/inbox/` file patterns (`ingest/inbox.py`).

## 6. Ingest status, resumability & snapshot provenance

- Every fetched file is kept byte-exact under `data/raw/<source>/` with a SHA-256 recorded in
  the `raw_files` table — any number shown in the UI is traceable to a dated official file.
- Long backfill, SHP, and quarterly XBRL jobs checkpoint every item in `ingest_progress` (`job`,
  `item_key`, `status: ok|holiday|skip|fail`, `updated_at`), can be stopped anytime and resumed via
  `make backfill`, `make sync-shp`, `make sync-quarterly`, or `make sync-all`, and surface per-source
  progress + `fin_quarantine` counts via `make status`.
- Every job updates the precomputed DuckDB `screener_snapshot` table (`make snapshot`) so
  `/api/screener/dataset` serves gzipped, ETag-cached rows cleanly in `< 0.5s` while `/api/meta/status`
  surfaces per-source as-of dates in UI tooltips.
- Manual imports via `data/inbox/` are treated as first-class sources with the same
  provenance (`raw_files` rows marked "manual import").

## 7. What we deliberately DON'T do

- No scraping of aggregator/mirror sites (Google Finance, screener.in clones, TickerTape
  itself, etc.). Nothing in this project reads from them.
- No evasion of 403s (no header-rotation, IP pools, or headless browser farms).
- No fetching of FBIL key-protected downloads.
- No silent substitution of another source when the official one is down — the badge appears
  instead.
