"""Polite HTTP client for official financial sites.

Policy (NON-NEGOTIABLE #1 + DATA_SOURCES ToS notes):
- one request at a time, per-host minimum interval, retries with backoff;
- desktop-browser User-Agent with our app name (identified, not spoofed into anonymity);
- every successful response cached to data/raw/<source>/ so the pipeline can run offline later
  and every number remains traceable to a file;
- 403/429 => stop attempting immediately for this run (manual inbox fallback is the designed path).
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.config import data_path, settings

log = logging.getLogger(__name__)

_DEFAULT_UA = "ScreenerDesk/0.1 (offline-local screener; personal use) requests"


class _HostThrottle:
    """Minimum interval + jitter between requests to a single host."""

    def __init__(self, min_interval: float = 4.0, jitter: float = 1.5):
        self.min_interval = min_interval
        self.jitter = jitter
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        now = time.monotonic()
        prev = self._last.get(host)
        wait_for = 0.0
        if prev is not None:
            elapsed = now - prev
            if elapsed < self.min_interval:
                wait_for = self.min_interval - elapsed
        if wait_for:
            time.sleep(wait_for + random.uniform(0, self.jitter))
        self._last[host] = time.monotonic()


_throttle = _HostThrottle()


class FetchResult:
    __slots__ = ("status", "bytes", "url", "saved_path", "error")

    def __init__(self, status: int | None, bytes_: bytes | None, url: str,
                 saved_path: Path | None = None, error: str | None = None):
        self.status = status
        self.bytes = bytes_
        self.url = url
        self.saved_path = saved_path
        self.error = error

    def ok(self) -> bool:
        return self.status == 200 and self.bytes is not None


def save_raw(source: str, name: str, payload: bytes) -> Path:
    """Cache the raw official file under data/raw (never commit; used for traceability + offline)."""
    digest = hashlib.sha256(payload).hexdigest()[:16]
    out_dir = data_path(settings()["data"]["raw_dir"]) / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}__{digest}.bin"
    out.write_bytes(payload)
    return out


def fetch(
    url: str,
    *,
    source: str,
    session: requests.Session | None = None,
    save_name: str | None = None,
    rate_limit: float | None = None,
) -> FetchResult:
    """GET with retries/backoff, per-host throttle, and raw caching.

    Returns FetchResult; never raises for HTTP-level failure of the target resource.
    """
    from app.config import endpoints

    defaults = endpoints().get("common_defaults") or {}

    s = session or requests.Session()
    s.headers.setdefault("User-Agent", _DEFAULT_UA)
    s.headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    if "Accept" not in s.headers:
        s.headers["Accept"] = "*/*"

    host = urlparse(url).netloc
    interval = rate_limit or float(defaults.get("min_interval_seconds_per_host", 4))
    retries = int(defaults.get("retries", 3) or 3)

    backoffs = [5, 15, 45]
    attempt = 0
    while True:
        _throttle.wait(host)
        try:
            resp = s.get(url, timeout=60, allow_redirects=True)
        except requests.RequestException as e:
            log.warning("fetch %s attempt %d network error: %s", url, attempt + 1, e)
            error = f"net:{type(e).__name__}"
            status = None
        else:
            status = resp.status_code
            if status == 200:
                payload = resp.content
                saved = save_raw(source, save_name or urlparse(url).path.rsplit("/", 1)[-1], payload)
                log.info("fetched %s (%dB) -> %s", url, len(payload), saved)
                return FetchResult(status, payload, url, saved)
            if status in (403, 429):
                # Bot-protection semantics: don't hammer. Manual-import fallback is the policy path.
                log.warning("fetch %s -> %s; stopping (respects publisher controls)", url, status)
                return FetchResult(status, None, url, error=f"http:{status}")
            if status in (404, 400, 410):
                return FetchResult(status, None, url, error=f"http:{status}")
            log.warning("fetch %s -> %d", url, status)
            error = f"http:{status}"

        attempt += 1
        if attempt > retries:
            return FetchResult(status, None, url, error=error or "exhausted")
        wait = backoffs[min(attempt - 1, len(backoffs) - 1)]
        log.info("backoff %.0fs before retry", wait)
        time.sleep(wait)


def bootstrap_nse_session() -> requests.Session:
    """Session for www.nseindia.com APIs: homepage cookies + API-ish headers.

    Discovery note (2026-10-25): a plain homepage GET may return 403 while the API still accepts
    the cookie jar (verified). We attempt the homepage but never loop on its failure.
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": _DEFAULT_UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        _throttle.wait("www.nseindia.com")
        s.get("https://www.nseindia.com/", timeout=25)
    except requests.RequestException:
        pass  # proceed with whatever cookies we have; API may still work (verified behavior)
    return s


def fetch_json(url: str, *, source: str) -> dict | list | None:
    r = fetch(url, source=source)
    if not r.ok():
        return None
    try:
        return json.loads(r.bytes)
    except json.JSONDecodeError:
        log.warning("non-JSON payload from %s (len=%s)", url, len(r.bytes or b""))
        return None
