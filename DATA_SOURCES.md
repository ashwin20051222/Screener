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
| NSE SME master | `https://nsearchives.nseindia.com/content/equities/SME_EQUITY_L.csv` | ⏳ pending | same host/pattern; verified at first weekly run; SME screening flagged `is_sme` when wired (step 3+) |
| NSE ETF list | `https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv` | ✅ OK | drives the `is_etf` flag + ETF pseudo-sector |
| NSE F&O lot sizes | `https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv` | ✅ OK | drives `fno_eligible` (7.6) |
| NSE index constituents | `https://nsearchives.nseindia.com/content/indices/ind_{slug}list.csv` | ✅ OK | verified live: `ind_nifty50list.csv`, `ind_nifty500list.csv`, `ind_niftymidcap100list.csv`, `ind_niftysmallcap100list.csv`. The underscore variant (`ind_nifty50_list.csv`) is **404** — always the no-underscore form. Needed slugs: nifty50, niftynext50, nifty100, nifty200, nifty500, niftymidcap100, niftymidcap150, niftysmallcap100, niftysmallcap250 |
| BSE scrip master | `https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Industry=&Sector=&Scripcode=&export=CSV` | 🚫 **blocked (403 Access Denied)** even with browser referer | by policy we do NOT evade. Fallback 1 (automatic): partial BSE master derived from the BSE bhavcopy itself (ISIN + numeric scrip code + instrument name). Fallback 2 (manual): user downloads the official "List of Scrips" CSV export in a browser and drops `ListofScripData*.csv` into `data/inbox/` |

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
- **Deferred to step 7** (verified URLs to be discovered then; endpoints table kept in
  `endpoints.yaml` with `TBD-at-step7` paths):
  - bulk/block deals (`report-detail/display-bulk-and-block-deals` page family)
  - shareholding pattern (quarterly ownership)
  - financial results / XBRL filings (`companies-listing/corporate-filings`)
- Fairness: 1 request / ≥5 s on this host, never parallelised, no retries on 403.

## 6. Ingest status + provenance

- Every fetched file is kept byte-exact under `data/raw/<source>/` with a SHA-256 recorded in
  the `raw_files` table — any number shown in the UI is traceable to a dated official file.
- Every job writes a row to `ingest_status` (`ok|skip|fail|partial`); `/api/meta/status`
  exposes per-source as-of dates, which is what every value tooltip greys out with.
- Manual imports via `data/inbox/` are treated as first-class sources with the same
  provenance (`raw_files` rows marked "manual import").

## 7. What we deliberately DON'T do

- No scraping of aggregator/mirror sites (Google Finance, screener.in clones, TickerTape
  itself, etc.). Nothing in this project reads from them.
- No evasion of 403s (no header-rotation, IP pools, or headless browser farms).
- No fetching of FBIL key-protected downloads.
- No silent substitution of another source when the official one is down — the badge appears
  instead.
