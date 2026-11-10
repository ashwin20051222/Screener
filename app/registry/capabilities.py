"""Canonical capability & provenance resolver for all 255 screener filters.

Single source of truth combining `registry/filters.yaml` filter definitions with
operational provider metadata (instrument applicability, sector applicability,
primary/backup official sources, DuckDB required tables, calculation function,
lookback requirements, minimum history days, refresh cadence, freshness SLA, and
sync job dependency key).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "filters.yaml"

FILTER_META_FIELDS = (
    "feeds",
    "instrument_types",
    "applicable_sectors",
    "primary_source",
    "backup_source",
    "required_tables",
    "calculation_function",
    "lookback_periods",
    "min_history_days",
    "refresh_cadence",
    "freshness_sla",
    "sync_job",
)

# Exact per-filter lookback / minimum-trading-days rules matching app/metrics/technicals.py & ingest/technicals_job.py
_HISTORY_MIN_DAYS: Dict[str, tuple[str, int]] = {
    "1d_return": ("2 trading days", 2),
    "1w_return": ("6 trading days (~1W)", 6),
    "1w_return_vs_nifty": ("6 trading days vs NIFTY 50", 6),
    "1d_change_in_volume": ("2 trading days", 2),
    "1w_change_in_volume": ("6 trading days (~1W)", 6),
    "1m_average_volume": ("21 trading days (~1M)", 21),
    "3m_average_volume": ("63 trading days (~3M)", 63),
    "1m_return": ("22 trading days (~1M)", 22),
    "1m_return_vs_nifty": ("22 trading days vs NIFTY 50", 22),
    "6m_return": ("127 trading days (~6M)", 127),
    "6m_return_vs_nifty": ("127 trading days vs NIFTY 50", 127),
    "1y_return": ("253 trading days (~1Y)", 253),
    "1y_return_vs_nifty": ("253 trading days vs NIFTY 50", 253),
    "5y_cagr": ("1,261 trading days (~5Y)", 1261),
    "away_from_52w_high": ("Up to 252 trading days (min 2)", 2),
    "away_from_52w_low": ("Up to 252 trading days (min 2)", 2),
    "price_momentum_rank": ("Up to 252 trading days (cross-sectional returns)", 22),
    "1y_max_loss": ("250 trading days (~1Y drawdown)", 2),
    "sma_10d": ("10 trading days", 10),
    "sma_50d": ("50 trading days", 50),
    "sma_100d": ("100 trading days", 100),
    "sma_200d": ("200 trading days", 200),
    "ema_10d": ("10 trading days", 10),
    "ema_50d": ("50 trading days", 50),
    "ema_100d": ("100 trading days", 100),
    "ema_200d": ("200 trading days", 200),
    "price_above_1m_sma": ("21 trading days (~1M)", 21),
    "price_above_12m_sma": ("252 trading days (~12M)", 252),
    "price_above_1m_ema": ("21 trading days (~1M)", 21),
    "rsi_14d": ("15 trading days (Wilder 14d)", 15),
    "rsi_exponential_14d": ("15 trading days (EMA 14d)", 15),
    "adx_rating": ("29 trading days (Wilder ADX 14)", 29),
    "macd_line_1": ("35 trading days (EMA 12/26/9)", 35),
    "macd_line_2": ("35 trading days (EMA 12/26/9)", 35),
    "from_upper_bollinger_band": ("20 trading days (SMA20 +/- 2*SD)", 20),
    "from_lower_bollinger_band": ("20 trading days (SMA20 +/- 2*SD)", 20),
    "from_parabolic_sar": ("5 trading days (PSAR)", 5),
    "williams_r": ("14 trading days", 14),
    "stochastic_k": ("14 trading days", 14),
    "stochastic_d": ("16 trading days", 16),
    "1w_change_in_obv": ("7 trading days", 7),
    "1w_change_in_ad_line": ("6 trading days", 6),
    "super_trend": ("12 trading days (ATR 10)", 12),
    "relative_volume": ("91 trading days (today vs 90d avg)", 91),
    "volatility": ("201 trading days", 201),
    "volatility_vs_nifty": ("201 trading days vs NIFTY 50", 201),
    "beta": ("105 weekly closes (~2Y) vs NIFTY 50", 525),
    "alpha": ("105 weekly closes (~2Y) vs NIFTY 50", 525),
    "sharpe_ratio": ("201 trading days + FBIL MIBOR/6.5% benchmark", 201),
}

_FINANCIAL_ONLY_FILTERS = frozenset({
    "net_loans",
    "total_deposits",
    "policy_liabilities",
    "interest_income",
    "total_interest_expense",
    "loan_loss_provision",
    "net_interest_income",
})

_NON_FINANCIAL_ONLY_FILTERS = frozenset({
    "cost_of_goods_sold",
    "raw_materials",
    "power_fuel_cost",
    "current_ratio",
    "quick_ratio",
    "debt_to_equity",
    "long_term_debt_to_equity",
    "working_capital_turnover_ratio",
    "inventory_turnover_ratio",
    "days_of_inventory_outstanding",
    "days_of_sales_outstanding",
    "days_payable_outstanding",
    "cash_conversion_cycle",
})

_QUARTERLY_FILTERS = frozenset({
    "total_revenue_q",
    "net_income_q",
    "eps_q",
    "operating_and_other_expenses_q",
    "ebitda_q",
    "pbit_q",
    "pbt_q",
    "ttm_pe_ratio",
})


def resolve_filter_capabilities(fid: str, fdef: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministically resolves complete operational metadata for one filter definition."""
    cur_feed = str(fdef.get("feeds") or "unavailable").strip().lower()
    category = str(fdef.get("category") or "")

    # Normalize market_cap feed from historical `shp` label to `daily` because MCAP depends on EOD close + PR/XBRL/SHP shares
    if fid == "market_cap":
        cur_feed = "daily"

    applicable_sectors = "all"
    if fid in _FINANCIAL_ONLY_FILTERS:
        applicable_sectors = "financial_only"
    elif fid in _NON_FINANCIAL_ONLY_FILTERS:
        applicable_sectors = "non_financial_only"

    if fid == "market_cap":
        return {
            "feeds": "daily",
            "instrument_types": ["equity"],
            "applicable_sectors": "all",
            "primary_source": "NSE Equity Bhavcopy (Close) + NSE PR MCAP / XBRL / SHP Shares",
            "backup_source": "Optional NSE Authorized Realtime Vendor / Groww API + Corporate Filings",
            "required_tables": ["px_daily", "ref_security"],
            "calculation_function": "app.query.db_store.load_market_dataset_from_db (close * shares_outstanding / 1e7)",
            "lookback_periods": "1 trading day + latest shares_outstanding",
            "min_history_days": 1,
            "refresh_cadence": "Daily EOD (18:30 IST; optional intraday when vendor configured)",
            "freshness_sla": "EOD T+0 18:30 IST",
            "sync_job": "daily_bhav",
        }

    if cur_feed == "daily":
        return {
            "feeds": "daily",
            "instrument_types": ["equity", "etf"],
            "applicable_sectors": "all",
            "primary_source": "NSE CM UDiFF & Legacy Equity Bhavcopy (NSE Archives)",
            "backup_source": "Optional NSE Authorized Realtime Vendor / Groww API (if configured)",
            "required_tables": ["px_daily"],
            "calculation_function": "ingest.udiff.parse_udiff / ingest.nse.cm_bhav_from_bytes",
            "lookback_periods": "1 trading day",
            "min_history_days": 1,
            "refresh_cadence": "Daily EOD (18:30 IST; optional intraday when vendor configured)",
            "freshness_sla": "EOD T+0 18:30 IST",
            "sync_job": "daily_bhav",
        }

    if cur_feed == "weekly":
        if fid == "lot_size":
            return {
                "feeds": "weekly",
                "instrument_types": ["fno_equity"],
                "applicable_sectors": "all",
                "primary_source": "NSE F&O Permitted Lot Size CSV (fo_mktlots.csv)",
                "backup_source": "NSE F&O UDiFF Bhavcopy NewBrdLotQty",
                "required_tables": ["ref_fno_lot", "ref_security"],
                "calculation_function": "ingest.nse.sync_fno_lots",
                "lookback_periods": "Current weekly expiry snapshot",
                "min_history_days": 0,
                "refresh_cadence": "Weekly / Lot Revision Event",
                "freshness_sla": "Weekly <= 7 days",
                "sync_job": "weekly_master",
            }
        return {
            "feeds": "weekly",
            "instrument_types": ["equity"],
            "applicable_sectors": "all",
            "primary_source": "NSE Securities Master CSV (EQUITY_L.csv / SME_EQUITY_L.csv)",
            "backup_source": "NSE PR Market Cap CSV / Ind-AS XBRL",
            "required_tables": ["ref_security"],
            "calculation_function": "ingest.nse.sync_equity_master",
            "lookback_periods": "Master reference snapshot",
            "min_history_days": 0,
            "refresh_cadence": "Weekly / Listing Event",
            "freshness_sla": "Weekly <= 7 days",
            "sync_job": "weekly_master",
        }

    if cur_feed == "history":
        lookback, min_days = _HISTORY_MIN_DAYS.get(fid, ("252 trading days", 252))
        if fid == "price_momentum_rank":
            calc_fn = "app.metrics.scores.compute_all_quant_scores"
        else:
            calc_fn = "ingest.technicals_job.compute_technicals_for_symbol / app.metrics.technicals"
        req_tables = ["px_daily", "tech_daily"] if fid != "price_momentum_rank" else ["px_daily", "tech_daily", "quant_scores"]
        return {
            "feeds": "history",
            "instrument_types": ["equity", "etf"],
            "applicable_sectors": "all",
            "primary_source": "NSE Historical CM Bhavcopy (UDiFF >= 2024-07-08, Legacy CM < 2024-07-08) + PR NIFTY 50",
            "backup_source": "Local technical indicator engine from cached raw bhavcopies",
            "required_tables": req_tables,
            "calculation_function": calc_fn,
            "lookback_periods": lookback,
            "min_history_days": min_days,
            "refresh_cadence": "Daily EOD (recomputed after CM bhavcopy ingest)",
            "freshness_sla": "EOD T+0 18:45 IST (subject to trading history depth)",
            "sync_job": "technicals" if min_days <= 1 else "history_backfill",
        }

    if cur_feed == "xbrl":
        if category == "Special":
            return {
                "feeds": "xbrl",
                "instrument_types": ["equity"],
                "applicable_sectors": "all",
                "primary_source": "NSE Corporate Financial Results XBRL + Daily EOD Price (Local Quant Model)",
                "backup_source": "BSE Corporate Filings XBRL / Manual data/inbox XBRL",
                "required_tables": ["fin_annual", "px_daily", "quant_scores"],
                "calculation_function": "app.metrics.scores.compute_all_quant_scores",
                "lookback_periods": "Latest FY annual + daily EOD price",
                "min_history_days": 1,
                "refresh_cadence": "Daily EOD (valuation leg) & Quarterly (fundamentals leg)",
                "freshness_sla": "Quarterly filings + EOD price",
                "sync_job": "xbrl_financials",
            }
        if fid.startswith("5y_") or "5y_historical" in fid:
            lookback = "6 fiscal years (FY0 to FY-5)"
        elif fid == "3y_historical_dividend_growth":
            lookback = "4 fiscal years (FY0 to FY-3)"
        elif fid.startswith("1y_hist") or fid in {"return_on_equity", "return_on_assets", "return_on_investment", "asset_turnover_ratio", "working_capital_turnover_ratio", "inventory_turnover_ratio", "days_of_inventory_outstanding", "days_of_sales_outstanding", "days_payable_outstanding", "cash_conversion_cycle"}:
            lookback = "2 fiscal years (FY0, FY-1)"
        elif fid in _QUARTERLY_FILTERS:
            lookback = "4 quarters (TTM)" if fid == "ttm_pe_ratio" else "Latest quarter (Q0)"
        else:
            lookback = "Latest fiscal year (FY0)"

        if "sector" in fid or "sub_sector" in fid:
            calc_fn = "app.metrics.benchmarks.BenchmarkEngine.enrich_stock_with_benchmarks"
        elif fid in _QUARTERLY_FILTERS:
            calc_fn = "ingest.xbrl.parse_indas_xbrl + ingest.financials._compute_fundamentals_from_rows"
        else:
            calc_fn = "ingest.xbrl.parse_indas_xbrl + ingest.financials._compute_fundamentals_from_rows"

        req_tables = ["fin_quarterly"] if (fid in _QUARTERLY_FILTERS and fid != "ttm_pe_ratio") else ["fin_annual", "fin_quarterly"]
        if category == "Valuation":
            req_tables = list(dict.fromkeys([*req_tables, "px_daily", "ref_security"]))

        return {
            "feeds": "xbrl",
            "instrument_types": ["equity"],
            "applicable_sectors": applicable_sectors,
            "primary_source": "NSE Corporate Financial Results XBRL (Ind-AS Consolidated/Standalone)",
            "backup_source": "BSE Corporate Filings XBRL / Manual XML in data/inbox/",
            "required_tables": req_tables,
            "calculation_function": calc_fn,
            "lookback_periods": lookback,
            "min_history_days": 0,
            "refresh_cadence": "Quarterly (within 45-60d of quarter-end; valuation ratios daily on EOD price)",
            "freshness_sla": "Quarterly filings + Daily EOD price for multiples",
            "sync_job": "xbrl_financials",
        }

    if cur_feed == "shp":
        is_delta = "change" in fid
        return {
            "feeds": "shp",
            "instrument_types": ["equity"],
            "applicable_sectors": "all",
            "primary_source": "NSE Corporate Shareholding Pattern XBRL (Reg. 31 SEBI LODR)",
            "backup_source": "Manual SHP XBRL XML in data/inbox/",
            "required_tables": ["ownership_quarterly"],
            "calculation_function": "ingest.ownership.parse_shp_xbrl + compute_all_ownership_snapshots_bulk",
            "lookback_periods": "3 quarters (Q0, Q-1, Q-2)" if is_delta else "Latest quarter (Q0)",
            "min_history_days": 0,
            "refresh_cadence": "Quarterly (within 21 days of quarter-end)",
            "freshness_sla": "Quarterly <= 30 days after quarter-end",
            "sync_job": "shp_ownership",
        }

    if cur_feed == "deals":
        is_insider = fid.startswith("insider_")
        return {
            "feeds": "deals",
            "instrument_types": ["equity"],
            "applicable_sectors": "all",
            "primary_source": (
                "NSE Insider Trading Disclosures (SEBI PIT Reg. 7(2))"
                if is_insider
                else "NSE Bulk & Block Deals Daily Archives"
            ),
            "backup_source": "NSE Corporate Announcements / Manual CSV in data/inbox/",
            "required_tables": ["insider_trades"] if is_insider else ["bulk_block_deals"],
            "calculation_function": "ingest.ownership.sync_insider_trades / sync_bulk_block_deals",
            "lookback_periods": "1M / 3M / 6M rolling calendar window",
            "min_history_days": 0,
            "refresh_cadence": "Daily EOD / Event-driven",
            "freshness_sla": "EOD T+1",
            "sync_job": "deals_insider",
        }

    if cur_feed == "fno":
        lookback = "5 consecutive futures sessions / 1W OI history" if ("rollover" in fid or "1w_" in fid) else (
            "2 consecutive F&O sessions" if "1d_" in fid else "Current trading session (Near & Next expiry)"
        )
        min_d = 5 if "rollover" in fid else (6 if "1w_" in fid else (2 if "1d_" in fid else 1))
        return {
            "feeds": "fno",
            "instrument_types": ["fno_equity"],
            "applicable_sectors": "all",
            "primary_source": "NSE F&O UDiFF Bhavcopy (BhavCopy_NSE_FO_*) + CM Underlying Close",
            "backup_source": "NSE F&O Market Lots Master CSV",
            "required_tables": ["fno_daily", "fno_metrics_daily", "px_daily"],
            "calculation_function": "ingest.fno_metrics.compute_fno_metrics_for_date",
            "lookback_periods": lookback,
            "min_history_days": min_d,
            "refresh_cadence": "Daily EOD (18:45 IST, F&O eligible symbols only)",
            "freshness_sla": "EOD T+0 18:45 IST",
            "sync_job": "fno_daily",
        }

    if cur_feed == "manual":
        return {
            "feeds": "manual",
            "instrument_types": ["fno_equity"],
            "applicable_sectors": "all",
            "primary_source": "NSE F&O UDiFF Bhavcopy + FBIL Overnight MIBOR (manual CSV or 6.5% RBI fallback)",
            "backup_source": "FBIL Daily Overnight MIBOR CSV via data/inbox/",
            "required_tables": ["fno_daily", "fno_metrics_daily", "ref_fbil_mibor", "px_daily"],
            "calculation_function": "ingest.fno_metrics.compute_fno_metrics_for_date",
            "lookback_periods": "Current expiry + MIBOR rate",
            "min_history_days": 1,
            "refresh_cadence": "Daily EOD / Manual FBIL MIBOR drop in data/inbox/",
            "freshness_sla": "EOD + FBIL rate date",
            "sync_job": "manual_mibor",
        }

    if cur_feed == "amfi":
        if fid == "tracking_error":
            return {
                "feeds": "amfi",
                "instrument_types": ["etf"],
                "applicable_sectors": "all",
                "primary_source": "AMFI Daily NAV (NAVAll.txt / portal.amfiindia.com) + NSE Index Close",
                "backup_source": "NSE ETF Master + Manual NAV history drop in data/inbox/",
                "required_tables": ["etf_meta", "etf_nav_daily", "px_daily"],
                "calculation_function": "ingest.etf.compute_tracking_error",
                "lookback_periods": "Min 30 matched daily NAV & benchmark return observations",
                "min_history_days": 30,
                "refresh_cadence": "Daily (after AMFI EOD NAV publication)",
                "freshness_sla": "EOD T+1 (requires >= 30d history)",
                "sync_job": "amfi_etf",
            }
        return {
            "feeds": "amfi",
            "instrument_types": ["etf"],
            "applicable_sectors": "all",
            "primary_source": "AMFI Monthly Scheme TER Disclosure CSV (manual or AMFI Portal)",
            "backup_source": "Manual AMFI TER CSV in data/inbox/ (TER_*.csv)",
            "required_tables": ["etf_meta"],
            "calculation_function": "ingest.etf.ingest_ter_csv_bytes",
            "lookback_periods": "Latest monthly TER filing",
            "min_history_days": 0,
            "refresh_cadence": "Monthly (via AMFI TER CSV)",
            "freshness_sla": "Monthly <= 35 days",
            "sync_job": "amfi_etf",
        }

    # Unavailability / Consensus / Sell-side Forecasts
    return {
        "feeds": "unavailable",
        "instrument_types": ["equity"],
        "applicable_sectors": "all",
        "primary_source": "No official public source (Requires Licensed Consensus Vendor e.g. Refinitiv/Bloomberg/FactSet)",
        "backup_source": "None",
        "required_tables": [],
        "calculation_function": "None (not fabricated)",
        "lookback_periods": "N/A",
        "min_history_days": 0,
        "refresh_cadence": "Unavailable",
        "freshness_sla": "Unavailable (paid institutional consensus license required)",
        "sync_job": "unavailable",
    }


@lru_cache(maxsize=1)
def load_registry_filters() -> Dict[str, Dict[str, Any]]:
    """Loads registry/filters.yaml and merges resolved capability fields cleanly."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    raw: Dict[str, Dict[str, Any]] = doc.get("filters") or {}
    out: Dict[str, Dict[str, Any]] = {}
    for fid, fdef in raw.items():
        merged = dict(fdef)
        caps = resolve_filter_capabilities(fid, merged)
        for k, v in caps.items():
            # Keep YAML overrides if already explicitly present, except ensure consistency for resolved canonical fields
            if k not in merged or merged[k] in (None, "") or k in (
                "feeds",
                "instrument_types",
                "applicable_sectors",
                "primary_source",
                "backup_source",
                "required_tables",
                "calculation_function",
                "lookback_periods",
                "min_history_days",
                "refresh_cadence",
                "freshness_sla",
                "sync_job",
            ):
                merged[k] = v
        out[fid] = merged
    return out

