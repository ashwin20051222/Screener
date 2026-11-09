"""app/metrics/technicals.py
Technical indicators engine implementing Section 10.9 & Section 12 specifications:
SMA, EMA, RSI, MACD, Bollinger Bands, Parabolic SAR, Williams %R, Stochastic,
OBV, AD Line, SuperTrend, Max Drawdown, Volatility, Beta, Alpha, and Sharpe Ratio.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple


def sma(series: Sequence[float], window: int) -> Optional[float]:
    """Simple Moving Average of trailing n elements."""
    if len(series) < window or window <= 0:
        return None
    return sum(series[-window:]) / float(window)


def ema_multiplier(n: int) -> float:
    """EMA smoothing factor multiplier: 2 / (n + 1)."""
    return 2.0 / (float(n) + 1.0)


def ema_series(series: Sequence[float], window: int) -> List[float]:
    """Exponential Moving Average series seeded with SMA of the first n elements."""
    if len(series) < window or window <= 0:
        return []
    alpha = ema_multiplier(window)
    # Seed with SMA of first window
    initial_sma = sum(series[:window]) / float(window)
    res = [initial_sma]
    for val in series[window:]:
        current_ema = val * alpha + res[-1] * (1.0 - alpha)
        res.append(current_ema)
    return res


def ema(series: Sequence[float], window: int) -> Optional[float]:
    """Latest EMA value."""
    s = ema_series(series, window)
    return s[-1] if s else None


def pct_above_ma(current_price: Optional[float], ma_val: Optional[float]) -> Optional[float]:
    """Percentage distance above moving average: (Price / MA - 1) * 100."""
    if current_price is None or ma_val is None or ma_val <= 0:
        return None
    return ((current_price / ma_val) - 1.0) * 100.0


def on_balance_volume_series(closes: Sequence[float], volumes: Sequence[float]) -> List[float]:
    """Computes running OBV series from closes and volumes.
    Day 0 is baseline; for day i:
      if close[i] > close[i-1]: obv[i] = obv[i-1] + volume[i-1] (or volume[i])
    Following Section 12 Golden Test specification:
    Closes: [7661.6, 7578.8, 7457.4, 7608.5, 7701.2, 7582.5, 7598.8]
    Volumes: [385730, 676390, 328598, 488766, 321296, 332924]
    Yields: [-385730, -1062120, -733522, -244756, -566052, -233128]
    """
    if len(closes) < 2 or len(volumes) < len(closes) - 1:
        return []
    obv = 0.0
    result = []
    for i in range(1, len(closes)):
        c_prev = closes[i - 1]
        c_curr = closes[i]
        vol = volumes[i - 1]
        if c_curr > c_prev:
            obv += vol
        elif c_curr < c_prev:
            obv -= vol
        result.append(obv)
    return result


def rsi_14d(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Simple 14-day RSI (arithmetic mean of gains and losses)."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / float(period) if gains else 0.0
    avg_loss = sum(losses) / float(period) if losses else 0.0
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def williams_r(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Williams %R: (Highest High - Close) / (Highest High - Lowest Low) * -100."""
    if len(closes) < period or len(highs) < period or len(lows) < period:
        return None
    hh = max(highs[-period:])
    ll = min(lows[-period:])
    c = closes[-1]
    if hh == ll:
        return None
    return ((hh - c) / (hh - ll)) * -100.0


def stochastic_k(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Stochastic %K: (Close - Lowest Low) / (Highest High - Lowest Low) * 100."""
    if len(closes) < period or len(highs) < period or len(lows) < period:
        return None
    hh = max(highs[-period:])
    ll = min(lows[-period:])
    c = closes[-1]
    if hh == ll:
        return None
    return ((c - ll) / (hh - ll)) * 100.0


def bollinger_bands(closes: Sequence[float], period: int = 20, num_sd: float = 2.0) -> Optional[Tuple[float, float, float]]:
    """Returns (Upper Band, Middle SMA, Lower Band) over period."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    mean = sum(window) / float(period)
    variance = sum((x - mean) ** 2 for x in window) / float(period)
    sd = math.sqrt(variance)
    return (mean + num_sd * sd, mean, mean - num_sd * sd)


def max_drawdown_1y(closes: Sequence[float], lookback: int = 250) -> Optional[float]:
    """1Y Max Loss: worst peak-to-trough drawdown where peak occurs before trough.
    Returns negative percentage (e.g. -24.5 for -24.5%).
    """
    if len(closes) < 2:
        return None
    sub = list(closes[-lookback:])
    max_peak = sub[0]
    max_dd = 0.0
    for price in sub:
        if price > max_peak:
            max_peak = price
        elif max_peak > 0:
            dd = (price - max_peak) / max_peak
            if dd < max_dd:
                max_dd = dd
    return max_dd * 100.0


def annualized_volatility(daily_closes: Sequence[float], lookback: int = 200) -> Optional[float]:
    """Annualized volatility of daily returns: stdev(daily_log_returns) * sqrt(252) * 100."""
    if len(daily_closes) < lookback + 1:
        return None
    sub = daily_closes[-(lookback + 1):]
    log_returns = [math.log(sub[i] / sub[i - 1]) for i in range(1, len(sub))]
    n = len(log_returns)
    mean_r = sum(log_returns) / float(n)
    var = sum((r - mean_r) ** 2 for r in log_returns) / float(n - 1)
    sd = math.sqrt(var)
    return sd * math.sqrt(252.0) * 100.0


def beta_and_alpha(
    stock_weekly_closes: Sequence[float],
    benchmark_weekly_closes: Sequence[float],
    lookback_weeks: int = 104,
) -> Tuple[Optional[float], Optional[float]]:
    """Beta = cov(r_stock, r_bench) / var(r_bench) over 104 weekly closes.
    Alpha = total stock return - total benchmark return (simple excess return as documented).
    """
    if len(stock_weekly_closes) < lookback_weeks + 1 or len(benchmark_weekly_closes) < lookback_weeks + 1:
        return None, None
    s_closes = stock_weekly_closes[-(lookback_weeks + 1):]
    b_closes = benchmark_weekly_closes[-(lookback_weeks + 1):]

    r_s = [s_closes[i] / s_closes[i - 1] - 1.0 for i in range(1, len(s_closes))]
    r_b = [b_closes[i] / b_closes[i - 1] - 1.0 for i in range(1, len(b_closes))]

    mean_s = sum(r_s) / float(len(r_s))
    mean_b = sum(r_b) / float(len(r_b))

    cov = sum((r_s[i] - mean_s) * (r_b[i] - mean_b) for i in range(len(r_s))) / float(len(r_s) - 1)
    var_b = sum((r_b[i] - mean_b) ** 2 for i in range(len(r_b))) / float(len(r_b) - 1)

    if var_b <= 0:
        return None, None
    beta = cov / var_b

    # Simple excess return
    tot_s = (s_closes[-1] / s_closes[0] - 1.0) * 100.0
    tot_b = (b_closes[-1] / b_closes[0] - 1.0) * 100.0
    alpha = tot_s - tot_b

    return beta, alpha


def sharpe_ratio(
    excess_return: float,
    volatility: float,
) -> Optional[float]:
    """Sharpe Ratio = (Stock Return - Benchmark Return / Risk-free) / Volatility.
    Section 12 Golden Test: (42.5% - 5%) / 28% = 1.34.
    """
    if volatility <= 0:
        return None
    return excess_return / volatility
