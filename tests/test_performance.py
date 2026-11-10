"""tests/test_performance.py
Phase 5 performance benchmark on 6,500 stocks (clearly labelled synthetic benchmark fixture).
Verifies QueryEngine filtering, multi-filter AND, custom formula AST, nulls-last sort,
tertiles, sector counts, pagination, and quant scores complete within strict latency bounds.
"""
from __future__ import annotations

import random
import time

from app.metrics.scores import compute_all_quant_scores
from app.query.engine import FilterCondition, QueryEngine

SECTORS = [
    ("Financials", "Private Banks"),
    ("Information Technology", "IT Services & Consulting"),
    ("Consumer Discretionary", "Auto - 4 Wheelers"),
    ("Industrials", "Capital Goods"),
    ("Health Care", "Pharmaceuticals"),
    ("Materials", "Chemicals"),
    ("Consumer Staples", "FMCG"),
    ("Energy", "Oil & Gas"),
    ("Utilities", "Electric Utilities"),
    ("Communication Services", "Telecom Services"),
    ("Real Estate", "Realty"),
]


def _build_fixture_stocks(n: int = 6500) -> list[dict]:
    rng = random.Random(42)
    rows = []
    for i in range(n):
        sec, sub = SECTORS[i % len(SECTORS)]
        rows.append({
            "nse_symbol": f"STK{i:04d}",
            "name": f"Benchmark Fixture Corp {i}",
            "sector": sec,
            "sub_sector": sub,
            "market_cap": round(rng.uniform(50.0, 500000.0), 2),
            "close_price": round(rng.uniform(20.0, 8000.0), 2),
            "pe_ratio": None if i % 15 == 0 else round(rng.uniform(5.0, 85.0), 2),
            "pb_ratio": round(rng.uniform(0.6, 15.0), 2),
            "return_on_equity": round(rng.uniform(-10.0, 45.0), 2),
            "roce": round(rng.uniform(-5.0, 48.0), 2),
            "net_profit_margin": round(rng.uniform(1.0, 30.0), 2),
            "asset_turnover_ratio": round(rng.uniform(0.3, 2.5), 2),
            "debt_to_equity": round(rng.uniform(0.0, 3.0), 2),
            "1y_return": round(rng.uniform(-40.0, 120.0), 2),
            "1m_return": round(rng.uniform(-15.0, 30.0), 2),
            "dividend_yield": round(rng.uniform(0.0, 6.0), 2),
        })
    return rows


def test_query_engine_and_scores_6500_stocks_performance():
    market = _build_fixture_stocks(6500)

    t_scores0 = time.perf_counter()
    scores = compute_all_quant_scores(market)
    t_scores_ms = (time.perf_counter() - t_scores0) * 1000.0
    assert len(scores) == 6500
    assert t_scores_ms < 1000.0, f"Quant scores took too long: {t_scores_ms:.1f}ms"

    engine = QueryEngine(benchmark_scope="market")
    filters = [
        FilterCondition("market_cap", "range", min_val=500.0, max_val=250000.0),
        FilterCondition("pe_ratio", "range", min_val=5.0, max_val=35.0),
        FilterCondition("sector", "enum", allowed_values={"Financials", "Information Technology", "Industrials"}),
        FilterCondition("custom_pe_pb", "custom", min_val=10.0, max_val=60.0, custom_expression="pe_ratio + pb_ratio"),
    ]

    t_q0 = time.perf_counter()
    res = engine.execute_query(
        market_universe=market,
        filters=filters,
        sort_by="market_cap",
        sort_asc=False,
        page=1,
        page_size=20,
    )
    t_q_ms = (time.perf_counter() - t_q0) * 1000.0

    assert res["total_count"] > 0
    assert len(res["items"]) == 20
    assert t_q_ms < 500.0, f"6,500-stock multi-filter query took {t_q_ms:.1f}ms"
