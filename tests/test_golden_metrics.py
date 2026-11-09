"""tests/test_golden_metrics.py
Golden test suite strictly verifying every mathematical calculation in Section 12.
All tests must pass with 100% precision.
"""
import pytest

from app.metrics.formulas import (
    cagr,
    pe_ratio,
    pb_ratio,
    ps_ratio,
    dividend_yield,
    multiple_premium,
    interest_coverage,
    quick_ratio,
    cash_conversion_cycle,
    rollover_cost,
    percentage_rollover,
    put_call_ratio,
    oi_change_pct,
    bank_net_loans,
)
from app.metrics.technicals import (
    ema_multiplier,
    pct_above_ma,
    on_balance_volume_series,
    sharpe_ratio,
    williams_r,
    stochastic_k,
)


def test_golden_cagr():
    """CAGR 700 to 960 over 5 years = 6.5%."""
    res = cagr(700, 960, 5)
    assert res is not None
    assert round(res * 100.0, 1) == 6.5


def test_golden_pe():
    """PE 300/30 = 10."""
    res = pe_ratio(300, 30)
    assert res == 10.0


def test_golden_pe_premium():
    """PE premium: 22.0 vs sector 17.6 = +25.0%; 12.3 vs 17.6 = -30.1%."""
    prem1 = multiple_premium(22.0, 17.6)
    prem2 = multiple_premium(12.3, 17.6)
    assert prem1 is not None and round(prem1, 1) == 25.0
    assert prem2 is not None and round(prem2, 1) == -30.1


def test_golden_pb_premium():
    """PB premium: 3.8 vs 2.7 = +40.7%; 1.3 vs 2.7 = -51.9%."""
    prem1 = multiple_premium(3.8, 2.7)
    prem2 = multiple_premium(1.3, 2.7)
    assert prem1 is not None and round(prem1, 1) == 40.7
    assert prem2 is not None and round(prem2, 1) == -51.9


def test_golden_ps_premium():
    """PS premium: 4.7 vs 3.1 = +51.6%."""
    prem = multiple_premium(4.7, 3.1)
    assert prem is not None and round(prem, 1) == 51.6


def test_golden_dividend_yield():
    """Dividend yield 16/250 = 6.4%."""
    dy = dividend_yield(16, 250)
    assert dy is not None and round(dy, 1) == 6.4


def test_golden_ema_multiplier():
    """EMA multiplier for n=20 = 0.0952."""
    mult = ema_multiplier(20)
    assert round(mult, 4) == 0.0952


def test_golden_pct_above_sma():
    """% above 1M SMA: 30 vs 28 = 7.14%; above 12M SMA: 30 vs 22.7 = 32.2%."""
    above_1m = pct_above_ma(30, 28)
    above_12m = pct_above_ma(30, 22.7)
    assert above_1m is not None and round(above_1m, 2) == 7.14
    assert above_12m is not None and round(above_12m, 1) == 32.2


def test_golden_interest_coverage():
    """Interest coverage 120/50 = 2.4."""
    ic = interest_coverage(120, 50)
    assert ic == 2.4


def test_golden_quick_ratio():
    """Quick ratio (250-50)/300 = 0.67."""
    qr = quick_ratio(250, 50, 300)
    assert qr is not None and round(qr, 2) == 0.67


def test_golden_cash_conversion_cycle():
    """Cash conversion cycle 28+13-32 = 9."""
    ccc = cash_conversion_cycle(28, 13, 32)
    assert ccc == 9


def test_golden_rollover_cost():
    """Rollover cost 95.45/94.35-1 = 1.2%."""
    rc = rollover_cost(95.45, 94.35)
    assert rc is not None and round(rc, 1) == 1.2


def test_golden_percentage_rollover():
    """Percentage rollover 3,430,000 / (55,083,000+3,430,000+28,000) = 5.9%."""
    pct_ro = percentage_rollover(3430000, 55083000, 28000)
    assert pct_ro is not None and round(pct_ro, 1) == 5.9


def test_golden_put_call_ratio():
    """Put call ratio 120/100 = 1.2."""
    pcr = put_call_ratio(120, 100)
    assert pcr == 1.2


def test_golden_oi_change_pct():
    """1D OI change 120 vs 100 = +20%."""
    oi_chg = oi_change_pct(120, 100)
    assert oi_chg is not None and round(oi_chg, 1) == 20.0


def test_golden_obv_series():
    """OBV for closes 7661.6, 7578.8, 7457.4, 7608.5, 7701.2, 7582.5, 7598.8
    with volumes 385730, 676390, 328598, 488766, 321296, 332924
    = -385730, -1062120, -733522, -244756, -566052, -233128.
    """
    closes = [7661.6, 7578.8, 7457.4, 7608.5, 7701.2, 7582.5, 7598.8]
    volumes = [385730, 676390, 328598, 488766, 321296, 332924]
    expected = [-385730.0, -1062120.0, -733522.0, -244756.0, -566052.0, -233128.0]
    obv = on_balance_volume_series(closes, volumes)
    assert obv == expected


def test_golden_sharpe_ratio():
    """Sharpe (42.5% - 5%) / 28% = 1.34."""
    sharpe = sharpe_ratio(42.5 - 5.0, 28.0)
    assert sharpe is not None and round(sharpe, 2) == 1.34


def test_golden_bank_net_loans():
    """Bank net loans 100000 - 2000 = 98000."""
    net_loans = bank_net_loans(100000, 2000)
    assert net_loans == 98000


def test_golden_williams_r_and_stochastic():
    """Williams %R and Stochastic %K on hand-computed 14-day window.
    Highs: [100 .. 150 (HH)], Lows: [80 (LL) .. 120], Close = 130.
    HH = 150, LL = 80, Close = 130. Range = 70.
    Williams %R = (150 - 130) / 70 * -100 = 20/70 * -100 = -28.57%
    Stochastic %K = (130 - 80) / 70 * 100 = 50/70 * 100 = 71.43%
    """
    highs = [100.0 + i * 2.0 for i in range(13)] + [150.0]  # HH = 150
    lows = [80.0] + [85.0 + i * 2.0 for i in range(13)]     # LL = 80
    closes = [110.0] * 13 + [130.0]                          # Close = 130

    wr = williams_r(highs, lows, closes, period=14)
    stoch = stochastic_k(highs, lows, closes, period=14)

    assert wr is not None and round(wr, 2) == -28.57
    assert stoch is not None and round(stoch, 2) == 71.43

