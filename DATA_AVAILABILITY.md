# DATA_AVAILABILITY.md — what the screener can and cannot display, and where the line comes from

Availability posture per spec 7.x filter families, as of step 2 (2026-10-25). "Badge" is
what a UI filter card shows when its data is not present. Every entry cites the source of
truth; statuses live verbatim in `config/endpoints.yaml`.

## Available (officially, verified live)

| Family / dataset | Source | Since | Usage |
|---|---|---|---|
| Prices (daily OHLC, volume, turnover, derived VWAP) | NSE + BSE UDiFF bhavcopies | ✅ verified | returns, premiums, smoothing-based quant filters, price-vs-benchmark |
| F&O activity (OI, OI change, lots, expiry) | NSE FO bhavcopy + `fo_mktlots.csv` | ✅ verified | family 7.6 F&O filters; `fno_eligible` flag |
| Market-cap classification (Large/Mid/Small) | AMFI half-yearly xlsx (rank 1–100 / 101–250 / 251+) | ✅ verified | mc presets; classification column |
| ETF universe + underlying index | `eq_etfseclist.csv` (official ETF list) | ✅ verified | 7.14 ETF view (beefed up at step 5) |
| Corporate actions (ex/rec dates, purpose, face value) | NSE corporateActions session API | ✅ verified once | dividend/split flags (computed at step 3) |
| Sector/industry tags (mapping layer) | NSE index constituent lists + BSE sector column at step 5 | ✅ verified (4 of the index list slugs) | sector filter family + sector-medians |

## Manual-entry paths (official but not automatable)

| Data | Why manual | Where it lands |
|---|---|---|
| FBIL 3M Term MIBOR (for DCF fair-value filters) | FBIL gates machine access behind an access-key licensing + reCAPTCHA | `data/inbox/fbil_mibor.json`, badge **"manual entry — official FBIL published rate"** |
| BSE scrip master (face value, shares outstanding) | api.bseindia.com returns 403 to automation | user drops official `ListofScripData*.csv` into `data/inbox/`; automatic partial BSE master from bhavcopy as fallback |

## Deferred (official sources exist; endpoints to be wired)

| Family | Source (planned) | Step |
|---|---|---|
| Quarterly / annual financials (P&L, balance sheet, cash flow) | NSE corporate filings XBRL downloads; exchange engine circular formats | 6 |
| Ownership / shareholding pattern | NSE company pages / corporate filing APIs | 6 |
| Bulk & block deals | NSE report-detail pages / API | 6 |

## Not available from official sources (badged, shown as "Not available from official sources")

- Anything not published by NSE/BSE/SEBI/AMFI/FBIL/exchange formats — including "Moneyflow",
  analyst scores, or partner-sourced alternative-data shims (spec explicitly forbids these
  from non-official mirrors).

## Badge rules in UI (step 4+)

- Each value → tooltip line "Source: <OFFICIAL NAME> · As of <date> [+ 'manual entry' tag]".
- Filter card for manual-only data shows its current as-of and a stale-date warning when older
  than ~35 days.
- Missing data never blocks the screener; the metric just lacks values (rows keep count with
  blank cells).
