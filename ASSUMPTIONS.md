# ASSUMPTIONS.md — every derived number's rule, disclosed up front

Anything the price files don't directly state is **derived by a stated rule**, dated and
traceable (raw file in `data/raw/`, per-table `*_at` timestamps). This file is the promise of
those rules; it grows in step 3 with the full metrics registry.

## Derived at ingest (step 2)

1. **Day VWAP** — the UDiFF cash-market bhavcopy ships no VWAP column, so
   `wap = TtlTrfVal / TtlTradgVol` (Rs traded value ÷ shares traded). Rows with zero volume
   keep `NULL` (no fraud with a guess).
2. **BSE partial master** — BSE's master API denies automation, so the BSE "master" is derived
   from the BSE bhavcopy rows: `security_id = ISIN if present else "BSE:<FinInstrmId>"`,
   plus instrument name and series. It therefore **knows nothing about face value or shares
   outstanding** — market cap is not computed from it (that needs BSE's headline data;
   handled at step 6 with its proper endpoint or an inbox drop).
3. **Series scopes** — NSE keeps `EQ` only (settings `ingest.series_equity_nse`); BSE keeps an
   equity-ish allowlist (`A B T M MT XT Z P E EA EB EF EG EZ`). Both are tunables, flagged for
   re-review in step 3 when sector/market-cap joins are built.
4. **F&O eligibility** — a security is `fno_eligible` iff it appears in NSE's official
   `fo_mktlots.csv` (the same file also carries the lot size). If it leaves the file, a later
   weekly sync keeps the flag until we explicitly re-derive it (re-derivation is idempotent
   because the flag source is the file).
5. **AMFI classification** — stored as AMFI itself publishes it (ISIN, rank, average market
   cap in Rs Cr, period date). Our Large/Mid/Small presets are AMFI's rank bands
   (Large 1–100, Mid 101–250, Small 251+), applied in step 3/4 — never recomputed from our own
   averages.
6. **Corporate actions window** — fetched −45 / +10 calendar days around today. Purposes are
   stored verbatim (parsed lightly for face value only); no dividend tax or adjustment logic
   until step 3 decides the adjustment policy explicitly.

## Benchmarking & filtering rules (fixed now, per mission)

7. **`benchmark_scope`** — sector medians, percentile ranks and quant scores use the **FULL
   listed market** (all mainline-listed equities from both exchanges). Filtering/sorting
   operates on the **ACTIVE universe** (the user's Excel stock list). Default `market`, switch
   `universe` in `config/settings.yaml::benchmark_scope`.
8. **Tertile presets** — for non-market-cap metrics, Low / Mid / High presets are **tertiles of
   the active universe's non-null values** (`presets.preset_method = tertiles_universe`);
   they can be overridden by a presets override file in step 4.
9. **Market-cap presets** — Large/Mid/Small come from **AMFI ranks only** (`presets.mc_presets_source = amfi`), never from locally computed caps.
10. **Winsorization** — optional 0.5 / 99.5th percentile trim **for slider display bounds
    only**; user inputs are never clamped, and stored data is never altered.
11. **Slider bounds** — taken from the **active universe's** min/max at ingest day (step 4
    wires this in the registry).

## Data never implied

12. Any field not obtainable from an official source is **absent**, and its filter/card shows
    "Not available from official sources". No proxy, no backfill from aggregators, no
    interpolation.
13. Rates: FBIL 3M MIBOR is manual-entry-only, dated by the user's entry; a rate older than
    35 days degrades the badge to "stale manual rate" (warning, still displayed with its date).
    If absent, F&O `fair_value` and `fair_value_spread` report `Unavailable` rather than falling back to a hardcoded risk-free rate.

## Phase 4–5 Ingestion & Quant Architecture

14. **XBRL Scaling & Sign Conventions:** Live verification of NSE Ind-AS XBRL (`INDAS_*.xml`)
    confirmed raw monetary values are reported in single INR (multiples of 10^7 compared to Rs Cr);
    all extracted rupee line items are strictly divided by `10^7` into Rs Crores. Live Shareholding Pattern
    XBRL (`SHP_*.xml`) stores ownership fractions (e.g. `0.5044`), which `ingest/ownership.py` multiplies by `100` to store percentages (`50.44`).
15. **Statement Preference:** Consolidated Ind-AS filings (`NatureOfReportStandaloneConsolidated = Consolidated`) take priority over Standalone filings for identical `(isin, fy_end)`, recording `statement_type_used` in `fin_annual`/`fin_quarterly`.
16. **Banking & Insurance Exclusions:** Companies mapped via `config/sector_map.yaml` to `financial_template: banks | insurers` (plus NBFCs with `is_financial_institution = true`) systematically evaluate `COGS`, `Inventory`, `Current Ratio`, `Quick Ratio`, `Debt to Equity`, and `Cash Conversion Cycle` to `null` (sector-inapplicable) and substitute Net Interest Income Margin + ROA in Fundamental Score health scoring.
17. **AMFI NAVAll Format:** Live check against `portal.amfiindia.com/spages/NAVAll.txt` observed the updated 8-column semicolon format (`Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date`); the parser handles both 8-column and legacy 6-column records.
18. **Split/Bonus Continuity:** Pre-ex-date adjusted OHLC series (`px_daily_adjusted`) applies cumulative backward adjustment factors derived from NSE/BSE split ratios (`N:M`) and bonus ratios (`A:B`) while preserving raw bhavcopy `close` unedited for exact audit reconciliation.
19. **Quant Scores:** All 5 Special Quant Ranks (`price_momentum_rank`, `earnings_quality_rank`, `price_to_intrinsic_value_rank`, `value_momentum_rank`, `fundamental_score`) load transparent parameters from `config/scores.yaml`, compute over `benchmark_scope = market`, and strictly display the `"Approximate - computed locally"` badge.
