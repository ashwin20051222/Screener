"""Master-file parser tests built from the REAL public headers verified live 2026-10-25
(header spellings exactly as served by nsearchives.nseindia.com)."""
from __future__ import annotations

from datetime import date

from ingest.nse import (_parse_corp_actions, _parse_equity_master, _parse_etf_master,
                        _parse_fno_lots, _parse_index_list)

EQ_HEADER = ("SYMBOL     , NAME OF COMPANY         , SERIES , DATE OF LISTING ,"
             "PAID UP VALUE  , MARKET LOT ,  FACE VALUE  ,  ISIN NUMBER  ")

EQ_ROWS = "\n".join([
    EQ_HEADER,
    "20MICRONS,20 MICRONS LIMITED,EQ,02-Jan-2008,10.00,1,10.00,INE144J01027",
    "RELIANCE,RELIANCE INDUSTRIES EQ EQ,EQ,08-May-1995,10.00,1,10.00,INE002A01018",
    ",don't crash on empty symbol,,,,,,,,",
])

ETF_ROWS = "\n".join([
    "Symbol,Name of the Company, ISIN, ,Underlying Index,As on date",
    "HDFCNIFTY,NIFTY 50 ETF - HDFC,INF976L01XCU,,,2026-10-23",
    "GOLDBEES,GOLD BEES,INF380M01ZL3,,,2026-10-23",
])

LOT_HEADER = ("UNDERLYING,TRADING SYMBOL,SYMBOL,ISIN,BPL,CANDIDATE_MARKET_LOT,SAO_LIST,"
              "NewLot,SettingType,MarketType,DisplayType")

LOT_ROWS = "\n".join([
    LOT_HEADER,
    "ABCAPITAL,ABCAPITAL,ABCAPITAL,INE674A01025,,3100,,,,,Y",
    "RELIANCE,RELIANCE,RELIANCE,INE002A01018,,500,,,,N,",
])

IDX_HEADER = "Company Name                     ,Industry      ,Symbol        ,Series,ISIN Code "

IDX_ROWS = "\n".join([
    IDX_HEADER,
    "20 Microns Limited,Zuo Er,20MICRONS,EQ,INE144J01027",
    "Reliance Industries Limited,Energy,RELIANCE,EQ,INE002A01018",
])


def test_equity_master_with_real_spacy_header():
    rows = _parse_equity_master(EQ_ROWS.encode())
    by_sym = {r["nse_symbol"]: r for r in rows}
    assert set(by_sym) == {"20MICRONS", "RELIANCE"}
    r = by_sym["20MICRONS"]
    assert r["security_id"] == "INE144J01027"
    assert r["name"] == "20 MICRONS LIMITED"
    assert r["nse_series"] == "EQ"
    assert r["listing_date"] == date(2008, 1, 2)
    assert r["face_value"] == 10.0 and r["market_lot"] == 1
    assert by_sym["RELIANCE"]["listing_date"] == date(1995, 5, 8)


def test_equity_master_symbol_without_isin_gets_synthetic_id():
    payload = "\n".join([
        EQ_HEADER,
        "NOISIN,SOME COMPANY,EQ,01-Apr-2021,10.00,1,10.00,",
    ])
    rows = _parse_equity_master(payload.encode())
    assert rows[0]["security_id"] == "NSE:NOISIN"
    assert rows[0]["isin"] is None


def test_etf_master_marks_etf_true():
    rows = _parse_etf_master(ETF_ROWS.encode())
    by_sym = {r["nse_symbol"]: r for r in rows}
    assert set(by_sym) == {"HDFCNIFTY", "GOLDBEES"}
    assert all(r["is_etf"] for r in rows)
    assert by_sym["GOLDBEES"]["isin"] == "INF380M01ZL3"


def test_fno_lots_parse():
    rows = _parse_fno_lots(LOT_ROWS.encode())
    assert rows[0]["symbol"] == "ABCAPITAL"
    assert rows[0]["sao"] is None  # empty SAO cell -> None, never fake data
    assert {r["symbol"] for r in rows} == {"ABCAPITAL", "RELIANCE"}


def test_index_list_parse():
    rows = _parse_index_list(IDX_ROWS.encode())
    by_sym = {r["symbol"]: r for r in rows}
    assert by_sym["RELIANCE"]["company"] == "Reliance Industries Limited"
    assert by_sym["20MICRONS"]["isin"] == "INE144J01027"
    assert by_sym["RELIANCE"]["series"] == "EQ"


def test_corp_actions_json():
    data = [
        {
            "symbol": "RELIANCE",
            "isin": "INE002A01018",
            "comp": "Reliance Industries Ltd",
            "exDate": "10-Oct-2026 09:15",
            "recDate": "11-Oct-2026 09:15",
            "purpose": "Dividend - Rs 4.50/- Per Share",
            "faceVal": "10.00",
            "caBroadcastDate": "26-Sep-2026",
        },
        {"symbol": "", "exDate": None},   # dropped silently
        {"exDate": None, "symbol": "WEIRD"},  # no ex-date -> skipped
    ]
    rows = _parse_corp_actions(data)
    (only,) = rows
    assert only["symbol"] == "RELIANCE"
    assert only["ex_date"] == date(2026, 10, 10)
    assert only["record_date"] == date(2026, 10, 11)
    assert only["face_value"] == 10.00
    assert "Dividend" in only["purpose"]


def test_corp_actions_empty_input():
    assert _parse_corp_actions({}) == []
    assert _parse_corp_actions(None) == []
    assert _parse_corp_actions([]) == []
