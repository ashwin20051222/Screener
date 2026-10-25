# METRICS.md — the one filter registry (step 3 scaffolding stub)

The screener has **exactly one canonical list of metrics**: a registry file
(`config/metrics_registry.yaml`, created in step 3). Everything else is generated or
validated against it:

- the UI filter panel (cards, dual sliders, Low/Mid/High presets),
- the API query schema (`/api/screener` step 4),
- the results-table column set (user-toggleable),
- the in-app glossary pages, and
- the pytest suite (every registry entry has an implemented, tested metric module in
  `app/metrics/`).

## Registry entry shape (planned)

```yaml
- id: return_3y_cagr              # stable machine id
  family: returns                 # profitability | valuation | balance_sheet | cash_flow |
                                  # dividends | returns | fno | ownership | quality | etf
  label: "Price CAGR (3Y)"
  short_label: "CAGR 3Y"
  glossary: "Annualised price change over the last 3 calendar years..."
  unit: pct
  direction: higher_is_better     # lower_is_better | neutral
  needs: [px_daily:3y_prices]     # data source + lookback
  computed: app/metrics/returns.py::price_cagr
  slider: {log: false}
  presets: {method: tertiles_universe}
  benchmark_scope: market
  availability: available         # available | manual_input | unavailable;<reason>
  tests: tests/test_metrics_returns.py::test_3y_cagr_golden
```

## Golden-number test plan (from spec section 8, run in step 3)

- 3-year price CAGR on a supplied price series.
- RS / return-premium computations vs. benchmark portfolios.
- *k*-EMA multiplier effects on smoothing; OBV accumulation series; Sharpe ratio ≈
  **1.34** on the reference portfolio series; monotonic-rank preservation.
- Bank "net loans" = loans − NPA provisions as per template 7.12; insurer/income templates
  skip this term cleanly.
- Percentile ranks preserve order and are recomputed only after observation-cut at the run
  cutoff date ("never look forward").

## Families and their current availability posture (detail in DATA_AVAILABILITY.md)

Profitability / balance-sheet / cash-flow → quarterly-only once XBRL filings land (step 6).
Prices, market-cap classification, F&O, ETF flags, corp actions, ownership (deferred) →
per-section badges defined from official-source verification status.

*(This file is a stub until step 3; the definitive table will be generated from the registry
so it can never drift from the code.)*
