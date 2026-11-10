"""Pluggable Market Data Provider abstractions and honest cadence/freshness model."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FreshnessTier(str, Enum):
    LIVE = "Live"
    DELAYED_1_3M = "1-3 min delayed"
    DELAYED_15M = "15 min delayed"
    EOD = "EOD"
    HISTORICAL = "Historical"
    STALE = "Stale"
    UNCONFIGURED = "Unconfigured"


METRIC_CADENCE_MATRIX: Dict[str, Dict[str, Any]] = {
    "price_volume": {
        "label": "Price, Volume & VWAP",
        "default_cadence": "Daily EOD (18:30 IST via NSE CM Bhavcopy; optional intraday vendor/API)",
        "live_capable": True,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["NSE CM UDiFF Bhavcopy", "NSE Authorized Realtime Vendor (optional)", "Groww API (optional)"],
    },
    "market_cap": {
        "label": "Market Capitalization",
        "default_cadence": "Daily EOD (Close x Latest Shares Outstanding)",
        "live_capable": True,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["NSE CM Close + PR MCAP / XBRL / SHP Shares"],
    },
    "technicals": {
        "label": "Returns, Moving Averages, Momentum & Volatility",
        "default_cadence": "Daily EOD (recomputed from historical px_daily)",
        "live_capable": False,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["Locally computed from NSE CM + PR NIFTY 50 history"],
    },
    "fno": {
        "label": "F&O Basis, Rollover, OI & Strikes",
        "default_cadence": "Daily EOD (18:45 IST, F&O eligible symbols only)",
        "live_capable": False,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["NSE F&O UDiFF Bhavcopy", "NSE F&O Market Lots", "FBIL MIBOR (optional)"],
    },
    "etf_nav": {
        "label": "ETF NAV, Tracking Error & Expense Ratio",
        "default_cadence": "Daily NAV (AMFI T+1) / Monthly TER",
        "live_capable": False,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["AMFI NAVAll.txt", "NSE ETF Master", "AMFI Monthly TER CSV"],
    },
    "deals": {
        "label": "Bulk/Block Deals & Insider Trades",
        "default_cadence": "Daily EOD / Corporate Disclosure Event",
        "live_capable": False,
        "default_freshness": FreshnessTier.EOD.value,
        "sources": ["NSE Bulk/Block Deals", "NSE SEBI PIT Disclosures"],
    },
    "xbrl_financials": {
        "label": "Income Statement, Balance Sheet, Cash Flow, Ratios & Growth",
        "default_cadence": "Quarterly (within 45-60d of quarter-end; multiples daily on EOD price)",
        "live_capable": False,
        "default_freshness": FreshnessTier.HISTORICAL.value,
        "sources": ["NSE Corporate Financial Results XBRL (Ind-AS)"],
    },
    "shp_ownership": {
        "label": "Shareholding Pattern & 3M/6M Holdings Change",
        "default_cadence": "Quarterly (within 21d of quarter-end)",
        "live_capable": False,
        "default_freshness": FreshnessTier.HISTORICAL.value,
        "sources": ["NSE Reg. 31 Shareholding Pattern XBRL"],
    },
    "reference_masters": {
        "label": "Security Master, Index Constituents, F&O Lots, AMFI Market-Cap Tier",
        "default_cadence": "Weekly / Semi-Annual (AMFI)",
        "live_capable": False,
        "default_freshness": FreshnessTier.HISTORICAL.value,
        "sources": ["NSE Equity/SME/ETF CSVs", "Nifty Indices CSVs", "AMFI Categorisation XLSX"],
    },
    "consensus_forecasts": {
        "label": "Analyst Ratings & Forward Estimates",
        "default_cadence": "Unavailable without paid consensus license",
        "live_capable": False,
        "default_freshness": FreshnessTier.UNCONFIGURED.value,
        "sources": [],
    },
}


@dataclass
class QuoteRecord:
    symbol: str
    ltp: Optional[float]
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    as_of: Optional[str] = None
    freshness: str = FreshnessTier.EOD.value
    latency_seconds: Optional[int] = None
    provider: str = "nse_official_eod"
    source_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderHealth:
    provider_id: str
    display_name: str
    configured: bool
    enabled: bool
    mode: str
    cadence: str
    status: str  # active | unconfigured | disabled | error | rate_limited | stale
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    detail: str = ""
    authorized_redistribution: str = ""
    supported_capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def classify_eod_freshness(as_of_date: Optional[date], today: Optional[date] = None) -> str:
    """Honest classification of EOD price date without pretending stale/EOD data is real-time."""
    if as_of_date is None:
        return FreshnessTier.STALE.value
    ref = today or date.today()
    age_days = (ref - as_of_date).days
    # Accounts for weekends/holidays up to 4 calendar days cleanly; > 5 days is stale
    if age_days > 5:
        return FreshnessTier.STALE.value
    return FreshnessTier.EOD.value


class MarketDataProvider(ABC):
    provider_id: str = "base"

    @abstractmethod
    def health(self, con=None) -> ProviderHealth:
        """Reports honest readiness, configuration, mode, cadence, and errors."""

    @abstractmethod
    def fetch_quotes(self, symbols: List[str], con=None) -> List[QuoteRecord]:
        """Fetches latest quotes available under this provider cleanly (never fabricates)."""

    def capabilities(self) -> Dict[str, Any]:
        return {"provider_id": self.provider_id}

