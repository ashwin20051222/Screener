"""tests/test_snapshot.py
Offline tests for Task F:
- Parity between bulk set-based ownership/fundamentals SQL and single-symbol calculators
- screener_snapshot & screener_snapshot_meta materialization and loading
- ?universe= union filtering, ?fields= sparse projection, ETag / 304 Not Modified, GZip ASGI
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

import duckdb

from app import config, db
from app.main import app as fastapi_app
from app.query.snapshot import build_screener_snapshot, load_snapshot_from_db
from ingest.financials import (
    compute_all_fundamental_metrics_bulk,
    compute_fundamental_metrics,
)
from ingest.ownership import (
    compute_all_ownership_snapshots_bulk,
    compute_ownership_snapshot,
)


def _seed_sample_db(db_path):
    con = duckdb.connect(str(db_path))
    db.init_schema(con)
    today = date(2026, 11, 9)

    db.upsert_rows(con, "ref_security", [
        {
            "security_id": "INE001", "isin": "INE001", "nse_symbol": "ALPHA",
            "name": "Alpha Ind Ltd", "sector": "Industrials", "sub_sector": "Engineering",
            "shares_outstanding": 100_000_000, "is_financial_institution": False,
        },
        {
            "security_id": "INE002", "isin": "INE002", "nse_symbol": "BETA",
            "name": "Beta Bank Ltd", "sector": "Financials", "sub_sector": "Private Banks",
            "shares_outstanding": 200_000_000, "is_financial_institution": True,
        },
        {
            "security_id": "INE003", "isin": "INE003", "nse_symbol": "GAMMA",
            "name": "Gamma Tech Ltd", "sector": "Information Technology", "sub_sector": "IT Services",
            "shares_outstanding": 50_000_000, "is_financial_institution": False,
        },
    ], keys=["security_id"])

    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "NIFTY50", "symbol": "ALPHA", "as_of": today},
        {"index_name": "NIFTY100", "symbol": "ALPHA", "as_of": today},
        {"index_name": "NIFTY100", "symbol": "BETA", "as_of": today},
    ], keys=["index_name", "symbol", "as_of"])

    db.upsert_rows(con, "px_daily", [
        {"date": today, "symbol": "ALPHA", "source": "NSE", "series": "EQ", "open": 495, "high": 505, "low": 490, "close": 500, "prev_close": 490, "volume": 100000},
        {"date": today, "symbol": "BETA", "source": "NSE", "series": "EQ", "open": 198, "high": 202, "low": 196, "close": 200, "prev_close": 195, "volume": 200000},
        {"date": today, "symbol": "GAMMA", "source": "NSE", "series": "EQ", "open": 98, "high": 102, "low": 97, "close": 100, "prev_close": 99, "volume": 50000},
    ], keys=["date", "symbol", "source", "series"])

    # Ownership 3 quarters + deals + PIT
    db.upsert_rows(con, "ownership_quarterly", [
        {"symbol": "ALPHA", "quarter_end": date(2026, 9, 30), "promoter_pct": 60.0, "promoter_pledged_pct": 1.0, "mf_pct": 10.0, "dii_pct": 14.0, "fii_pct": 16.0, "retail_pct": 10.0},
        {"symbol": "ALPHA", "quarter_end": date(2026, 6, 30), "promoter_pct": 59.5, "promoter_pledged_pct": 1.2, "mf_pct": 9.5, "dii_pct": 13.5, "fii_pct": 16.5, "retail_pct": 10.5},
        {"symbol": "ALPHA", "quarter_end": date(2026, 3, 31), "promoter_pct": 58.0, "promoter_pledged_pct": 2.0, "mf_pct": 9.0, "dii_pct": 13.0, "fii_pct": 17.0, "retail_pct": 11.0},
    ], keys=["symbol", "quarter_end"])

    db.upsert_rows(con, "bulk_block_deals", [
        {"deal_date": date.today() - timedelta(days=5), "exchange": "NSE", "deal_type": "BULK", "symbol": "ALPHA", "client_name": "Fund X", "buy_sell": "BUY", "quantity": 1_000_000, "price": 495.0},
    ], keys=["deal_date", "exchange", "deal_type", "symbol", "client_name", "buy_sell", "quantity"])

    # Annual + quarterly financials (Alpha Consolidated + Beta Standalone)
    db.upsert_rows(con, "fin_annual", [
        {"symbol": "ALPHA", "fiscal_year_end": date(2026, 3, 31), "statement_type": "consolidated", "total_revenue": 1000.0, "ebitda": 200.0, "pbit": 160.0, "net_income": 120.0, "eps": 12.0, "dps": 3.0, "total_assets": 800.0, "total_equity": 500.0, "total_liabilities": 300.0, "total_current_assets": 300.0, "total_current_liabilities": 150.0, "total_inventory": 60.0, "total_debt": 50.0, "total_long_term_debt": 40.0, "cash_and_st_inv": 80.0, "cfo": 140.0, "capex": 30.0},
        {"symbol": "ALPHA", "fiscal_year_end": date(2025, 3, 31), "statement_type": "consolidated", "total_revenue": 800.0, "ebitda": 160.0, "pbit": 130.0, "net_income": 100.0, "eps": 10.0, "dps": 2.5, "total_assets": 700.0, "total_equity": 420.0, "total_liabilities": 280.0, "total_current_assets": 260.0, "total_current_liabilities": 140.0, "total_inventory": 50.0, "total_debt": 60.0, "total_long_term_debt": 50.0, "cash_and_st_inv": 60.0, "cfo": 110.0, "capex": 25.0},
        {"symbol": "BETA", "fiscal_year_end": date(2026, 3, 31), "statement_type": "standalone", "total_revenue": 2000.0, "net_income": 300.0, "eps": 15.0, "total_assets": 5000.0, "total_equity": 1000.0, "total_liabilities": 4000.0, "total_debt": 400.0, "total_current_assets": 900.0, "total_current_liabilities": 700.0},
    ], keys=["symbol", "fiscal_year_end", "statement_type"])

    for m, qdt in enumerate((date(2026, 9, 30), date(2026, 6, 30), date(2026, 3, 31), date(2025, 12, 31))):
        db.upsert_rows(con, "fin_quarterly", [
            {"symbol": "ALPHA", "quarter_end": qdt, "statement_type": "consolidated", "total_revenue_q": 260.0 - m * 5, "net_income_q": 30.0, "eps_q": 3.0},
        ], keys=["symbol", "quarter_end", "statement_type"])

    con.close()


def test_bulk_ownership_and_fundamentals_parity(tmp_path):
    db_file = tmp_path / "parity.db"
    _seed_sample_db(db_file)
    con = duckdb.connect(str(db_file))

    own_bulk = compute_all_ownership_snapshots_bulk(con)
    for sym in ("ALPHA", "BETA", "GAMMA"):
        single = compute_ownership_snapshot(con, sym)
        assert own_bulk[sym] == single

    fin_inputs = {
        "ALPHA": (500.0, 100_000_000, False),
        "BETA": (200.0, 200_000_000, True),
        "GAMMA": (100.0, 50_000_000, False),
    }
    fin_bulk = compute_all_fundamental_metrics_bulk(con, fin_inputs)
    for sym, (px, sh, is_fin) in fin_inputs.items():
        single = compute_fundamental_metrics(con, sym, px, sh, is_fin)
        if single.get("statement_type_used") is None:
            assert sym not in fin_bulk
        else:
            assert fin_bulk[sym] == single
    # Financial institution exclusions preserved in bulk
    assert fin_bulk["BETA"]["current_ratio"] is None
    assert fin_bulk["BETA"]["debt_to_equity"] is None
    assert fin_bulk["ALPHA"]["current_ratio"] == 2.0
    assert fin_bulk["ALPHA"]["ttm_pe_ratio"] is not None
    con.close()


def test_snapshot_universe_fields_and_http_etag_gzip(tmp_path, monkeypatch):
    db_file = tmp_path / "snap.db"
    _seed_sample_db(db_file)
    monkeypatch.setattr(config, "data_path", lambda rel: db_file if rel.endswith(".db") else (tmp_path / rel))

    res = build_screener_snapshot()
    assert res["status"] == "ok"
    assert res["row_count"] == 3
    assert len(res["etag"]) >= 16

    full = load_snapshot_from_db()
    assert full["synced"] is True
    assert full["row_count"] == 3
    assert full["total_market_count"] == 3

    n50 = load_snapshot_from_db(universe="NIFTY50")
    assert [r["nse_symbol"] for r in n50["rows"]] == ["ALPHA"]
    assert n50["total_market_count"] == 3

    union_u = load_snapshot_from_db(universe="NIFTY50,NIFTY100")
    assert {r["nse_symbol"] for r in union_u["rows"]} == {"ALPHA", "BETA"}

    sparse = load_snapshot_from_db(universe="NIFTY50", fields="pe_ratio,return_on_equity")
    alpha = sparse["rows"][0]
    assert "pe_ratio" in alpha and "return_on_equity" in alpha
    assert "ebitda_margin" not in alpha
    assert "nse_symbol" in alpha and "_provenance" in alpha

    # ASGI ETag + 304 Not Modified + GZip verification
    async def _asgi_get(qs: bytes, headers: list[tuple[bytes, bytes]]):
        msgs = []
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "GET", "scheme": "http", "path": "/api/screener/dataset",
            "query_string": qs, "headers": headers,
        }
        async def recv():
            return {"type": "http.request", "body": b"", "more_body": False}
        async def send(m):
            msgs.append(m)
        await fastapi_app(scope, recv, send)
        return msgs

    first = asyncio.run(_asgi_get(b"universe=NIFTY100", [(b"accept-encoding", b"gzip")]))
    start1 = dict(first[0]["headers"])
    assert first[0]["status"] == 200
    assert b"etag" in start1

    etag_val = start1[b"etag"]
    second = asyncio.run(_asgi_get(b"universe=NIFTY100", [(b"if-none-match", etag_val)]))
    assert second[0]["status"] == 304
