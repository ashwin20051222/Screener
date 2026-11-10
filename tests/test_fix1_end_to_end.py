"""tests/test_fix1_end_to_end.py
Offline tests covering Fix Prompt #1 Task H verification requirements:
- Universe membership filtering, multi-universe deduplicated union, empty selection = all listed
- Honest row & dynamic sector counts (never hardcoded 5996 or 'Industrials'/'General' fallback)
- ingest_progress resume & HTTP 403 immediate stop (backfill + quarterly)
- Backfill holiday skipping (404 marked 'holiday' and skipped on resume)
- Registry & frontend JSON `feeds:` tag consistency (all 255 filters)
- End-to-end ETag change across data mutation
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import duckdb
import yaml

from app import config, db
from app.api.routes import get_screener_dataset, get_universes
from app.query.snapshot import build_screener_snapshot, load_snapshot_from_db
from ingest import backfill, http, sources
from scripts.coverage import compute_coverage_report

ROOT = Path(__file__).resolve().parents[1]


class _FakeFetchResult:
    def __init__(self, status: int | None, data: bytes | None = None, error: str | None = None):
        self.status = status
        self.bytes = data
        self.url = "https://mock.local/test"
        self.saved_path = None
        self.error = error

    def ok(self) -> bool:
        return self.status == 200 and self.bytes is not None

    def blocked(self) -> bool:
        return self.status in (403, 429)


def test_registry_and_web_json_feeds_consistent():
    reg = yaml.safe_load((ROOT / "registry" / "filters.yaml").read_text(encoding="utf-8"))
    web_doc = json.loads((ROOT / "apps" / "web" / "src" / "data" / "filters.json").read_text(encoding="utf-8"))
    web_filters = web_doc["filters"]
    allowed_feeds = {"amfi", "daily", "deals", "fno", "history", "manual", "shp", "unavailable", "weekly", "xbrl"}

    yaml_filters = reg["filters"]
    assert len(yaml_filters) == 255
    assert set(yaml_filters.keys()) == set(web_filters.keys())

    for fid, meta in yaml_filters.items():
        assert meta.get("feeds") in allowed_feeds, f"{fid} has invalid feeds={meta.get('feeds')}"
        assert web_filters[fid].get("feeds") == meta["feeds"], f"{fid} out of sync in apps/web/src/data/filters.json"


def test_universe_union_empty_honest_counts_and_unclassified(tmp_path, monkeypatch):
    db_file = tmp_path / "u_e2e.db"
    monkeypatch.setattr(config, "data_path", lambda rel: db_file if rel.endswith(".db") else (tmp_path / rel))

    con = duckdb.connect(str(db_file))
    db.init_schema(con)
    as_of = date(2026, 11, 9)

    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE01", "isin": "INE01", "nse_symbol": "AAA", "name": "AAA Co", "sector": "Financials", "sub_sector": "Private Banks", "shares_outstanding": 1000},
        {"security_id": "INE02", "isin": "INE02", "nse_symbol": "BBB", "name": "BBB Co", "sector": "Energy", "sub_sector": "Oil & Gas", "shares_outstanding": 1000},
        {"security_id": "INE03", "isin": "INE03", "nse_symbol": "CCC", "name": "CCC Co", "shares_outstanding": 1000},
    ], keys=["security_id"])
    db.upsert_rows(con, "px_daily", [
        {"date": as_of, "symbol": "AAA", "source": "NSE", "series": "EQ", "close": 100.0},
        {"date": as_of, "symbol": "BBB", "source": "NSE", "series": "EQ", "close": 200.0},
        {"date": as_of, "symbol": "CCC", "source": "NSE", "series": "EQ", "close": 50.0},
    ], keys=["date", "symbol", "source", "series"])
    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "NIFTY50", "symbol": "AAA", "as_of": as_of},
        {"index_name": "NIFTY100", "symbol": "AAA", "as_of": as_of},
        {"index_name": "NIFTY100", "symbol": "BBB", "as_of": as_of},
    ], keys=["index_name", "symbol", "as_of"])
    con.close()

    snap_res = build_screener_snapshot()
    assert snap_res["row_count"] == 3
    etag_v1 = snap_res["etag"]

    # Empty selection => all 3 equities
    all_ds = get_screener_dataset()
    assert all_ds["row_count"] == 3
    assert all_ds["total_market_count"] == 3
    assert all_ds["row_count"] != 5996

    # Check Unclassified fallback on CCC
    by_sym = {r["nse_symbol"]: r for r in all_ds["rows"]}
    assert by_sym["CCC"]["sector"] == "Unclassified"
    assert by_sym["CCC"]["sub_sector"] == "Unclassified"

    # Multi-universe deduplicated union (NIFTY50={AAA}, NIFTY100={AAA, BBB} => 2 rows, no dup AAA)
    union_ds = get_screener_dataset(universe="NIFTY50,NIFTY100")
    assert union_ds["row_count"] == 2
    assert [r["nse_symbol"] for r in union_ds["rows"]] == ["AAA", "BBB"]

    # Dynamic sector counts match exact loaded rows in coverage report
    rep = compute_coverage_report(all_ds)
    assert rep["by_sector"]["Unclassified"]["all"] == 1
    assert rep["by_sector"]["Financials"]["nifty100"] == 1
    assert rep["by_sector"]["Energy"]["nifty100"] == 1

    # Universe summary reflects real counts
    uni_list = get_universes()
    n50 = [u for u in uni_list if u["slug"] == "NIFTY50"][0]
    n100 = [u for u in uni_list if u["slug"] == "NIFTY100"][0]
    assert n50["count"] == 1 and n100["count"] == 2

    # Modifying DB invalidates ETag cleanly
    con2 = duckdb.connect(str(db_file))
    con2.execute("UPDATE px_daily SET close = 110.0 WHERE symbol = 'AAA'")
    con2.close()
    snap_v2 = build_screener_snapshot()
    assert snap_v2["etag"] != etag_v1


def test_backfill_holiday_skip_403_abort_and_resume(tmp_path, monkeypatch):
    db_file = tmp_path / "bf.db"
    monkeypatch.setattr(config, "data_path", lambda rel: db_file if rel.endswith(".db") else (tmp_path / rel))
    monkeypatch.setattr(backfill, "data_path", lambda rel: tmp_path / rel)

    con = duckdb.connect(str(db_file))
    db.init_schema(con)
    anchor = date(2026, 11, 6)  # Friday
    # Day 0 (Nov 6 Fri): 404 holiday; Day -1 (Nov 5 Thu): already stored in DB -> ok; Day -2 (Nov 4 Wed): 403 block!
    db.upsert_rows(con, "px_daily", [
        {"date": date(2026, 11, 5), "symbol": "AAA", "source": "NSE", "series": "EQ", "close": 100.0},
    ], keys=["date", "symbol", "source", "series"])

    fetched_urls = []

    def fake_fetch(url, *, source="", session=None, save_name=None, rate_limit=None):
        fetched_urls.append(url)
        if "20261106" in url:
            return _FakeFetchResult(404, None, "http:404")
        if "20261104" in url:
            return _FakeFetchResult(403, None, "http:403")
        return _FakeFetchResult(404, None, "http:404")

    monkeypatch.setattr(http, "fetch", fake_fetch)

    res1 = backfill.backfill_prices(
        con, trading_days=5, fo_days=0, resume=True, sync_actions=False, run_technicals=False, start_date=anchor
    )
    assert res1["blocked"] is True
    assert res1["status"] == "partial"
    assert res1["cm_holidays_marked"] == 1
    assert len(fetched_urls) == 2  # Stopped IMMEDIATELY on Nov 4 403 without scanning older days!
    assert "2026-11-06" in db.get_progress_keys(con, "backfill_cm", statuses=("holiday",))
    assert "2026-11-05" in db.get_progress_keys(con, "backfill_cm", statuses=("ok",))
    assert "2026-11-04" in db.get_progress_keys(con, "backfill_cm", statuses=("fail",))

    # Re-run with resume=True: Nov 6 holiday must NOT be refetched! Nov 4 still failed, hits 403 immediately cleanly.
    fetched_urls.clear()
    res2 = backfill.backfill_prices(
        con, trading_days=5, fo_days=0, resume=True, sync_actions=False, run_technicals=False, start_date=anchor
    )
    assert res2["blocked"] is True
    assert len(fetched_urls) == 1
    assert "20261104" in fetched_urls[0]
    con.close()


def test_quarterly_resume_and_403_abort(tmp_path, monkeypatch):
    db_file = tmp_path / "q.db"
    monkeypatch.setattr(config, "data_path", lambda rel: db_file if rel.endswith(".db") else (tmp_path / rel))
    con = duckdb.connect(str(db_file))
    db.init_schema(con)

    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE1", "isin": "INE1", "nse_symbol": "SYM1", "name": "Sym 1"},
        {"security_id": "INE2", "isin": "INE2", "nse_symbol": "SYM2", "name": "Sym 2"},
    ], keys=["security_id"])
    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "NIFTY100", "symbol": "SYM1", "as_of": date(2026, 11, 9)},
        {"index_name": "NIFTY100", "symbol": "SYM2", "as_of": date(2026, 11, 9)},
    ], keys=["index_name", "symbol", "as_of"])

    # Pre-checkpoint SYM1 as ok so resume skips SYM1 cleanly; fail immediately with 403 on SYM2!
    db.mark_progress(con, "quarterly", "SYM1", "ok", "already done")

    called = []
    monkeypatch.setattr(http, "bootstrap_nse_session", lambda *a, **k: object())

    def fake_shp(con_arg, sym, max_quarters=3, session=None):
        called.append(("shp", sym))
        return {"status": "blocked", "quarters": 0, "message": "http:403"}

    import ingest.ownership as own_mod
    monkeypatch.setattr(own_mod, "sync_shareholding_for_symbol", fake_shp)

    res = sources.run_quarterly(con, universe="nifty100", resume=True)
    assert res["skipped_resume"] == 1
    assert res["blocked"] is True
    assert res["status"] == "partial"
    assert called == [("shp", "SYM2")]
    con.close()
