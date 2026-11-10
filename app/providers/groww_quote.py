"""Optional Groww Trade API Live-Data Quote Adapter.

Follows Groww's published Live Data REST specification:
- Endpoint: https://api.groww.in/v1/live-data/ohlc?segment=CASH&exchange_symbols=NSE_RELIANCE,...
- Headers: Authorization: Bearer <GROWW_ACCESS_TOKEN>, X-API-VERSION: 1.0, Accept: application/json
- Up to 50 symbols per request.

Only active when `GROWW_ACCESS_TOKEN` is supplied via environment variables.
Credentials are never hardcoded, stored in repo files, or emitted in logs/responses.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.providers.base import FreshnessTier, MarketDataProvider, ProviderHealth, QuoteRecord

GROWW_OHLC_URL = "https://api.groww.in/v1/live-data/ohlc"
GROWW_LTP_URL = "https://api.groww.in/v1/live-data/ltp"


class GrowwQuoteProvider(MarketDataProvider):
    provider_id = "groww_live_api"

    def __init__(self) -> None:
        self._last_error: Optional[str] = None
        self._last_success: Optional[str] = None

    def _token(self) -> str:
        return os.environ.get("GROWW_ACCESS_TOKEN", "").strip()

    def _enabled(self) -> bool:
        flag = os.environ.get("GROWW_API_ENABLED", "true").strip().lower()
        return bool(self._token()) and flag not in {"0", "false", "no", "off"}

    def health(self, con=None) -> ProviderHealth:
        has_token = bool(self._token())
        enabled = self._enabled()
        if not has_token:
            status = "unconfigured"
            detail = "Not configured: supply GROWW_ACCESS_TOKEN in runtime environment for personal live quotes."
        elif not enabled:
            status = "disabled"
            detail = "Disabled via GROWW_API_ENABLED=false."
        elif self._last_error:
            status = "error"
            detail = f"Last API error: {self._last_error}"
        else:
            status = "active"
            detail = "Groww Live Data REST API ready (up to 50 NSE CASH symbols/request)."

        return ProviderHealth(
            provider_id=self.provider_id,
            display_name="Groww Trade API Live Data (Optional Personal Broker Feed)",
            configured=has_token,
            enabled=enabled,
            mode=FreshnessTier.LIVE.value if enabled else FreshnessTier.UNCONFIGURED.value,
            cadence="On-demand / Live Market Hours (max 50 symbols/call)" if enabled else "Disabled (token not set)",
            status=status,
            last_success=self._last_success,
            last_error=self._last_error,
            detail=detail,
            authorized_redistribution="Personal broker API key only — single-user workstation; not for public multi-tenant redistribution.",
            supported_capabilities=["intraday_ltp", "ohlc_snapshot"] if enabled else [],
        )

    def fetch_quotes(self, symbols: List[str], con=None) -> List[QuoteRecord]:
        token = self._token()
        if not token or not self._enabled() or not symbols:
            return []

        clean = [s.strip().upper() for s in symbols if s and s.strip()]
        out: List[QuoteRecord] = []
        now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        for idx in range(0, len(clean), 50):
            chunk = clean[idx: idx + 50]
            exch_syms = ",".join(f"NSE_{s}" for s in chunk)
            params = urllib.parse.urlencode({"segment": "CASH", "exchange_symbols": exch_syms})
            req_ltp = urllib.request.Request(
                f"{GROWW_LTP_URL}?{params}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-API-VERSION": "1.0",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req_ltp, timeout=8.0) as resp:
                    data: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                payload = data.get("payload") or {}
                for k, val in payload.items():
                    sym = str(k).replace("NSE_", "").strip().upper()
                    if val is None:
                        continue
                    out.append(
                        QuoteRecord(
                            symbol=sym,
                            ltp=float(val),
                            as_of=now_iso,
                            freshness=FreshnessTier.LIVE.value,
                            latency_seconds=0,
                            provider=self.provider_id,
                            source_note="Groww Live Data API (CASH)",
                        )
                    )
                self._last_success = now_iso
                self._last_error = None
            except urllib.error.HTTPError as exc:
                self._last_error = f"HTTP {exc.code}"
                break
            except Exception as exc:
                self._last_error = str(exc)[:160]
                break
        return out

