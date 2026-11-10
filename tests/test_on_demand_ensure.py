"""tests/test_on_demand_ensure.py
Comprehensive offline tests for:
- On-demand filter capability resolution & dependency planning
- Immediate derived recomputation (technicals / snapshot rebuild) from existing raw DB rows
- Single-flight job deduplication, DuckDB persistence, and 403 block handling
- Instrument & sector eligibility filtering in /api/coverage
- Legacy pre-Jul-2024 CM bhavcopy parser & URL routing
- Quarterly non-pollution in Ind-AS XBRL + expanded tag extraction
- ETF master SECURITYNAME fix & honest provider health/cadence reporting
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import duckdb
import pytest
from fastapi import HTTPException

from app import config, db
from app.api.routes import get_coverage, get_data_job_status, get_data_jobs, get_providers
from app.jobs.ensure_manager import ensure_filters, get_job, rebuild_all
from ingest import backfill, http
from ingest.nse import _parse_etf_master, sync_etf_master_from_bytes
from ingest.udiff import parse_udiff
from ingest.xbrl import parse_indas_xbrl


class _FakeFetch:
    def __init__(self, status: int | None, data: bytes | None = None, error: str | None = None):
        self.status = status
        self.bytes = data
        self.url = "https://mock.nse.local/test"
        self.saved_path = None
        self.error = error

    def ok(self) -> bool:
        return self.status == 200 and self.bytes is not None

    def blocked(self) -> bool:
        return self.status in (403, 429)


def _setup_tmp_db(tmp_path: Path, monkeypatch) -> Path:
    db_file = tmp_path / "ensure_test.db"
    monkeypatch.setattr(config, "data_path", lambda rel: db_file if rel.endswith(".db") else (tmp_path / rel))
    con = duckdb.connect(str(db_file))
    db.init_schema(con)
    con.close()
    return db_file


def test_unavailable_and_not_applicable_filters(tmp_path, monkeypatch):
    db_file = _setup_tmp_db(tmp_path, monkeypatch)
    con = duckdb.connect(str(db_file))
    as_of = date(2026, 11, 9)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE01", "isin": "INE01", "nse_symbol": "CASHO", "name": "Cash Only Ltd", "sector": "Industrials", "fno_eligible": False, "is_etf": False, "shares_outstanding": 1000000},
    ], keys=["security_id"])
    db.upsert_rows(con, "px_daily", [
        {"date": as_of, "symbol": "CASHO", "source": "NSE", "series": "EQ", "close": 100.0},
    ], keys=["date", "symbol", "source", "series"])
    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "CASHONLY", "symbol": "CASHO", "as_of": as_of},
    ], keys=["index_name", "symbol", "as_of"])
    con.close()
    rebuild_all()

    res = ensure_filters(["percentage_upside", "put_call_ratio", "expense_ratio", "net_loans"], universe="CASHONLY")
    by_fid = {r["filter_id"]: r for r in res["filters"]}
    assert by_fid["percentage_upside"]["state"] == "unavailable"
    assert by_fid["put_call_ratio"]["state"] == "not_applicable"
    assert by_fid["expense_ratio"]["state"] == "not_applicable"
    assert by_fid["net_loans"]["state"] == "not_applicable"
    assert res["jobs"] == []


def test_immediate_derived_recompute_and_auto_refresh(tmp_path, monkeypatch):
    db_file = _setup_tmp_db(tmp_path, monkeypatch)
    con = duckdb.connect(str(db_file))
    base_d = date(2026, 10, 1)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE01", "isin": "INE01", "nse_symbol": "TECHCO", "name": "Tech Co", "sector": "Information Technology", "shares_outstanding": 1000000},
    ], keys=["security_id"])
    # Seed 22 trading days raw px_daily WITHOUT computing tech_daily yet
    px_rows = []
    for i in range(22):
        d = base_d + timedelta(days=i)
        c = 100.0 + i * 1.5
        px_rows.append({
            "date": d,
            "symbol": "TECHCO",
            "source": "NSE",
            "series": "EQ",
            "open": c - 1.0,
            "high": c + 1.0,
            "low": c - 1.5,
            "close": c,
            "prev_close": c - 1.5,
            "volume": 10000 + i * 100,
        })
    db.upsert_rows(con, "px_daily", px_rows, keys=["date", "symbol", "source", "series"])
    con.close()

    # Build initial snapshot before technicals exist -> rsi_14d is null in snapshot
    from app.query.snapshot import build_screener_snapshot, load_snapshot_from_db
    s1 = build_screener_snapshot()
    v1 = s1["version"]
    snap_before = load_snapshot_from_db()
    assert snap_before["rows"][0].get("rsi_14d") is None
    cov_before = get_coverage()
    assert cov_before["by_id"]["sma_200d"]["status"] == "insufficient_history"
    assert cov_before["by_id"]["sma_200d"]["min_history_days"] == 200

    # Checking rsi_14d must compute tech_daily immediately without hitting network and bump snapshot version!
    monkeypatch.setattr("app.jobs.ensure_manager._EXECUTOR.submit", lambda *a, **k: None)
    ensure_res = ensure_filters(["rsi_14d", "sma_200d"])
    assert ensure_res["recomputed"] is True
    assert ensure_res["snapshot_version"] > v1

    snap_after = load_snapshot_from_db()
    assert snap_after["rows"][0].get("rsi_14d") is not None
    cov = get_coverage()
    assert cov["by_id"]["rsi_14d"]["status"] == "available"
    assert cov["by_id"]["sma_200d"]["status"] == "queued"


def test_job_dedup_persistence_and_403_handling(tmp_path, monkeypatch):
    db_file = _setup_tmp_db(tmp_path, monkeypatch)
    con = duckdb.connect(str(db_file))
    as_of = date(2026, 11, 9)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE01", "isin": "INE01", "nse_symbol": "AAA", "name": "AAA Co", "sector": "Energy"},
    ], keys=["security_id"])
    db.upsert_rows(con, "ref_index_constituent", [
        {"index_name": "NIFTY100", "symbol": "AAA", "as_of": as_of},
    ], keys=["index_name", "symbol", "as_of"])
    con.close()
    rebuild_all()

    # Patch background executor submit to keep job in queued state for dedup assertion first
    submitted = []
    monkeypatch.setattr("app.jobs.ensure_manager._EXECUTOR.submit", lambda *a, **k: submitted.append((a, k)))

    r1 = ensure_filters(["return_on_equity"], universe="NIFTY100")
    assert len(r1["jobs"]) == 1
    jid = r1["jobs"][0]["job_id"]

    # Second call with another xbrl filter in same universe must reuse exact same job_id!
    r2 = ensure_filters(["pe_ratio"], universe="NIFTY100")
    assert len(r2["jobs"]) == 1
    assert r2["jobs"][0]["job_id"] == jid
    assert get_job(jid)["sync_job"] == "xbrl_financials"

    # Now verify synchronous 403 block handling using backfill mock
    monkeypatch.setattr(http, "fetch", lambda *a, **k: _FakeFetch(403, error="http:403"))
    con2 = duckdb.connect(str(db_file))
    con2.execute("DELETE FROM data_jobs")
    con2.close()

    res_blk = ensure_filters(["1y_return"], universe="NIFTY100", wait=True)
    assert res_blk["jobs"][0]["status"] == "blocked"
    assert "403" in (res_blk["jobs"][0]["error"] or "")

    jobs_resp = get_data_jobs()
    assert any(j["status"] == "blocked" for j in jobs_resp["jobs"])
    assert get_data_job_status(res_blk["jobs"][0]["job_id"])["status"] == "blocked"
    with pytest.raises(HTTPException) as exc_info:
        get_data_job_status("nonexistent_id")
    assert exc_info.value.status_code == 404


def test_legacy_cm_bhavcopy_and_routing():
    csv_legacy = (
        "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,\n"
        "RELIANCE,EQ,3100,3150,3080,3125.5,3124,3105,5000000,15627500000,01-JUL-2024,180000,INE002A01018,\n"
    ).encode("utf-8")
    parsed = parse_udiff(csv_legacy, source="NSE", series_keep=["EQ"])
    assert len(parsed["px_rows"]) == 1
    row = parsed["px_rows"][0]
    assert row["symbol"] == "RELIANCE"
    assert row["date"] == date(2024, 7, 1)
    assert row["close"] == 3125.5
    assert row["wap"] == round(15627500000 / 5000000, 4)

    eps = {"nse_cm_bhavcopy": {"url_pattern": "https://ex/udiff_{yyyymmdd}.zip"}}
    leg_url, leg_name = backfill._cm_url_and_save_name(eps, date(2024, 7, 1))
    udf_url, _ = backfill._cm_url_and_save_name(eps, date(2024, 7, 8))
    assert "cm01JUL2024bhav.csv.zip" in leg_url
    assert leg_name == "cm01JUL2024bhav.csv.zip"
    assert udf_url == "https://ex/udiff_20240708.zip"


def test_xbrl_quarterly_non_pollution_and_indas_tags():
    q_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <xbrl xmlns="http://www.xbrl.org/2003/instance">
      <Symbol>TESTCO</Symbol>
      <ReportingQuarter>Half yearly</ReportingQuarter>
      <DateOfStartOfReportingPeriod>2025-04-01</DateOfStartOfReportingPeriod>
      <DateOfEndOfReportingPeriod>2025-09-30</DateOfEndOfReportingPeriod>
      <RevenueFromOperations contextRef="OneD">25000000000</RevenueFromOperations>
      <ProfitLossForPeriod contextRef="OneD">3000000000</ProfitLossForPeriod>
      <BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations contextRef="OneD">12.5</BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations>
      <Assets contextRef="OneI">100000000000</Assets>
    </xbrl>"""
    p_q = parse_indas_xbrl(q_xml, symbol="TESTCO", report_period="Quarterly")
    assert p_q["annual"] is None
    assert p_q["quarterly"] is not None
    assert p_q["quarterly"]["eps_q"] == 12.5

    ann_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <xbrl xmlns="http://www.xbrl.org/2003/instance">
      <Symbol>TESTCO</Symbol>
      <ReportingQuarter>Yearly</ReportingQuarter>
      <DateOfEndOfReportingPeriod>2026-03-31</DateOfEndOfReportingPeriod>
      <RevenueFromOperations contextRef="FourD">100000000000</RevenueFromOperations>
      <ProfitLossForPeriod contextRef="FourD">10000000000</ProfitLossForPeriod>
      <BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations contextRef="FourD">50.0</BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations>
      <CashAndCashEquivalents contextRef="OneI">4000000000</CashAndCashEquivalents>
      <BankBalanceOtherThanCashAndCashEquivalents contextRef="OneI">6000000000</BankBalanceOtherThanCashAndCashEquivalents>
      <TradeReceivablesCurrent contextRef="OneI">8000000000</TradeReceivablesCurrent>
      <TradeReceivablesNoncurrent contextRef="OneI">2000000000</TradeReceivablesNoncurrent>
      <TradePayablesCurrent contextRef="OneI">5000000000</TradePayablesCurrent>
      <BorrowingsNoncurrent contextRef="OneI">20000000000</BorrowingsNoncurrent>
      <Assets contextRef="OneI">120000000000</Assets>
      <Liabilities contextRef="OneI">50000000000</Liabilities>
      <Equity contextRef="OneI">70000000000</Equity>
      <PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities contextRef="FourD">3000000000</PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities>
      <DividendsPaidClassifiedAsFinancingActivities contextRef="FourD">1500000000</DividendsPaidClassifiedAsFinancingActivities>
    </xbrl>"""
    p_ann = parse_indas_xbrl(ann_xml, symbol="TESTCO", report_period="Annual")
    ann = p_ann["annual"]
    assert ann is not None
    assert ann["cash_and_st_inv"] == 1000.0
    assert ann["total_receivables"] == 1000.0
    assert ann["accounts_payable"] == 500.0
    assert ann["total_long_term_debt"] == 2000.0
    assert ann["capex"] == 300.0
    assert ann["dividends_paid"] == 150.0


def test_etf_master_security_name_and_providers_endpoint(tmp_path, monkeypatch):
    _setup_tmp_db(tmp_path, monkeypatch)
    csv_etf = (
        "Symbol,Underlying Asset,SecurityName,DateofListing,MarketLot,ISINNumber,FaceValue,ETF Underlying,Underlying Key\n"
        "NIFTYBEES,Nifty 50,NIPINDETFNIFTYBEES,08-Jan-02,1,INF204KB14I2,1,EQUITY,Nifty 50\n"
    ).encode("utf-8")
    rows = _parse_etf_master(csv_etf)
    assert rows[0]["name"] == "NIPINDETFNIFTYBEES"
    assert rows[0]["isin"] == "INF204KB14I2"
    assert rows[0]["face_value"] == 1.0

    con = db.connect()
    res = sync_etf_master_from_bytes(con, csv_etf)
    assert res["rows"] == 1
    meta = con.execute("SELECT benchmark_index FROM etf_meta WHERE symbol = 'NIFTYBEES'").fetchone()
    assert meta[0] == "Nifty 50"
    con.close()

    prov = get_providers()
    assert prov["active_quote_provider"] == "nse_official_eod"
    assert prov["is_realtime_active"] is False
    ids = {p["provider_id"]: p for p in prov["providers"]}
    assert ids["groww_live_api"]["status"] == "unconfigured"
    assert ids["nse_live_vendor"]["status"] == "unconfigured"


def test_bse_master_merge_preserves_nse_fields(tmp_path, monkeypatch):
    from ingest.bse import sync_master_from_bhavcopy
    _setup_tmp_db(tmp_path, monkeypatch)
    con = db.connect()
    db.merge_rows(con, "ref_security", [{
        "security_id": "INE002A01018",
        "isin": "INE002A01018",
        "nse_symbol": "RELIANCE",
        "name": "Reliance Industries Limited",
        "sector": "Energy",
        "shares_outstanding": 6766000000,
        "fno_eligible": True,
        "listing_status": "listed",
    }], keys=["security_id"])

    bse_csv = (
        "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,"
        "FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,"
        "LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,"
        "TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4\n"
        "2026-11-09,2026-11-09,CM,BSE,STK,500325,INE002A01018,RELIANCE,A,,,,,RELIANCE INDUST,"
        "1200,1210,1190,1205,1205,1200,,,0,0,1000,1205000,10,,,,,0,,\n"
    ).encode("utf-8")
    res = sync_master_from_bhavcopy(con, payload=bse_csv)
    assert res["rows"] == 1
    row = con.execute(
        "SELECT nse_symbol, bse_code, name, sector, shares_outstanding, fno_eligible FROM ref_security WHERE security_id = 'INE002A01018'"
    ).fetchone()
    assert row == ("RELIANCE", "500325", "Reliance Industries Limited", "Energy", 6766000000, True)
    con.close()
