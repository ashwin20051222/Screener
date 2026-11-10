"""tests/test_sector_mapping.py
Offline tests for Task G:
- All 22 official NSE Macro/Industry strings map cleanly onto UI sectors
- Media Entertainment & Publication maps to Communication Services
- Unmapped official strings resolve to None (UI 'Unclassified', never 'Industrials' or 'General')
- Nifty Total Market CSV + BSE ListofScripData inbox CSV industry enrichment
"""
from __future__ import annotations

import duckdb

from app import config, db
from app.query.snapshot import build_screener_snapshot, load_snapshot_from_db
from ingest.bse import sync_scrip_master_from_inbox_csv
from ingest.master_enrichment import (
    classify_security_industries,
    get_unmapped_industries,
    map_industry_to_sector,
)
from ingest.nse import sync_total_market_industries_from_bytes

OFFICIAL_22_NSE_INDUSTRIES = {
    "Automobile and Auto Components": "Consumer Discretionary",
    "Capital Goods": "Industrials",
    "Chemicals": "Materials",
    "Construction": "Industrials",
    "Construction Materials": "Materials",
    "Consumer Durables": "Consumer Discretionary",
    "Consumer Services": "Consumer Discretionary",
    "Diversified": "Industrials",
    "Fast Moving Consumer Goods": "Consumer Staples",
    "Financial Services": "Financials",
    "Forest Materials": "Materials",
    "Healthcare": "Health Care",
    "Information Technology": "Information Technology",
    "Media Entertainment & Publication": "Communication Services",
    "Metals & Mining": "Materials",
    "Oil Gas & Consumable Fuels": "Energy",
    "Power": "Utilities",
    "Realty": "Real Estate",
    "Services": "Industrials",
    "Telecommunication": "Communication Services",
    "Textiles": "Consumer Discretionary",
    "Utilities": "Utilities",
}


def test_all_22_official_nse_industries_mapped():
    config.sector_map.cache_clear()
    for raw, expected_sector in OFFICIAL_22_NSE_INDUSTRIES.items():
        assert map_industry_to_sector(raw) == expected_sector
    assert map_industry_to_sector("Exotic Cosmic Widgetry") == "INDUSTRY_UNMAPPED"


def test_unmapped_never_defaults_to_industrials_or_general(tmp_path):
    con = duckdb.connect(str(tmp_path / "sec.db"))
    db.init_schema(con)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE1", "isin": "INE1", "nse_symbol": "UNM", "name": "Unmapped Co"},
        {"security_id": "INE2", "isin": "INE2", "nse_symbol": "OIL", "name": "Oil Co"},
        {"security_id": "INE3", "isin": "INE3", "nse_symbol": "AUTO", "name": "Auto Co"},
    ], keys=["security_id"])

    res = classify_security_industries(con, [
        ("UNM", "Brand New Exotic Niche"),
        ("OIL", "Oil Gas & Consumable Fuels"),
        ("AUTO", "Automobile and Auto Components"),
    ])
    assert res["unmapped_count"] == 1
    assert res["unmapped_industries"] == ["Brand New Exotic Niche"]

    unmapped = get_unmapped_industries(con)
    assert unmapped == [{"industry": "Brand New Exotic Niche", "count": 1}]

    build_screener_snapshot(con)
    ds = load_snapshot_from_db(con)
    by_sym = {r["nse_symbol"]: r for r in ds["rows"]}
    assert by_sym["OIL"]["sector"] == "Energy"
    assert by_sym["AUTO"]["sector"] == "Consumer Discretionary"
    assert by_sym["UNM"]["sector"] == "Unclassified"
    assert by_sym["UNM"]["sub_sector"] == "Brand New Exotic Niche"
    con.close()


def test_total_market_and_bse_inbox_industry_classification(tmp_path):
    con = duckdb.connect(str(tmp_path / "tm.db"))
    db.init_schema(con)
    db.upsert_rows(con, "ref_security", [
        {"security_id": "INE10", "isin": "INE10", "nse_symbol": "MICRO1", "name": "Micro Metals Ltd"},
        {"security_id": "INE11", "isin": "INE11", "nse_symbol": "MEDIA1", "name": "Media News Ltd"},
        {"security_id": "INE12", "isin": "INE12", "bse_code": "500111", "name": "BSE Only Co"},
    ], keys=["security_id"])

    csv_payload = (
        "Company Name,Industry,Symbol,Series,ISIN Code\n"
        "Micro Metals Ltd,Metals & Mining,MICRO1,EQ,INE10\n"
        "Media News Ltd,Media Entertainment & Publication,MEDIA1,EQ,INE11\n"
    ).encode("utf-8")
    tm_res = sync_total_market_industries_from_bytes(con, csv_payload)
    assert tm_res["updated"] == 2

    bse_csv = tmp_path / "ListofScripData.csv"
    bse_csv.write_text(
        "Security Code,Issuer Name,Security Id,Security Name,Status,Group,Face Value,ISIN No,Industry,Instrument\n"
        "500111,BSE Only Co,BSEONLY,BSEONLY,Active,B,10.0,INE12,Telecommunication,Equity\n",
        encoding="utf-8",
    )
    bse_res = sync_scrip_master_from_inbox_csv(con, bse_csv)
    assert bse_res["classified"]["updated"] == 1

    rows = con.execute("SELECT security_id, sector, sub_sector FROM ref_security ORDER BY security_id").fetchall()
    assert rows == [
        ("INE10", "Materials", "Metals & Mining"),
        ("INE11", "Communication Services", "Media Entertainment & Publication"),
        ("INE12", "Communication Services", "Telecommunication"),
    ]
    con.close()
