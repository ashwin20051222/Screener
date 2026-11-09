"""tests/test_api.py
Integration tests for FastAPI router endpoints:
- get_filters()
- query_screener()
- validate_custom_filter()
"""
import pytest

from app.api.routes import (
    CustomFilterValidateRequest,
    FilterRuleModel,
    ScreenerQueryRequest,
    get_filters,
    query_screener,
    validate_custom_filter,
)

SAMPLE_ROWS = [
    {"name": "Reliance", "sector": "Energy", "sub_sector": "Oil & Gas", "market_cap": 1600000.0, "pe_ratio": 24.5, "roe": 9.0},
    {"name": "TCS", "sector": "Information Technology", "sub_sector": "IT Services", "market_cap": 1100000.0, "pe_ratio": 27.8, "roe": 43.5},
    {"name": "HDFC Bank", "sector": "Financials", "sub_sector": "Private Banks", "market_cap": 900000.0, "pe_ratio": 18.2, "roe": 16.2},
]


def test_api_filters():
    data = get_filters()
    assert "filters" in data
    assert len(data["filters"]) == 255
    assert "return_on_equity" in data["filters"]
    roe = data["filters"]["return_on_equity"]
    assert roe["direction_of_goodness"] == "higher_is_better"
    assert "Net profit" in roe["formula"]


def test_api_query_unfiltered():
    req = ScreenerQueryRequest(
        active_universe=SAMPLE_ROWS,
        filters=[],
        sort_by="market_cap",
        sort_asc=False,
        page=1,
        page_size=10,
    )
    data = query_screener(req)
    assert data["total_count"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["name"] == "Reliance"


def test_api_query_with_range_filter():
    req = ScreenerQueryRequest(
        active_universe=SAMPLE_ROWS,
        filters=[
            FilterRuleModel(filter_id="pe_ratio", filter_type="range", min_val=20.0, max_val=30.0)
        ],
        sort_by="pe_ratio",
        sort_asc=True,
        page=1,
        page_size=10,
    )
    data = query_screener(req)
    assert data["total_count"] == 2
    names = [s["name"] for s in data["items"]]
    assert names == ["Reliance", "TCS"]


def test_api_custom_filter_validate():
    req = CustomFilterValidateRequest(
        expression="(pe_ratio + pb_ratio) / 2",
        sample_rows=[
            {"pe_ratio": 20.0, "pb_ratio": 4.0},
            {"pe_ratio": 10.0, "pb_ratio": 2.0},
        ],
    )
    data = validate_custom_filter(req)
    assert data["valid"] is True
    assert data["sample_evaluations"] == [12.0, 6.0]
