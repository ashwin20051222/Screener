"""Optional pluggable NSE Authorized Real-Time / Delayed Vendor adapter.

Only activates when explicit user-supplied vendor environment variables are set:
- NSE_LIVE_VENDOR_NAME (e.g., Global Financial Datafeeds LLP / TrueData)
- NSE_LIVE_VENDOR_BASE_URL (REST snapshot base URL)
- NSE_LIVE_VENDOR_API_KEY (Bearer / API key read strictly from env, never logged)
- NSE_LIVE_VENDOR_MODE ("live" | "delayed_1_3m" | "delayed_15m")

Default state when unconfigured is cleanly `unconfigured` (never fakes real-time).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.providers.base import FreshnessTier, MarketDataProvider, ProviderHealth, QuoteRecord

_MODE_MAP = {
    "live": FreshnessTier.LIVE.value,
    "delayed_1_3m": FreshnessTier.DELAYED_1_3M.value,
    "delayed_15m": FreshnessTier.DELAYED_15M.value,
}


class NSELiveVendorProvider(MarketDataProvider):
    provider_id = "nse_live_vendor"

    def _config(self) -> Dict[str, str]:
        return {
            "name": os.environ.get("NSE_LIVE_VENDOR_NAME", "").strip(),
            "base_url": os.environ.get("NSE_LIVE_VENDOR_BASE_URL", "").strip(),
            "api_key": os.environ.get("NSE_LIVE_VENDOR_API_KEY", "").strip(),
            "mode_key": os.environ.get("NSE_LIVE_VENDOR_MODE", "delayed_15m").strip().lower(),
        }

    def health(self, con=None) -> ProviderHealth:
        cfg = self._config()
        configured = bool(cfg["base_url"] and cfg["api_key"])
        mode_label = _MODE_MAP.get(cfg["mode_key"], FreshnessTier.DELAYED_15M.value)
        vendor_name = cfg["name"] or "NSE Authorized Data Vendor (Global Datafeeds / TrueData / Licensed Feed)"
        return ProviderHealth(
            provider_id=self.provider_id,
            display_name=vendor_name,
            configured=configured,
            enabled=configured,
            mode=mode_label if configured else FreshnessTier.UNCONFIGURED.value,
            cadence=f"Streaming / Snapshot ({mode_label})" if configured else "Requires licensed vendor credentials",
            status="active" if configured else "unconfigured",
            last_success=None,
            last_error=None,
            detail=(
                f"Configured vendor endpoint ready ({mode_label})."
                if configured
                else "Not configured: set NSE_LIVE_VENDOR_BASE_URL and NSE_LIVE_VENDOR_API_KEY in environment to enable licensed intraday feed."
            ),
            authorized_redistribution="Governed by user license agreement with NSE Data & Analytics authorized vendor.",
            supported_capabilities=["intraday_ltp", "ohlcv_snapshot", "fno_live_quotes"] if configured else [],
        )

    def fetch_quotes(self, symbols: List[str], con=None) -> List[QuoteRecord]:
        cfg = self._config()
        if not (cfg["base_url"] and cfg["api_key"]) or not symbols:
            return []
        clean = [s.strip().upper() for s in symbols if s and s.strip()][:50]
        mode_label = _MODE_MAP.get(cfg["mode_key"], FreshnessTier.DELAYED_15M.value)
        url = f"{cfg['base_url'].rstrip('/')}?symbols={urllib.parse.quote(','.join(clean))}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        items = payload.get("quotes") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        out: List[QuoteRecord] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            sym = str(item.get("symbol") or "").upper()
            ltp = item.get("ltp") or item.get("last_price")
            if not sym or ltp is None:
                continue
            out.append(
                QuoteRecord(
                    symbol=sym,
                    ltp=float(ltp),
                    open=float(item["open"]) if item.get("open") is not None else None,
                    high=float(item["high"]) if item.get("high") is not None else None,
                    low=float(item["low"]) if item.get("low") is not None else None,
                    prev_close=float(item["prev_close"]) if item.get("prev_close") is not None else None,
                    volume=int(item["volume"]) if item.get("volume") is not None else None,
                    as_of=str(item.get("timestamp") or now_iso),
                    freshness=mode_label,
                    provider=self.provider_id,
                    source_note=cfg["name"] or "NSE Authorized Vendor",
                )
            )
        return out

