"""Official NSE EOD Price Provider reading authoritative NSE CM Bhavcopy data from DuckDB."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import duckdb

from app import config
from app.providers.base import (
    FreshnessTier,
    MarketDataProvider,
    ProviderHealth,
    QuoteRecord,
    classify_eod_freshness,
)


class NSEOfficialEODProvider(MarketDataProvider):
    provider_id = "nse_official_eod"

    def health(self, con=None) -> ProviderHealth:
        max_dt: Optional[date] = None
        row_cnt = 0
        err: Optional[str] = None
        own = con is None
        try:
            if own:
                db_p = config.data_path(config.settings()["data"]["db_path"])
                if db_p.exists():
                    con = duckdb.connect(str(db_p), read_only=True)
            if con is not None:
                res = con.execute(
                    "SELECT MAX(date), COUNT(DISTINCT symbol) FROM px_daily WHERE source != 'NSE-INDEX'"
                ).fetchone()
                if res:
                    max_dt = res[0]
                    row_cnt = int(res[1] or 0)
        except duckdb.IOException as exc:
            # Database is held by an external sync process; inspect sidecar snapshot cleanly
            try:
                from app.query.snapshot import _load_sidecar_snapshot
                sc = _load_sidecar_snapshot(fields="close_price")
                pr_s = (sc.get("as_of") or {}).get("price")
                if pr_s:
                    max_dt = date.fromisoformat(str(pr_s)[:10])
                    row_cnt = int(sc.get("total_market_count") or 0)
            except Exception:
                err = str(exc)
        except Exception as exc:
            err = str(exc)
        finally:
            if own and con is not None:
                con.close()

        tier = classify_eod_freshness(max_dt)
        status = "error" if err else ("active" if max_dt and tier == FreshnessTier.EOD.value else ("stale" if max_dt else "unconfigured"))
        return ProviderHealth(
            provider_id=self.provider_id,
            display_name="NSE Official Archives (EOD CM/FO Bhavcopy + XBRL)",
            configured=True,
            enabled=True,
            mode=tier if max_dt else FreshnessTier.EOD.value,
            cadence="Daily EOD (18:30 IST on NSE trading days)",
            status=status,
            last_success=str(max_dt) if max_dt else None,
            last_error=err,
            detail=(
                f"Latest NSE EOD close date: {max_dt} ({row_cnt} symbols)"
                if max_dt
                else "No NSE EOD bhavcopy synced yet; run Daily EOD sync."
            ),
            authorized_redistribution="Official exchange public archives (personal workstation / research policy compliant).",
            supported_capabilities=["eod_ohlcv", "historical_cm_backfill", "fno_eod_bhavcopy", "xbrl_filings", "shp_filings"],
        )

    def fetch_quotes(self, symbols: List[str], con=None) -> List[QuoteRecord]:
        if not symbols or con is None:
            return []
        clean = [s.strip().upper() for s in symbols if s and s.strip()]
        if not clean:
            return []
        placeholders = ", ".join(["?"] * len(clean))
        rows = con.execute(
            f"""
            SELECT symbol, close, open, high, low, prev_close, volume, date
            FROM px_daily
            WHERE source != 'NSE-INDEX' AND symbol IN ({placeholders})
            QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) = 1
            """,
            clean,
        ).fetchall()
        out: List[QuoteRecord] = []
        for sym, close, op, hi, lo, prev_c, vol, dt in rows:
            tier = classify_eod_freshness(dt)
            out.append(
                QuoteRecord(
                    symbol=sym,
                    ltp=close,
                    open=op,
                    high=hi,
                    low=lo,
                    prev_close=prev_c,
                    volume=vol,
                    as_of=str(dt) if dt else None,
                    freshness=tier,
                    latency_seconds=None,
                    provider=self.provider_id,
                    source_note="NSE CM Bhavcopy EOD close",
                )
            )
        return out

