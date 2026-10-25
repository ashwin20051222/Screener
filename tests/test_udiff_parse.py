"""UDiFF parser tests - fixtures capture the EXACT 34-column layout verified live 2026-10-25
(NSE CM 3,730 rows, NSE FO 40,212 rows, BSE CM plain CSV; identical header layout)."""
from __future__ import annotations

import textwrap
import zipfile
import io

from ingest.udiff import parse_udiff, read_bhav_bytes

HEADER = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,"
    "FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,"
    "LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,"
    "TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4"
)


def _cm_rows() -> str:
    # EQ row mirrors the live 20MICRONS row of 2026-10-23; GB row proves series filtering; a graded row without price skipped
    return "\n".join([
        HEADER,
        "2026-10-23,2026-10-23,CM,NSE,STK,16921,INE144J01027,20MICRONS,EQ,,,,,20 MICRONS LTD,178.25,179.20,170.05,174.94,175.00,178.03,,174.95,,,184221,31991242.29,4966,F1,1,,,,,",
        "2026-10-23,2026-10-23,CM,NSE,STK,19078,IN0020200104,SGBJUN28,GB,,,,,2.5%GOLDBONDS2028SR-III,14100.00,14100.00,13998.30,14004.25,14005.00,14250.00,,14004.25,,,568,7960173.43,65,F1,1,,,,,",
        "2026-10-23,2026-10-23,CM,NSE,STK,1234,,X,EQ,,,,,NO PRICE ROW,0.00,0.00,0.00,,,,,,0,0,0,F1,1,,,,,",
    ])


def _fo_rows() -> str:
    # FO layout (verified live): ISIN empty, symbol in TckrSymb, SctySrs empty,
    # XpryDt + StrkPric + OptnTp populated; futures have empty OptnTp.
    return "\n".join([
        HEADER,
        "2026-10-23,2026-10-23,FO,NSE,STF,67129,,ABCAPITAL,,2026-11-27,2026-11-27,0.00,,ABCAPITAL26NOVFUT,270.00,272.00,268.10,271.45,271.40,269.00,271.40,271.45,3383000,0,14219210,0.00,10284,F1,3100,,,,,",
        "2026-10-23,2026-10-23,FO,NSE,STO,67129,,ABCAPITAL,,2026-10-27,2026-10-27,425.00,PE,ABCAPITAL26OCT425PE,0.00,0.00,0.00,38.35,38.35,38.35,347.25,77.48,12400,0,0,0.00,0,F1,3100,,,,,",
        "2026-10-23,2026-10-23,FO,NSE,STO,67129,,ABCAPITAL,,2026-10-27,2026-10-27,430.00,CE,ABCAPITAL26OCT430CE,5.00,6.00,3.50,4.25,4.20,3.90,347.25,4.30,915000,85000,5000,0.00,175,F1,3100,,,,,",
    ])


def _zip(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("BhavCopy_NSE_CM_0_0_0_TEST_F_0000.csv", text)
    return buf.getvalue()


def test_cm_parses_and_filters_series():
    res = parse_udiff(_zip(_cm_rows()), source="NSE", series_keep=["EQ"])
    assert len(res["px_rows"]) == 1, res["px_rows"]
    row = res["px_rows"][0]
    assert row["symbol"] == "20MICRONS"
    assert row["isin"] == "INE144J01027"
    assert row["series"] == "EQ"
    assert row["date"].isoformat() == "2026-10-23"
    assert row["close"] == 174.94
    assert row["prev_close"] == 178.03
    assert res["skipped"] == 2  # GB row filtered + no-price row
    # derived day VWAP = turnover / volume (mission 7.5)
    assert abs(row["wap"] - 31991242.29 / 184221) < 0.01


def test_cm_keeps_all_series_when_unfiltered():
    res = parse_udiff(_zip(_cm_rows()), source="NSE", series_keep=None)
    assert {r["series"] for r in res["px_rows"]} == {"EQ", "GB"}
    assert res["skipped"] == 1


def test_fo_parses_futures_and_options():
    res = parse_udiff(_zip(_fo_rows()), source="NSE", fo_mode=True)
    assert len(res["fno_rows"]) == 3
    fut = next(r for r in res["fno_rows"] if r["instrument"] == "STF")
    assert fut["expiry"].isoformat() == "2026-11-27"
    assert fut["oi"] == 3383000
    assert fut["close"] == 271.45
    pe = next(r for r in res["fno_rows"] if r["option_type"] == "PE")
    assert pe["strike"] == 425.0
    assert pe["oi"] == 12400
    ce = next(r for r in res["fno_rows"] if r["option_type"] == "CE")
    assert ce["oi_change"] == 85000


def test_plain_csv_bse_layout():
    res = parse_udiff(_cm_rows(), source="BSE", series_keep=None)
    assert len(res["px_rows"]) == 2
    assert any(r["symbol"] == "SGBJUN28" for r in res["px_rows"])


def test_required_column_guard():
    bad = "A,B\n1,2"
    try:
        read_bhav_bytes(bad.encode())
        assert False, "should have raised"
    except ValueError as e:
        assert "missing columns" in str(e)
