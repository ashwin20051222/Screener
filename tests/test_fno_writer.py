"""F&O writer tests: real UDiFF FO bytes -> fno_daily, futures persist with option_type=''.

The fno_daily composite PK (DuckDB PK columns are implicitly NOT NULL) means futures —
which have no option type — are stored with `''`, never NULL.
"""
from __future__ import annotations

import io
import zipfile
from datetime import date

import pytest

from ingest.nse import fo_bhav_from_bytes

HEADER = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,"
    "FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,"
    "LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,"
    "TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4"
)

FO_ROWS = "\n".join([
    HEADER,
    "2026-10-23,2026-10-23,FO,NSE,STF,67129,,ABCAPITAL,,2026-11-27,2026-11-27,0.00,,ABCAPITAL26NOVFUT,270.00,272.00,268.10,271.45,271.40,269.00,271.40,271.45,3383000,0,14219210,0.00,10284,F1,3100,,,,,",
    "2026-10-23,2026-10-23,FO,NSE,STO,67129,,ABCAPITAL,,2026-10-27,2026-10-27,425.00,PE,ABCAPITAL26OCT425PE,0.00,0.00,0.00,38.35,38.35,38.35,347.25,77.48,12400,0,0,0.00,0,F1,3100,,,,,",
])


def _zip_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("BhavCopy_NSE_FO_0_0_0_TEST_F_0000.csv", text)
    return buf.getvalue()


@pytest.fixture()
def con(tmp_path):
    import duckdb

    from app import db

    c = duckdb.connect(str(tmp_path / "fno.duckdb"))
    db.init_schema(c)
    yield c
    c.close()


def test_futures_and_options_persist(con):
    res = fo_bhav_from_bytes(con, _zip_bytes(FO_ROWS), date(2026, 10, 23))
    assert res["status"] == "ok" and res["rows"] == 2

    rows = con.execute(
        "SELECT underlying, instrument, option_type, strike, oi, expiry "
        "FROM fno_daily ORDER BY instrument, option_type").fetchall()
    fut, opt = rows[0], rows[1]
    assert fut[0] == "ABCAPITAL" and fut[1] == "STF"
    assert fut[2] == ""  # futures carry empty string, not NULL
    assert fut[3] == 0.0 and fut[4] == 3383000
    assert opt[1] == "STO" and opt[2] == "PE" and opt[3] == 425.0

    # re-ingest same bytes -> same 2 rows (idempotent upsert)
    fo_bhav_from_bytes(con, _zip_bytes(FO_ROWS), date(2026, 10, 23))
    assert con.execute("SELECT count(*) FROM fno_daily").fetchone()[0] == 2
