"""tests/test_ownership.py
Offline tests for Step 4.4: Shareholding Pattern XBRL, Promoter Pledges, Bulk/Block Deals, SEBI PIT Insider Trades.
All fixtures reflect exact live official NSE XBRL/JSON structures observed 2026-11-10.
"""
from __future__ import annotations

from datetime import date, timedelta
import json
import duckdb
import pytest

from app import db
from ingest.ownership import (
    compute_ownership_snapshot,
    parse_largedeals_json,
    parse_pit_json_or_csv,
    sync_shareholding_xbrl_from_bytes,
)


@pytest.fixture()
def db_con(tmp_path):
    c = duckdb.connect(str(tmp_path / "own.duckdb"))
    db.init_schema(c)
    yield c
    c.close()


def _make_shp_xml(q_end: str, prom: float, mf: float, dii: float, fii: float, ins: float, retail: float, pledged: int, prom_shares: int, total_sh: int, shareholders: int) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrli="http://www.xbrl.org/2003/instance">
  <xbrli:context id="MainI"><xbrli:entity><xbrli:identifier>RELIANCE</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>{q_end}</xbrli:instant></xbrli:period></xbrli:context>
  <Symbol contextRef="MainI">TESTCORP</Symbol>
  <DateOfReport contextRef="MainI">{q_end}</DateOfReport>
  <NumberOfShareholders contextRef="ShareholdingPattern_ContextI">{shareholders}</NumberOfShareholders>
  <NumberOfShares contextRef="ShareholdingPattern_ContextI">{total_sh}</NumberOfShares>
  <NumberOfShares contextRef="ShareholdingOfPromoterAndPromoterGroup_ContextI">{prom_shares}</NumberOfShares>
  <NumberOfSharesPledgedOrOtherwiseEncumbered contextRef="ShareholdingOfPromoterAndPromoterGroup_ContextI">{pledged}</NumberOfSharesPledgedOrOtherwiseEncumbered>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="ShareholdingOfPromoterAndPromoterGroup_ContextI">{prom}</ShareholdingAsAPercentageOfTotalNumberOfShares>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="MutualFundsOrUTI_ContextI">{mf}</ShareholdingAsAPercentageOfTotalNumberOfShares>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="InstitutionsDomestic_ContextI">{dii}</ShareholdingAsAPercentageOfTotalNumberOfShares>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="InstitutionsForeign_ContextI">{fii}</ShareholdingAsAPercentageOfTotalNumberOfShares>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="InsuranceCompanies_ContextI">{ins}</ShareholdingAsAPercentageOfTotalNumberOfShares>
  <ShareholdingAsAPercentageOfTotalNumberOfShares contextRef="ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh_ContextI">{retail}</ShareholdingAsAPercentageOfTotalNumberOfShares>
</xbrl>""".encode()


def test_shp_xbrl_fractions_and_quarterly_changes(db_con):
    db.upsert_rows(db_con, "ref_security", [{
        "security_id": "INE001TEST01",
        "isin": "INE001TEST01",
        "nse_symbol": "TESTCORP",
        "name": "Test Corp",
        "shares_outstanding": 10_000_000,
    }], keys=["security_id"])

    # Ingest 3 quarters: Mar, Jun, Sep 2026 (with fractions like 0.5044 -> 50.44%)
    sync_shareholding_xbrl_from_bytes(db_con, _make_shp_xml("2026-03-31", 0.5000, 0.1000, 0.2000, 0.1500, 0.0800, 0.1200, 0, 5_000_000, 10_000_000, 50000))
    sync_shareholding_xbrl_from_bytes(db_con, _make_shp_xml("2026-06-30", 0.5020, 0.1050, 0.2080, 0.1520, 0.0850, 0.1180, 100_000, 5_020_000, 10_000_000, 52000))
    sync_shareholding_xbrl_from_bytes(db_con, _make_shp_xml("2026-09-30", 0.5044, 0.1131, 0.2172, 0.1550, 0.0947, 0.1150, 252_200, 5_044_000, 10_000_000, 55000))

    # Add Bulk deals & PIT insider trades inside 30D / 90D windows
    largedeal_blob = {
        "as_on_date": "15-Oct-2026",
        "BULK_DEALS_DATA": [
            {"buySell": "BUY", "clientName": "Fund A", "date": "10-Oct-2026", "qty": "200000", "symbol": "TESTCORP", "watp": "150.0"},
            {"buySell": "SELL", "clientName": "Trader B", "date": "05-Aug-2026", "qty": "50000", "symbol": "TESTCORP", "watp": "145.0"},
        ],
        "BLOCK_DEALS_DATA": [
            {"buySell": "BUY", "clientName": "Block Inst", "date": "12-Oct-2026", "qty": "100000", "symbol": "TESTCORP", "watp": "151.0"},
        ],
    }
    deals = parse_largedeals_json(largedeal_blob)
    db.upsert_rows(db_con, "bulk_block_deals", deals, keys=["deal_date", "exchange", "deal_type", "symbol", "client_name", "buy_sell", "quantity"])

    pit_blob = json.dumps({
        "data": [
            {"symbol": "TESTCORP", "acqName": "Director X", "secAcq": "50000", "tdpTransactionType": "Buy", "date": "12-Oct-2026"},
            {"symbol": "TESTCORP", "acqName": "KMP Y", "secAcq": "10000", "tdpTransactionType": "Sell", "date": "01-Jul-2026"},
        ]
    }).encode()
    pit_rows = parse_pit_json_or_csv(pit_blob)
    db.upsert_rows(db_con, "insider_trades", pit_rows, keys=["broadcast_date", "symbol", "acquirer_name", "transaction_type", "shares"])

    snap = compute_ownership_snapshot(db_con, "TESTCORP", as_of=date(2026, 10, 15))
    assert snap["promoter_holding"] == pytest.approx(50.44)
    assert snap["mutual_fund_holding"] == pytest.approx(11.31)
    assert snap["domestic_institutional_holding"] == pytest.approx(21.72)
    assert snap["insurance_firms_holding"] == pytest.approx(9.47)
    assert snap["pledged_promoter_holdings"] == pytest.approx(5.0)  # 252,200 / 5,044,000 * 100
    assert snap["no_of_shareholders"] == 55000

    # Percentage-point quarterly diffs
    assert snap["mf_holding_change_3m"] == pytest.approx(11.31 - 10.50)
    assert snap["mf_holding_change_6m"] == pytest.approx(11.31 - 10.00)
    assert snap["promoter_holding_change_3m"] == pytest.approx(50.44 - 50.20)
    assert snap["promoter_holding_change_6m"] == pytest.approx(50.44 - 50.00)

    # 1M Bulk deals: +200k + 100k = +300k shares / 10M = +3.0%
    assert snap["bulk_deals_1m_cumulative"] == pytest.approx(3.0)
    # 3M Bulk deals: +300k - 50k = +250k shares / 10M = +2.5%
    assert snap["bulk_deals_3m_cumulative"] == pytest.approx(2.5)
    # 1M PIT: +50k / 10M = +0.5%; 6M PIT: (+50k - 10k) / 10M = +0.4%
    assert snap["insider_trades_1m_cumulative"] == pytest.approx(0.5)
    assert snap["insider_trades_6m_cumulative"] == pytest.approx(0.4)


def test_pr_mcap_zip_and_shp_batch_resume_abort(tmp_path, monkeypatch):
    import io, zipfile
    from datetime import date
    from app import db
    from ingest import nse as nse_mod
    from ingest import ownership as own_mod
    from ingest.http import FetchResult
    from app.query.db_store import load_market_dataset_from_db

    import duckdb
    con = duckdb.connect(str(tmp_path / "pr_shp.db"))
    db.init_schema(con)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE002", "isin": "INE002", "nse_symbol": "AAA", "name": "AAA Ltd"},
        {"security_id": "INE003", "isin": "INE003", "nse_symbol": "BBB", "name": "BBB Ltd"},
        {"security_id": "INE004", "isin": "INE004", "nse_symbol": "CCC", "name": "CCC Ltd"},
    ], keys=["security_id"])
    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "NIFTY100", "symbol": "BBB", "as_of": date(2026, 11, 10)},
        {"index_name": "NIFTY500", "symbol": "CCC", "as_of": date(2026, 11, 10)},
    ], keys=["index_name", "symbol", "as_of"])
    db.upsert_rows(con, "px_daily", [
        {"source": "NSE", "date": date(2026, 11, 9), "symbol": "BBB", "series": "EQ", "close": 500.0},
    ], keys=["source", "symbol", "date", "series"])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mcap09112026.csv", (
            "Trade Date,Symbol,Series,Security Name,Category,Last Trade Date,Face Value(Rs.),Issue Size,Close Price/Paid up value(Rs.),Market Cap(Rs.)\n"
            "09 NOV 2026,BBB,EQ,BBB LTD,Listed,09 NOV 2026,2.00,20000000,500.00,10000000000.00\n"
        ))
        z.writestr("pd09112026.csv", (
            "MKT,SERIES,SYMBOL,SECURITY,PREV_CL_PR,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,NET_TRDVAL,NET_TRDQTY,IND_SEC,CORP_IND,TRADES,HI_52_WK,LO_52_WK\n"
            "Y, , ,Nifty 50,24900,25000,25100,24800,25044.65,1000,100,Y, ,10,26000,22000\n"
        ))
    res = nse_mod.sync_nse_pr_mcap_from_zip_bytes(con, buf.getvalue(), date(2026, 11, 9), url="(test PR)")
    assert res["status"] == "ok" and res["rows"] == 1 and res["nifty50_synced"] is True

    ds = load_market_dataset_from_db(con)
    bbb = [r for r in ds["rows"] if r["nse_symbol"] == "BBB"][0]
    # 500 * 20,000,000 / 1e7 = 1000.0 Rs Cr
    assert bbb["market_cap"] == pytest.approx(1000.0)
    assert bbb["_provenance"]["shares_source"] == "NSE PR MCAP"

    # Check ordering: NIFTY100 (BBB) comes before NIFTY500 (CCC), then AAA
    ordered = own_mod.ordered_universe_symbols(con, "all")
    assert ordered == ["BBB", "CCC", "AAA"]

    # Check checkpoint/resume + immediate 403 abort
    db.mark_progress(con, "sync_shp", "BBB", "ok", "cached")
    called = []
    monkeypatch.setattr(own_mod, "bootstrap_nse_session", lambda: object())
    def fake_fetch(url, **kwargs):
        called.append(url)
        return FetchResult(403, None, url, error="http:403")
    monkeypatch.setattr(own_mod.http, "fetch", fake_fetch)

    batch_res = own_mod.sync_shp_batch(con, universe="all", resume=True)
    assert batch_res["skipped_resume"] == 1  # BBB skipped via ingest_progress
    assert batch_res["blocked"] is True      # aborted immediately on CCC 403
    assert len(called) == 1                  # did NOT hammer AAA after 403 on CCC
    con.close()

