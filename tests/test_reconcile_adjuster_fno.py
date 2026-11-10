"""tests/test_reconcile_adjuster_fno.py
Offline tests covering Phase 4.1, 4.2, and 4.3:
- Corporate actions split/bonus adjustment
- 10-stock exchange reconciliation (close, volume, market cap, F&O OI vs raw UDiFF files)
- Sector mapping via config/sector_map.yaml + SME master parsing
- F&O metrics engine (near/next/far expiries, FBIL MIBOR fair value vs missing, strikes, PCR, rollover)
"""
from __future__ import annotations

from datetime import date
import duckdb
import pytest

from app import db


@pytest.fixture()
def db_con(tmp_path):
    c = duckdb.connect(str(tmp_path / "test.duckdb"))
    db.init_schema(c)
    yield c
    c.close()
from ingest.adjuster import adjust_price_series, parse_action_factor
from ingest.fno_metrics import compute_fno_metrics_for_date
from ingest.master_enrichment import detect_financial_template, enrich_securities_from_constituents, map_industry_to_sector
from ingest.nse import _parse_sme_master, cm_bhav_from_bytes, fo_bhav_from_bytes, sync_index_list_from_bytes
from ingest.reconcile import reconcile_against_raw_files

UDIFF_HDR = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,"
    "XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,"
    "ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,"
    "TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4"
)

STOCKS_10 = [
    ("RELIANCE", "INE002A01018", 2420.50, 5000000, 6766000000),
    ("TCS", "INE467B01029", 3150.00, 2100000, 3618000000),
    ("HDFCBANK", "INE040A01034", 1450.00, 8400000, 7600000000),
    ("ICICIBANK", "INE090A01021", 930.00, 9100000, 7020000000),
    ("INFY", "INE009A01021", 1400.00, 4200000, 4150000000),
    ("HINDUNILVR", "INE030A01027", 2350.00, 1200000, 2349000000),
    ("ITC", "INE154A01025", 415.00, 11000000, 12480000000),
    ("SBIN", "INE062A01020", 560.00, 14500000, 8924000000),
    ("BHARTIARTL", "INE397D01024", 820.00, 3900000, 5690000000),
    ("LT", "INE018A01030", 2950.00, 1750000, 1374000000),
]


def _make_cm_csv(d_str="2026-10-23") -> bytes:
    lines = [UDIFF_HDR]
    for i, (sym, isin, px, vol, _shares) in enumerate(STOCKS_10):
        tval = round(px * vol, 2)
        lines.append(
            f"{d_str},{d_str},CM,NSE,STK,{100+i},{isin},{sym},EQ,,,,,"
            f"{sym} LTD,{px},{px+10},{px-10},{px},{px},{px-5},,,0,0,{vol},{tval},1000,F,1,,,,,"
        )
    return "\n".join(lines).encode()


def _make_fo_csv(d_str="2026-10-23", oi_scale: float = 1.0) -> bytes:
    lines = [UDIFF_HDR]
    # Include near/next/far STF + CE/PE STO rows for RELIANCE & TCS + STF for remaining 8
    for sym, isin, px, vol, _ in STOCKS_10:
        near_oi = int(1000000 * oi_scale)
        lines.append(
            f"{d_str},{d_str},FO,NSE,STF,5001,{isin},{sym},,2026-10-29,2026-10-29,,,"
            f"FUTSTK,{px},{px+5},{px-5},{px+10},{px+10},{px},{px},{px+10},{near_oi},5000,12000,1000000,400,F,500,,,,,"
        )
    # Add Next & Far futures + Options for RELIANCE
    lines.append(
        f"{d_str},{d_str},FO,NSE,STF,5002,INE002A01018,RELIANCE,,2026-11-26,2026-11-26,,,"
        f"FUTSTK,2440,2450,2430,2445,2445,2430,2420.5,2445,{int(300000*oi_scale)},10000,3000,500000,100,F,500,,,,,"
    )
    lines.append(
        f"{d_str},{d_str},FO,NSE,STF,5003,INE002A01018,RELIANCE,,2026-12-31,2026-12-31,,,"
        f"FUTSTK,2460,2470,2450,2465,2465,2450,2420.5,2465,{int(50000*oi_scale)},1000,500,100000,20,F,500,,,,,"
    )
    lines.append(
        f"{d_str},{d_str},FO,NSE,STO,6001,INE002A01018,RELIANCE,,2026-10-29,2026-10-29,2500,CE,"
        f"OPTSTK,45,48,40,42,42,40,2420.5,42,{int(800000*oi_scale)},20000,5000,200000,150,F,500,,,,,"
    )
    lines.append(
        f"{d_str},{d_str},FO,NSE,STO,6002,INE002A01018,RELIANCE,,2026-10-29,2026-10-29,2400,PE,"
        f"OPTSTK,35,38,30,32,32,30,2420.5,32,{int(960000*oi_scale)},15000,4500,150000,120,F,500,,,,,"
    )
    return "\n".join(lines).encode()


def test_corp_action_adjuster():
    assert parse_action_factor("Face Value Split (Sub-Division) - From Rs 10/- To Rs 2/-") == pytest.approx(0.2)
    assert parse_action_factor("Bonus 1:1") == pytest.approx(0.5)
    assert parse_action_factor("Dividend - Rs 4.50 Per Share") is None

    ohlcv = [
        {"date": date(2026, 1, 10), "open": 1000.0, "high": 1020.0, "low": 980.0, "close": 1000.0, "volume": 1000},
        {"date": date(2026, 1, 15), "open": 500.0, "high": 510.0, "low": 490.0, "close": 505.0, "volume": 2000},
    ]
    acts = [{"ex_date": date(2026, 1, 15), "purpose": "Bonus 1:1"}]
    adj = adjust_price_series(ohlcv, acts)
    assert adj[0]["close"] == 500.0
    assert adj[0]["volume"] == 2000
    assert adj[1]["close"] == 505.0  # on or after ex_date unadjusted


def test_reconcile_10_stocks_against_raw_files(db_con):
    cm_bytes = _make_cm_csv("2026-10-23")
    fo_bytes = _make_fo_csv("2026-10-23")

    # Seed ref_security with shares_outstanding
    secs = [
        {
            "security_id": isin,
            "isin": isin,
            "nse_symbol": sym,
            "name": f"{sym} LTD",
            "shares_outstanding": shares,
            "listing_status": "listed",
        }
        for sym, isin, _, _, shares in STOCKS_10
    ]
    db.upsert_rows(db_con, "ref_security", secs, keys=["security_id"])

    cm_bhav_from_bytes(db_con, cm_bytes, date(2026, 10, 23))
    fo_bhav_from_bytes(db_con, fo_bytes, date(2026, 10, 23))

    rep = reconcile_against_raw_files(
        db_con,
        cm_bhav_bytes=cm_bytes,
        fo_bhav_bytes=fo_bytes,
        source="NSE",
        min_stocks=10,
    )
    assert rep.stocks_checked == 10
    assert rep.passed == 10
    assert rep.failed == 0
    assert rep.ok

    # Introduce synthetic mismatch on one stock in DB and confirm reconciliation catches it
    db_con.execute("UPDATE px_daily SET close = 9999.0 WHERE symbol = 'RELIANCE'")
    rep_bad = reconcile_against_raw_files(db_con, cm_bhav_bytes=cm_bytes, fo_bhav_bytes=fo_bytes, min_stocks=10)
    assert rep_bad.failed == 1
    assert any(d.symbol == "RELIANCE" and d.field == "close_price" for d in rep_bad.discrepancies)


def test_sme_master_and_sector_enrichment(db_con):
    sme_csv = "\n".join([
        "SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE",
        "THEJO,Thejo Engineering Limited,SM,18-SEP-2012,10,300,INE121N01019,10",
    ]).encode()
    sme_rows = _parse_sme_master(sme_csv)
    assert sme_rows[0]["is_sme"] is True
    assert sme_rows[0]["nse_symbol"] == "THEJO"

    idx_csv = "\n".join([
        "Company Name,Industry,Symbol,Series,ISIN Code",
        "HDFC Bank Ltd,Financial Services,HDFCBANK,EQ,INE040A01034",
        "State Bank of India,Banks,SBIN,EQ,INE062A01020",
        "Reliance Industries Ltd,Oil & Gas,RELIANCE,EQ,INE002A01018",
    ]).encode()
    db.upsert_rows(db_con, "ref_security", [
        {"security_id": "INE040A01034", "nse_symbol": "HDFCBANK", "name": "HDFC Bank"},
        {"security_id": "INE062A01020", "nse_symbol": "SBIN", "name": "SBI"},
        {"security_id": "INE002A01018", "nse_symbol": "RELIANCE", "name": "Reliance"},
        {"security_id": "INF204KB14I2", "nse_symbol": "NIFTYBEES", "name": "Nifty BeES", "is_etf": True},
    ], keys=["security_id"])
    res_idx = sync_index_list_from_bytes(db_con, idx_csv, filename_hint="ind_nifty50list.csv")
    assert res_idx["index_name"] == "NIFTY50"

    enrich_securities_from_constituents(db_con)
    sec_rows = db_con.execute(
        "SELECT nse_symbol, sector, is_financial_institution, financial_template FROM ref_security"
    ).fetchall()
    by_s = {r[0]: r for r in sec_rows}
    assert by_s["RELIANCE"][1] == "Energy"
    assert by_s["SBIN"][2] is True and by_s["SBIN"][3] == "banks"
    assert by_s["NIFTYBEES"][1] == "ETF"
    assert map_industry_to_sector("Healthcare") == "Health Care"
    assert detect_financial_template("Insurance", "Financials") == (True, "insurers")


def test_fno_derived_metrics_with_and_without_mibor(db_con):
    cm_1 = _make_cm_csv("2026-10-22")
    fo_1 = _make_fo_csv("2026-10-22", oi_scale=1.0)
    cm_2 = _make_cm_csv("2026-10-23")
    fo_2 = _make_fo_csv("2026-10-23", oi_scale=1.2)

    cm_bhav_from_bytes(db_con, cm_1, date(2026, 10, 22))
    fo_bhav_from_bytes(db_con, fo_1, date(2026, 10, 22))
    cm_bhav_from_bytes(db_con, cm_2, date(2026, 10, 23))
    fo_bhav_from_bytes(db_con, fo_2, date(2026, 10, 23))

    # 1. Without FBIL MIBOR: fair_value must be NULL and flagged Unavailable
    res_no_mibor = compute_fno_metrics_for_date(db_con, date(2026, 10, 23))
    assert res_no_mibor["rows"] == 10
    row_rel = db_con.execute(
        """
        SELECT basis, fair_value, rollover_cost, percentage_rollover, calendar_spread,
               put_call_ratio, chg_1d_future_oi, highest_call_oi_strike, highest_put_oi_strike,
               highest_1d_oi_chg_ce_strike, fair_value_status
        FROM fno_metrics_daily WHERE underlying = 'RELIANCE' AND date = '2026-10-23'
        """
    ).fetchone()
    basis, fv, rc, pct_ro, cal_sp, pcr, chg_1d_foi, hi_ce, hi_pe, hi_1d_ce, fv_status = row_rel
    assert basis == pytest.approx(10.0)  # fut 2430.5 - spot 2420.5
    assert fv is None
    assert "Unavailable" in fv_status
    # Next fut = 2445, Near fut = 2430.5
    assert rc == pytest.approx((2445.0 / 2430.5 - 1.0) * 100.0, rel=1e-4)
    # OI next=360k, near=1.2M, far=60k -> 360k / 1.62M * 100 = 22.222%
    assert pct_ro == pytest.approx(360000.0 / 1620000.0 * 100.0, rel=1e-4)
    assert cal_sp == pytest.approx(2445.0 - 2430.5)
    assert pcr == pytest.approx(960000.0 / 800000.0)  # 1.2
    assert chg_1d_foi == pytest.approx(20.0)
    assert hi_ce == 2500.0
    assert hi_pe == 2400.0
    assert hi_1d_ce == 2500.0

    # 2. With FBIL MIBOR 6.50%: fair value computes cleanly
    db.upsert_rows(db_con, "ref_fbil_mibor", [{
        "rate_date": date(2026, 10, 23),
        "tenor": "mibor_3m",
        "rate_pct": 6.50,
    }], keys=["rate_date", "tenor"])
    compute_fno_metrics_for_date(db_con, date(2026, 10, 23))
    fv_after = db_con.execute(
        "SELECT fair_value, fair_value_status FROM fno_metrics_daily WHERE underlying = 'RELIANCE' AND date = '2026-10-23'"
    ).fetchone()
    # 6 days to expiry (Oct 23 -> Oct 29)
    assert fv_after[0] == pytest.approx(2420.5 * (1.0 + 0.065 * 6.0 / 365.0), rel=1e-6)
    assert fv_after[1] == "computed"
