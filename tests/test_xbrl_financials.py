"""tests/test_xbrl_financials.py
Offline tests for Step 4.5: Ind-AS XBRL parsing, unit conversion (raw INR -> Rs Cr),
sector templates (industrials, banks), consolidated-first selection with standalone fallback,
and Balance Sheet Integrity Quarantine.
"""
from __future__ import annotations

from datetime import date
import duckdb
import pytest

from app import db
from ingest.financials import compute_fundamental_metrics, ingest_financial_xbrl_bytes


@pytest.fixture()
def db_con(tmp_path):
    c = duckdb.connect(str(tmp_path / "fin.duckdb"))
    db.init_schema(c)
    yield c
    c.close()


def _indas_xml(symbol: str, period_end: str, stmt_type: str, rev_inr: float, net_inc_inr: float, assets_inr: float, liab_inr: float, eq_inr: float, is_bank: bool = False) -> bytes:
    bank_tags = ""
    if is_bank:
        bank_tags = f"""
        <InterestEarned contextRef="FourD">{rev_inr}</InterestEarned>
        <InterestExpended contextRef="FourD">{rev_inr * 0.4}</InterestExpended>
        <ProvisionsAndContingencies contextRef="FourD">20000000000</ProvisionsAndContingencies>
        <GrossAdvances contextRef="OneI">1000000000000</GrossAdvances>
        <NPAProvisions contextRef="OneI">20000000000</NPAProvisions>
        <Deposits contextRef="OneI">1500000000000</Deposits>
        """
    else:
        bank_tags = f"""
        <RevenueFromOperations contextRef="FourD">{rev_inr}</RevenueFromOperations>
        <CostOfMaterialsConsumed contextRef="FourD">{rev_inr * 0.5}</CostOfMaterialsConsumed>
        <Inventories contextRef="OneI">5000000000</Inventories>
        """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance">
  <Symbol>{symbol}</Symbol>
  <NatureOfReportStandaloneConsolidated>{stmt_type}</NatureOfReportStandaloneConsolidated>
  <DateOfEndOfReportingPeriod>{period_end}</DateOfEndOfReportingPeriod>
  {bank_tags}
  <EmployeeBenefitExpense contextRef="FourD">{rev_inr * 0.1}</EmployeeBenefitExpense>
  <DepreciationDepletionAndAmortisationExpense contextRef="FourD">{rev_inr * 0.05}</DepreciationDepletionAndAmortisationExpense>
  <FinanceCosts contextRef="FourD">{rev_inr * 0.04}</FinanceCosts>
  <ProfitBeforeTax contextRef="FourD">{net_inc_inr * 1.25}</ProfitBeforeTax>
  <TaxExpense contextRef="FourD">{net_inc_inr * 0.25}</TaxExpense>
  <ProfitLossForPeriod contextRef="FourD">{net_inc_inr}</ProfitLossForPeriod>
  <BasicEarningsPerShare contextRef="FourD">30.0</BasicEarningsPerShare>
  <PaidUpValueOfEquityShareCapital contextRef="OneI">10000000000</PaidUpValueOfEquityShareCapital>
  <FaceValueOfEquityShareCapital contextRef="OneI">10</FaceValueOfEquityShareCapital>
  <CurrentAssets contextRef="OneI">25000000000</CurrentAssets>
  <CurrentLiabilities contextRef="OneI">30000000000</CurrentLiabilities>
  <Assets contextRef="OneI">{assets_inr}</Assets>
  <Liabilities contextRef="OneI">{liab_inr}</Liabilities>
  <Equity contextRef="OneI">{eq_inr}</Equity>
  <LongTermBorrowings contextRef="OneI">10000000000</LongTermBorrowings>
  <CashAndCashEquivalents contextRef="OneI">5000000000</CashAndCashEquivalents>
  <NetCashFlowsFromUsedInOperatingActivities contextRef="FourD">{net_inc_inr * 1.1}</NetCashFlowsFromUsedInOperatingActivities>
  <PurchaseOfPropertyPlantAndEquipment contextRef="FourD">{net_inc_inr * 0.3}</PurchaseOfPropertyPlantAndEquipment>
</xbrl>""".encode()


def test_industrial_xbrl_consolidated_preferred_and_ratios(db_con):
    # FY0 consolidated + standalone; consolidated must win!
    # 10,000 Cr = 1e11 INR; 1,000 Cr net income; 12,000 Cr assets = 5,000 Cr Liab + 7,000 Cr Eq
    xml_con = _indas_xml("RELIANCE", "2026-03-31", "Consolidated", 1e11, 1e10, 1.2e11, 5e10, 7e10)
    xml_sa = _indas_xml("RELIANCE", "2026-03-31", "Standalone", 0.8e11, 0.8e10, 1.0e11, 4e10, 6e10)
    xml_con_prev = _indas_xml("RELIANCE", "2025-03-31", "Consolidated", 0.9e11, 0.8e10, 1.1e11, 5e10, 6e10)

    ingest_financial_xbrl_bytes(db_con, xml_sa, symbol="RELIANCE")
    ingest_financial_xbrl_bytes(db_con, xml_con, symbol="RELIANCE")
    ingest_financial_xbrl_bytes(db_con, xml_con_prev, symbol="RELIANCE")

    m = compute_fundamental_metrics(db_con, "RELIANCE", close_price=300.0, shares_outstanding=1_000_000_000)
    assert m["statement_type_used"] == "consolidated"
    assert m["total_revenue"] == pytest.approx(10000.0)
    assert m["net_income"] == pytest.approx(1000.0)
    assert m["pe_ratio"] == pytest.approx(10.0)  # 300 / EPS 30.0
    # Quick Ratio: (CA 2500 Cr - Inv 500 Cr) / CL 3000 Cr = 0.6667
    assert m["quick_ratio"] == pytest.approx(0.6667, rel=1e-3)
    # 1Y Rev growth: (10000 / 9000 - 1)*100 = +11.11%
    assert m["1y_historical_revenue_growth"] == pytest.approx(11.1111, rel=1e-3)


def test_bank_template_excludes_irrelevant_ratios_and_computes_net_loans(db_con):
    db.upsert_rows(db_con, "ref_security", [{
        "security_id": "INE040BANK",
        "nse_symbol": "TESTBANK",
        "name": "Test Bank",
        "sector": "Financials",
        "is_financial_institution": True,
        "financial_template": "banks",
    }], keys=["security_id"])

    # Standalone only -> fallback sets statement_type_used == 'standalone'
    # Gross advances 100,000 Cr (1e12 INR) - NPA 2,000 Cr (2e10 INR) = 98,000 Cr net loans!
    xml_bank = _indas_xml("TESTBANK", "2026-03-31", "Standalone", 1e11, 2e10, 2e12, 1.8e12, 0.2e12, is_bank=True)
    ingest_financial_xbrl_bytes(db_con, xml_bank, symbol="TESTBANK", template_type="banks")

    m = compute_fundamental_metrics(db_con, "TESTBANK", close_price=500.0, shares_outstanding=1_000_000_000, is_financial_institution=True)
    assert m["statement_type_used"] == "standalone"
    assert m["net_loans"] == pytest.approx(98000.0)
    assert m["cost_of_goods_sold"] is None
    assert m["current_ratio"] is None
    assert m["quick_ratio"] is None
    assert m["debt_to_equity"] is None


def test_balance_sheet_integrity_quarantine(db_con):
    # Deliberately broken BS: Assets = 12,000 Cr, Liab = 5,000 Cr, Eq = 5,000 Cr (2,000 Cr off!)
    xml_bad = _indas_xml("BROKENCORP", "2026-03-31", "Consolidated", 1e11, 1e10, 1.2e11, 5e10, 5e10)
    res = ingest_financial_xbrl_bytes(db_con, xml_bad, symbol="BROKENCORP")
    assert res["status"] == "quarantined"
    assert db_con.execute("SELECT count(*) FROM fin_annual WHERE symbol = 'BROKENCORP'").fetchone()[0] == 0
    q_row = db_con.execute("SELECT symbol, diff FROM fin_quarantine WHERE symbol = 'BROKENCORP'").fetchone()
    assert q_row[0] == "BROKENCORP" and q_row[1] == pytest.approx(2000.0)


def test_targeted_quarterly_sync_checkpoint_resume_and_403_abort(db_con, monkeypatch):
    from ingest import sources, ownership as own_mod, financials as fin_mod
    from ingest.http import FetchResult
    import ingest.http as http_mod
    import json as _json

    db.upsert_rows(db_con, "ref_security", [
        {"security_id": "INE1", "isin": "INE1", "nse_symbol": "AAA", "name": "AAA"},
        {"security_id": "INE2", "isin": "INE2", "nse_symbol": "BBB", "name": "BBB"},
        {"security_id": "INE3", "isin": "INE3", "nse_symbol": "CCC", "name": "CCC"},
    ], keys=["security_id"])
    db.upsert_rows(db_con, "ref_index_constituent", [
        {"index_name": "NIFTY100", "symbol": "CCC", "as_of": date(2026, 11, 10)},
        {"index_name": "NIFTY100", "symbol": "AAA", "as_of": date(2026, 11, 10)},
    ], keys=["index_name", "symbol", "as_of"])

    db.mark_progress(db_con, "quarterly", "AAA", "ok", "already synced")
    called_urls = []
    xml_ok = _indas_xml("CCC", "2026-03-31", "Consolidated", 1e11, 1e10, 5e11, 2e11, 3e11)

    def fake_fetch(url, **kwargs):
        called_urls.append(url)
        if "corporate-share-holdings-master" in url and "symbol=CCC" in url:
            return FetchResult(200, _json.dumps([
                {"date": "2026-09-30", "xbrl": "https://xbrl.test/shp_ccc_3.xml"},
                {"date": "2026-06-30", "xbrl": "https://xbrl.test/shp_ccc_2.xml"},
                {"date": "2026-03-31", "xbrl": "https://xbrl.test/shp_ccc_1.xml"},
                {"date": "2025-12-31", "xbrl": "https://xbrl.test/shp_ccc_0.xml"},
            ]).encode(), url)
        if "shp_ccc_" in url:
            shp_xml = b'<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"><ShareholdingOfPromoterAndPromoterGroup_ContextI><ShareholdingAsAPercentageOfTotalNumberOfShares>0.51</ShareholdingAsAPercentageOfTotalNumberOfShares></ShareholdingOfPromoterAndPromoterGroup_ContextI></xbrli:xbrl>'
            return FetchResult(200, shp_xml, url)
        if "corporates-financial-results" in url and "symbol=CCC" in url:
            if "period=Annual" in url:
                return FetchResult(200, _json.dumps([{"toDate": "2026-03-31", "consolidated": "Consolidated", "xbrl": "https://xbrl.test/fin_ccc.xml"}]).encode(), url)
            return FetchResult(200, b"[]", url)
        if "fin_ccc.xml" in url:
            return FetchResult(200, xml_ok, url)
        if "symbol=BBB" in url:
            return FetchResult(403, None, url, error="http:403")
        return FetchResult(404, None, url, error="http:404")

    monkeypatch.setattr(http_mod, "bootstrap_nse_session", lambda: object())
    monkeypatch.setattr(own_mod, "bootstrap_nse_session", lambda: object())
    monkeypatch.setattr(fin_mod, "bootstrap_nse_session", lambda: object())
    monkeypatch.setattr(http_mod, "fetch", fake_fetch)

    # Mark quarterly resume checkpoint skip + limit to NIFTY100 -> skips AAA, runs CCC (max_quarters=3 -> only 3 shp_ccc calls!), then stops cleanly
    res = sources.run_quarterly(db_con, universe="nifty100", resume=True)
    assert res["skipped_resume"] == 1
    assert res["shp_synced"] == 1
    assert res["fin_synced"] == 1
    shp_fetches = [u for u in called_urls if "shp_ccc_" in u]
    assert len(shp_fetches) == 3  # fetched 3 quarters for 6M delta, ignoring 4th!

    # Now test universe='all' hitting BBB -> stops immediately on 403
    res_all = sources.run_quarterly(db_con, universe="all", resume=True)
    assert res_all["blocked"] is True and res_all["status"] == "partial"

