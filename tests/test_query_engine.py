"""tests/test_query_engine.py
Tests for the multi-filter screener query engine:
- Multi-filter AND combination (range, enum, custom)
- Nulls-last sorting (ascending and descending)
- Pagination (page size, total counts, page slicing)
- Tertiles and AMFI market cap presets
- Dual benchmark scopes ('market' vs 'universe')
"""
import pytest

from app.query.engine import FilterCondition, QueryEngine
from app.query.presets import calculate_amfi_market_cap_categories, calculate_tertiles


# 15 seed rows transcribed from screenshots
SAMPLE_UNIVERSE = [
    {"name": "Reliance Industries Ltd", "sector": "Energy", "sub_sector": "Oil & Gas Refining & Marketing", "market_cap": 1639061.09, "close_price": 2420.50, "pe_ratio": 24.50, "return_on_equity": 8.95},
    {"name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "sub_sector": "IT Services & Consulting", "market_cap": 1150000.00, "close_price": 3150.00, "pe_ratio": 27.80, "return_on_equity": 43.50},
    {"name": "HDFC Bank Ltd", "sector": "Financials", "sub_sector": "Private Banks", "market_cap": 900000.00, "close_price": 1450.00, "pe_ratio": 18.20, "return_on_equity": 16.20},
    {"name": "ICICI Bank Ltd", "sector": "Financials", "sub_sector": "Private Banks", "market_cap": 650000.00, "close_price": 930.00, "pe_ratio": 16.90, "return_on_equity": 15.80},
    {"name": "Infosys Ltd", "sector": "Information Technology", "sub_sector": "IT Services & Consulting", "market_cap": 580000.00, "close_price": 1400.00, "pe_ratio": 23.40, "return_on_equity": 29.10},
    {"name": "Hindustan Unilever Ltd", "sector": "Consumer Staples", "sub_sector": "FMCG - Household Products", "market_cap": 550000.00, "close_price": 2350.00, "pe_ratio": 54.20, "return_on_equity": 20.40},
    {"name": "ITC Ltd", "sector": "Consumer Staples", "sub_sector": "FMCG - Tobacco", "market_cap": 520000.00, "close_price": 415.00, "pe_ratio": 26.50, "return_on_equity": 27.80},
    {"name": "State Bank of India", "sector": "Financials", "sub_sector": "Public Banks", "market_cap": 500000.00, "close_price": 560.00, "pe_ratio": 9.80, "return_on_equity": 16.50},
    {"name": "Bharti Airtel Ltd", "sector": "Communication Services", "sub_sector": "Telecom Services", "market_cap": 480000.00, "close_price": 820.00, "pe_ratio": 72.10, "return_on_equity": 12.30},
    {"name": "Larsen & Toubro Ltd", "sector": "Industrials", "sub_sector": "Construction & Engineering", "market_cap": 420000.00, "close_price": 2950.00, "pe_ratio": 38.20, "return_on_equity": 14.70},
    {"name": "Bajaj Finance Ltd", "sector": "Financials", "sub_sector": "NBFC", "market_cap": 410000.00, "close_price": 6800.00, "pe_ratio": 31.40, "return_on_equity": 23.50},
    {"name": "Asian Paints Ltd", "sector": "Materials", "sub_sector": "Paints", "market_cap": 290000.00, "close_price": 3050.00, "pe_ratio": None, "return_on_equity": 26.00},  # None PE for testing nulls
    {"name": "Maruti Suzuki India Ltd", "sector": "Consumer Discretionary", "sub_sector": "Auto - 4 Wheelers", "market_cap": 280000.00, "close_price": 9250.00, "pe_ratio": 29.50, "return_on_equity": 13.90},
    {"name": "Titan Company Ltd", "sector": "Consumer Discretionary", "sub_sector": "Gems, Jewellery & Watches", "market_cap": 260000.00, "close_price": 2980.00, "pe_ratio": 78.40, "return_on_equity": 30.20},
    {"name": "Sun Pharmaceutical Industries Ltd", "sector": "Health Care", "sub_sector": "Pharmaceuticals", "market_cap": 250000.00, "close_price": 1050.00, "pe_ratio": 32.10, "return_on_equity": None},  # None ROE
]


def test_query_engine_unfiltered():
    """Executing query without filters returns all rows paginated."""
    engine = QueryEngine(benchmark_scope="market")
    res = engine.execute_query(SAMPLE_UNIVERSE, page=1, page_size=20)
    assert res["total_count"] == 15
    assert len(res["items"]) == 15
    assert res["page"] == 1
    assert res["total_pages"] == 1


def test_query_engine_range_filter():
    """Range filter filters stocks within [min, max]."""
    engine = QueryEngine()
    # ROE between 20% and 35%
    roe_filter = FilterCondition(filter_id="return_on_equity", filter_type="range", min_val=20.0, max_val=35.0)
    res = engine.execute_query(SAMPLE_UNIVERSE, filters=[roe_filter])
    assert res["total_count"] > 0
    for stock in res["items"]:
        assert 20.0 <= stock["return_on_equity"] <= 35.0


def test_query_engine_enum_filter():
    """Enum filter limits results to selected sectors."""
    engine = QueryEngine()
    sec_filter = FilterCondition(
        filter_id="sector",
        filter_type="enum",
        allowed_values={"Financials", "Information Technology"},
    )
    res = engine.execute_query(SAMPLE_UNIVERSE, filters=[sec_filter])
    assert res["total_count"] == 6  # 4 Financials + 2 IT
    for stock in res["items"]:
        assert stock["sector"] in {"Financials", "Information Technology"}


def test_query_engine_multi_filter_and():
    """Multi-filter AND combination narrows results correctly."""
    engine = QueryEngine()
    sec_filter = FilterCondition(filter_id="sector", filter_type="enum", allowed_values={"Financials"})
    pe_filter = FilterCondition(filter_id="pe_ratio", filter_type="range", min_val=10.0, max_val=20.0)
    res = engine.execute_query(SAMPLE_UNIVERSE, filters=[sec_filter, pe_filter])
    # HDFC Bank (18.2) and ICICI Bank (16.9); SBI is 9.8 (<10) and Bajaj Finance is 31.4 (>20)
    names = {s["name"] for s in res["items"]}
    assert names == {"HDFC Bank Ltd", "ICICI Bank Ltd"}


def test_query_engine_nulls_last_sort_descending():
    """Sorting descending by PE Ratio puts highest PE first and None at the end."""
    engine = QueryEngine()
    res = engine.execute_query(SAMPLE_UNIVERSE, sort_by="pe_ratio", sort_asc=False, page_size=20)
    items = res["items"]
    assert items[-1]["name"] == "Asian Paints Ltd"  # pe_ratio is None
    assert items[-1]["pe_ratio"] is None
    # Highest PE should be first
    assert items[0]["name"] == "Titan Company Ltd"
    assert items[0]["pe_ratio"] == 78.40


def test_query_engine_nulls_last_sort_ascending():
    """Sorting ascending by PE Ratio puts lowest PE first and None at the end."""
    engine = QueryEngine()
    res = engine.execute_query(SAMPLE_UNIVERSE, sort_by="pe_ratio", sort_asc=True, page_size=20)
    items = res["items"]
    assert items[-1]["name"] == "Asian Paints Ltd"  # None is last even in ascending sort!
    assert items[-1]["pe_ratio"] is None
    assert items[0]["name"] == "State Bank of India"
    assert items[0]["pe_ratio"] == 9.80


def test_query_engine_pagination():
    """Pagination splits rows into distinct pages."""
    engine = QueryEngine()
    page1 = engine.execute_query(SAMPLE_UNIVERSE, page=1, page_size=5)
    page2 = engine.execute_query(SAMPLE_UNIVERSE, page=2, page_size=5)
    page3 = engine.execute_query(SAMPLE_UNIVERSE, page=3, page_size=5)

    assert len(page1["items"]) == 5
    assert len(page2["items"]) == 5
    assert len(page3["items"]) == 5
    assert page1["total_pages"] == 3

    # Check distinct items
    p1_names = [s["name"] for s in page1["items"]]
    p2_names = [s["name"] for s in page2["items"]]
    assert set(p1_names).isdisjoint(set(p2_names))


def test_tertiles_presets():
    """calculate_tertiles creates three non-overlapping tertile bands."""
    values = [10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    tertiles = calculate_tertiles(values)
    assert tertiles is not None
    assert "low" in tertiles and "mid" in tertiles and "high" in tertiles
    assert tertiles["low"][0] <= tertiles["low"][1]
    assert tertiles["mid"][0] <= tertiles["mid"][1]
    assert tertiles["high"][0] <= tertiles["high"][1]


def test_amfi_market_cap_categories():
    """calculate_amfi_market_cap_categories assigns largecap, midcap, smallcap ranges."""
    cats = calculate_amfi_market_cap_categories(SAMPLE_UNIVERSE)
    assert "largecap" in cats and "midcap" in cats and "smallcap" in cats
    assert cats["largecap"][0] <= cats["largecap"][1]


def test_benchmark_scope_market_vs_universe():
    """Benchmark engine computes sector benchmarks based on market vs universe scope."""
    # Market universe has all 15 stocks.
    # Active universe has only 2 Financials stocks.
    active_subset = [
        {"name": "HDFC Bank Ltd", "sector": "Financials", "sub_sector": "Private Banks", "market_cap": 900000.00, "close_price": 1450.00, "pe_ratio": 18.20},
        {"name": "ICICI Bank Ltd", "sector": "Financials", "sub_sector": "Private Banks", "market_cap": 650000.00, "close_price": 930.00, "pe_ratio": 16.90},
    ]

    engine_market = QueryEngine(benchmark_scope="market")
    res_m = engine_market.execute_query(market_universe=SAMPLE_UNIVERSE, active_universe=active_subset)
    # Under market scope, Financials sector PE includes HDFC (18.2), ICICI (16.9), SBI (9.8), Bajaj Finance (31.4).
    # Median of positive values = (16.9 + 18.2) / 2 = 17.55
    hdfc_stock = next(s for s in res_m["items"] if s["name"] == "HDFC Bank Ltd")
    assert round(hdfc_stock["sector_pe"], 2) == 17.55

    # Under universe scope, Financials sector PE is median of only [18.2, 16.9]
    engine_univ = QueryEngine(benchmark_scope="universe")
    res_u = engine_univ.execute_query(market_universe=SAMPLE_UNIVERSE, active_universe=active_subset)
    hdfc_stock_u = next(s for s in res_u["items"] if s["name"] == "HDFC Bank Ltd")
    assert round(hdfc_stock_u["sector_pe"], 2) == 17.55

