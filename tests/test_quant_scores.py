"""tests/test_quant_scores.py
Unit tests for Section 11 Quant Scores ('Approximate - computed locally'):
- Price Momentum Rank, Earnings Quality Rank, Price to Intrinsic Value Rank,
  Value Momentum Rank, Fundamental Score (1-10) including bank-specific financial health rules.
"""
from app.metrics.scores import compute_all_quant_scores, scores_config


def test_quant_scores_weights_and_bounds():
    cfg = scores_config()
    assert cfg["badge"] == "Approximate - computed locally"

    sample_market = [
        {
            "nse_symbol": "LEADER",
            "sector": "Information Technology",
            "sub_sector": "IT Services",
            "close_price": 1000.0,
            "1y_return": 45.0,
            "net_profit_margin": 22.0,
            "asset_turnover_ratio": 1.6,
            "cash_flow_operating_activities": 1200.0,
            "net_income": 1000.0,
            "earnings_per_share": 80.0,
            "5y_historical_eps_growth": 18.0,
            "5y_historical_revenue_growth": 16.0,
            "dividend_per_share": 35.0,
            "capital_expenditures": 100.0,
            "total_common_shares_outstanding": 100_000_000,
            "pe_ratio": 12.5,
            "pb_ratio": 3.0,
            "pe_premium_vs_sector": -20.0,
            "pb_premium_vs_sector": -10.0,
            "return_on_equity": 32.0,
            "roce": 35.0,
            "debt_to_equity": 0.05,
            "interest_coverage_ratio": 40.0,
        },
        {
            "nse_symbol": "LAGGARD",
            "sector": "Information Technology",
            "sub_sector": "IT Services",
            "close_price": 500.0,
            "1y_return": -15.0,
            "net_profit_margin": 5.0,
            "asset_turnover_ratio": 0.7,
            "cash_flow_operating_activities": 100.0,
            "net_income": 200.0,
            "earnings_per_share": 8.0,
            "5y_historical_eps_growth": 2.0,
            "5y_historical_revenue_growth": 4.0,
            "dividend_per_share": 2.0,
            "capital_expenditures": 50.0,
            "total_common_shares_outstanding": 100_000_000,
            "pe_ratio": 62.5,
            "pb_ratio": 8.0,
            "pe_premium_vs_sector": 150.0,
            "pb_premium_vs_sector": 80.0,
            "return_on_equity": 6.0,
            "roce": 7.0,
            "debt_to_equity": 2.5,
            "interest_coverage_ratio": 1.8,
        },
        {
            "nse_symbol": "HDFCBANK",
            "sector": "Financials",
            "sub_sector": "Private Banks",
            "is_financial_institution": True,
            "close_price": 1500.0,
            "1y_return": 12.0,
            "net_profit_margin": 20.0,
            "asset_turnover_ratio": 0.08,
            "net_interest_income": 80000.0,
            "total_revenue": 150000.0,
            "return_on_assets": 1.9,
            "return_on_equity": 16.5,
            "pe_ratio": 16.0,
            "pb_ratio": 2.4,
            "5y_historical_revenue_growth": 14.0,
            "5y_historical_eps_growth": 15.0,
            "earnings_per_share": 90.0,
        },
    ]

    scores = compute_all_quant_scores(sample_market)
    assert set(scores.keys()) == {"LEADER", "LAGGARD", "HDFCBANK"}

    lead = scores["LEADER"]
    lag = scores["LAGGARD"]
    bank = scores["HDFCBANK"]

    assert 0.0 <= lead["price_momentum_rank"] <= 100.0
    assert lead["price_momentum_rank"] > lag["price_momentum_rank"]
    assert lead["earnings_quality_rank"] > lag["earnings_quality_rank"]
    assert lead["price_to_intrinsic_value_rank"] > lag["price_to_intrinsic_value_rank"]
    assert lead["value_momentum_rank"] > lag["value_momentum_rank"]

    # Fundamental Score strictly bounded 1.0 .. 10.0 and LEADER beats LAGGARD in same sector
    assert 1.0 <= lead["fundamental_score"] <= 10.0
    assert 1.0 <= lag["fundamental_score"] <= 10.0
    assert lead["fundamental_score"] > lag["fundamental_score"]
    # Bank with null D/E and ROCE still receives valid Fundamental Score via NII + ROA + ROE
    assert bank["fundamental_score"] is not None and 1.0 <= bank["fundamental_score"] <= 10.0
