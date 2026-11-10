"""ScreenerDesk API (step 2: health + source status; screener query API lands in step 4)."""
from __future__ import annotations

import html as _html
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import duckdb

from app import db, scheduler
from app.api.routes import router as screener_router
from app.config import settings
from ingest import sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        con = db.connect()
        db.init_schema(con)
        con.close()
    except duckdb.IOException:
        logging.getLogger(__name__).warning(
            "DB locked by an active sync process; skipping schema init "
            "(schema already applied to the existing database)")
    sched = scheduler.build_scheduler()
    sched.start()
    yield
    sched.shutdown(wait=False)


app = FastAPI(title=settings()["app"]["name"], lifespan=lifespan)
app.include_router(screener_router)


@app.get("/health")
def health():
    return {"ok": True, "app": settings()["app"]["name"], "note": "offline-first; no login; nothing locked"}


@app.get("/api/meta/status")
def meta_status():
    """Feeds the results-pane sub-bar: 'last updated at <time> IST' + source as-of badges."""
    try:
        return sources.status_report()
    except duckdb.IOException:
        return {"px_per_source": [], "fno_as_of": "n/a", "amfi_period": "n/a",
                "corp_actions_as_of": "n/a", "fbil_as_of": "n/a",
                "securities": {"total": 0, "fno_eligible": None, "etf": None},
                "recent_jobs": [], "degraded": "database is locked by an active sync; retry shortly"}


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — data status</title>
<style>
:root{{--bg:#0b1220;--card:#101a2e;--line:#1e2b45;--txt:#e6edf7;--mut:#8aa0bd;--ok:#22c55e;--warn:#f59e0b;--dim:#64748b}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--txt);font:15px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;padding:32px 20px}}
.wrap{{max-width:860px;margin:0 auto}}
.brand{{display:flex;align-items:baseline;gap:10px;margin-bottom:4px}}
.brand h1{{font-size:22px;letter-spacing:.3px}}
.brand span{{color:var(--mut);font-size:13px}}
.note{{color:var(--mut);font-size:13px;margin-bottom:22px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:16px}}
.card h2{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);margin-bottom:12px}}
.row{{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px dashed var(--line);font-size:14px}}
.row:last-child{{border-bottom:none}}
.k{{color:var(--mut)}}
.badge{{font-size:12px;padding:2px 10px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}}
.b-ok{{color:var(--ok);border-color:rgba(34,197,94,.4)}}
.b-na{{color:var(--warn);border-color:rgba(245,158,11,.35)}}
footer{{color:var(--dim);font-size:12px;margin-top:18px}}
a{{color:#7dd3fc;text-decoration:none}}
</style></head><body><div class="wrap">
<div class="brand"><h1>{name}</h1><span>Step 2 — data pipeline &amp; provenance</span></div>
<div class="note">Offline-first · official sources only · {note}</div>

<div class="card"><h2>Securities universe</h2>
<div class="row"><span class="k">Exchange master rows</span><b>{n_sec}</b></div>
<div class="row"><span class="k">F&amp;O eligible</span><b>{fno}</b></div>
<div class="row"><span class="k">ETFs</span><b>{etf}</b></div>
</div>

<div class="card"><h2>Source as-of badges</h2>
{px_rows}
<div class="row"><span class="k">F&amp;O lots / bhavcopy</span><span class="badge {fno_cls}">{fno_asof}</span></div>
<div class="row"><span class="k">AMFI AUM period</span><span class="badge {amfi_cls}">{amfi}</span></div>
<div class="row"><span class="k">Corporate actions (NSE)</span><span class="badge {ca_cls}">{ca}</span></div>
<div class="row"><span class="k">FBIL FX reference</span><span class="badge {fbil_cls}">{fbil}</span></div>
</div>

<div class="card"><h2>Recent sync jobs</h2>
{jobs}
</div>

<footer>Browse the raw API at <a href="/docs">/docs</a> · screener grid UI ships in a later step · every displayed value carries a source + as-of badge.</footer>
</div></body></html>"""


def _badge(value: str, missing: tuple[str, ...] = ("n/a", "", "none", "empty")) -> str:
    ok = value.strip().lower() not in missing
    return f'<span class="badge {"b-ok" if ok else "b-na"}">{_html.escape(value)}</span>'


def _row(key: str, badge_html: str = "") -> str:
    tail = badge_html or '<span class="badge b-na">empty</span>'
    return f'<div class="row"><span class="k">{_html.escape(key)}</span>{tail}</div>'


_EMPTY_JOBS = _row("no sync jobs recorded yet")
_EMPTY_PX = _row("no price data yet — running sync will fill this in")


_WEB_DIST = Path(__file__).resolve().parents[1] / "apps" / "web" / "dist"
if (_WEB_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(_WEB_DIST / "assets")), name="web-assets")


@app.get("/", response_model=None)
def index():
    index_html = _WEB_DIST / "index.html"
    if index_html.is_file():
        return FileResponse(str(index_html))
    return HTMLResponse(status_page())


@app.get("/status", response_class=HTMLResponse)
def status_page():
    try:
        st = sources.status_report()
        locked = False
    except duckdb.IOException:
        # sync process holds the DB; show placeholder badges instead of a 500
        st = {"px_per_source": [], "fno_as_of": "n/a", "amfi_period": "n/a",
              "corp_actions_as_of": "n/a", "fbil_as_of": "n/a",
              "securities": {"total": 0, "fno_eligible": None, "etf": None},
              "recent_jobs": []}
        locked = True
    px_rows = "".join(_row(f'{s.get("source")} bhavcopy', _badge(str(s.get("as_of"))))
                      for s in st.get("px_per_source", [])) or _EMPTY_PX
    jobs = "".join(_row(str(j.get("kind")), _badge(str(j.get("finished_at") or "running"), ("running",)))
                   for j in st.get("recent_jobs", [])[:6]) or _EMPTY_JOBS
    return _PAGE.format(
        name=settings()["app"]["name"],
        note="⏳ sync in progress — the page will fill in when the running job finishes"
        if locked else "no login · nothing locked",
        n_sec=st.get("securities", {}).get("total", 0),
        fno=st.get("securities", {}).get("fno_eligible") or "—",
        etf=st.get("securities", {}).get("etf") or "—",
        px_rows=px_rows,
        fno_asof=str(st.get("fno_as_of")), amfi=str(st.get("amfi_period")),
        ca=str(st.get("corp_actions_as_of")), fbil=str(st.get("fbil_as_of")),
        fno_cls="b-na" if str(st.get("fno_as_of")).lower() in ("n/a", "") else "b-ok",
        amfi_cls="b-na" if str(st.get("amfi_period")).lower() in ("n/a", "") else "b-ok",
        ca_cls="b-na" if str(st.get("corp_actions_as_of")).lower() in ("n/a", "") else "b-ok",
        fbil_cls="b-na" if str(st.get("fbil_as_of")).lower() in ("n/a", "") else "b-ok",
        jobs=jobs,
    )


if __name__ == "__main__":
    import logging

    import uvicorn

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    uvicorn.run(app, host=settings()["app"].get("host", "127.0.0.1"),
                port=int(settings()["app"].get("port", 8787)), log_level="info")
