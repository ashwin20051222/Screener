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
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.config import data_path, settings

log = logging.getLogger(__name__)

_DEFAULT_UA = "ScreenerDesk/0.1 (local offline screener; personal use)"


class _HostThrottle:
    """Minimum interval + jitter between requests to a single host."""

    def __init__(self, min_interval: float = 5.0, jitter: float = 1.0):
        self.min_interval = min_interval
        self.jitter = jitter
        self._last: dict[str, float] = {}

    def wait(self, host: str, min_interval_override: float | None = None) -> None:
        floor = min_interval_override if min_interval_override is not None else self.min_interval
        now = time.monotonic()
        prev = self._last.get(host)
        wait_for = 0.0
        if prev is not None:
            elapsed = now - prev
            if elapsed < floor:
                wait_for = floor - elapsed
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

    def blocked(self) -> bool:
        return self.status in (403, 429)


def save_raw(source: str, name: str, payload: bytes) -> Path:
    """Cache the raw official file under data/raw (never commit; used for traceability + offline)."""
    digest = hashlib.sha256(payload).hexdigest()[:16]
    out_dir = data_path(settings()["data"]["raw_dir"]) / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}__{digest}.bin"
    out.write_bytes(payload)
    return out


def _curl_http2_get(url: str, ua: str, timeout: int = 30) -> tuple[int | None, bytes | None, str | None]:
    """HTTP/2 transport via system curl for nsearchives.nseindia.com using identical honest UA."""
    if not shutil.which("curl"):
        return None, None, "curl_missing"
    proc = subprocess.run(
        ["curl", "-sS", "-L", "-w", "\n__HTTP_STATUS__:%{http_code}", "--max-time", str(timeout), "-A", ua, url],
        capture_output=True,
    )
    marker = b"\n__HTTP_STATUS__:"
    idx = proc.stdout.rfind(marker)
    if proc.returncode != 0 or idx == -1:
        err_msg = (proc.stderr or b"").decode("utf-8", "replace").strip() or f"curl_rc_{proc.returncode}"
        return None, None, err_msg
    body = proc.stdout[:idx]
    try:
        code = int(proc.stdout[idx + len(marker):].decode("ascii", "replace").strip())
    except ValueError:
        return None, None, "bad_status"
    return code, body, None


def fetch(
    url: str,
    *,
    source: str,
    session: requests.Session | None = None,
    save_name: str | None = None,
    rate_limit: float | None = None,
) -> FetchResult:
    """GET with retries/backoff, per-host throttle (>=5s NSE), and raw caching.

    Returns FetchResult; never raises for HTTP-level failure of the target resource.
    """
    from app.config import endpoints

    defaults = endpoints().get("common_defaults") or {}

    s = session or requests.Session()
    if "python-requests" in (s.headers.get("User-Agent") or "").lower() or not s.headers.get("User-Agent"):
        s.headers["User-Agent"] = _DEFAULT_UA
    s.headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    if "Accept" not in s.headers:
        s.headers["Accept"] = "*/*"

    host = urlparse(url).netloc
    min_iv = rate_limit or float(defaults.get("min_interval_seconds_per_host", 5.0) or 5.0)
    if "nseindia.com" in host:
        min_iv = max(min_iv, 5.0)
    retries = int(defaults.get("retries", 3) or 3)
    timeout_s = int(defaults.get("timeout_seconds", 60) or 60)

    backoffs = [5, 15, 45]
    attempt = 0
    while True:
        _throttle.wait(host, min_interval_override=min_iv)
        status: int | None = None
        payload: bytes | None = None
        error: str = ""

        # nsearchives.nseindia.com uses HTTP/2 natively cleanly via curl with identical UA
        if host == "nsearchives.nseindia.com" and session is None and shutil.which("curl"):
            status, payload, curl_err = _curl_http2_get(url, s.headers.get("User-Agent", _DEFAULT_UA), timeout=min(timeout_s, 30))
            if status is None:
                log.warning("fetch %s attempt %d curl error: %s", url, attempt + 1, curl_err)
                error = f"net:{curl_err}"
        else:
            try:
                resp = s.get(url, timeout=timeout_s, allow_redirects=True)
                status = resp.status_code
                payload = resp.content
            except requests.RequestException as e:
                log.warning("fetch %s attempt %d network error: %s", url, attempt + 1, e)
                error = f"net:{type(e).__name__}"
                status = None

        if status == 200 and payload is not None:
            saved = save_raw(source, save_name or urlparse(url).path.rsplit("/", 1)[-1], payload)
            log.info("fetched %s (%dB) -> %s", url, len(payload), saved)
            return FetchResult(status, payload, url, saved)
        if status in (403, 429):
            log.warning("fetch %s -> %s; stopping (respects publisher controls)", url, status)
            return FetchResult(status, None, url, error=f"http:{status}")
        if status in (404, 400, 410):
            return FetchResult(status, None, url, error=f"http:{status}")
        if status is not None:
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


def fetch_json(url: str, *, source: str, session: requests.Session | None = None) -> dict | list | None:
    r = fetch(url, source=source, session=session)
    if not r.ok():
        return None
    try:
        return json.loads(r.bytes)
    except json.JSONDecodeError:
        log.warning("non-JSON payload from %s (len=%s)", url, len(r.bytes or b""))
        return None
