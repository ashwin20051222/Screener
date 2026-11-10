"""Provider registry & honest runtime price/freshness resolver."""
from __future__ import annotations

from typing import Any, Dict, List

from app.providers.base import METRIC_CADENCE_MATRIX, ProviderHealth
from app.providers.groww_quote import GrowwQuoteProvider
from app.providers.nse_eod import NSEOfficialEODProvider
from app.providers.nse_live_vendor import NSELiveVendorProvider

_EOD_PROVIDER = NSEOfficialEODProvider()
_VENDOR_PROVIDER = NSELiveVendorProvider()
_GROWW_PROVIDER = GrowwQuoteProvider()


def get_provider_status_summary(con=None) -> Dict[str, Any]:
    """Returns active quote provider mode, health list, and honest per-family cadence matrix."""
    healths: List[ProviderHealth] = [
        _EOD_PROVIDER.health(con),
        _VENDOR_PROVIDER.health(con),
        _GROWW_PROVIDER.health(con),
    ]
    eod_h, vendor_h, groww_h = healths
    if vendor_h.enabled and vendor_h.status == "active":
        active_provider = vendor_h.provider_id
        active_mode = vendor_h.mode
    elif groww_h.enabled and groww_h.status == "active":
        active_provider = groww_h.provider_id
        active_mode = groww_h.mode
    else:
        active_provider = eod_h.provider_id
        active_mode = eod_h.mode

    return {
        "active_quote_provider": active_provider,
        "active_price_mode": active_mode,
        "is_realtime_active": active_mode == "Live",
        "price_as_of": eod_h.last_success,
        "providers": [h.to_dict() for h in healths],
        "cadence_matrix": METRIC_CADENCE_MATRIX,
    }


__all__ = [
    "NSEOfficialEODProvider",
    "NSELiveVendorProvider",
    "GrowwQuoteProvider",
    "get_provider_status_summary",
    "METRIC_CADENCE_MATRIX",
]

