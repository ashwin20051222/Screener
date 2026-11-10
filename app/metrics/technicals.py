"""app/metrics/technicals.py
Complete Technical Indicators engine implementing Section 10.7, Section 10.9 & Section 12:
SMA, EMA, RSI (simple + Wilder), ADX(14) with +DI/-DI, MACD Lines 1 & 2,
Bollinger Bands & distances, Parabolic SAR, Williams %R, Stochastic %K/%D,
OBV & 1W change, AD Line & 1W change, SuperTrend (ATR 10, mult 3),
1Y Max Drawdown, 200D Volatility, 104W Beta/Alpha/Sharpe, Relative Volume, and Return windows.
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
    Follows Section 12 Golden Test specification cleanly.
    """
    if len(closes) < 2 or len(volumes) < len(closes) - 1:
        return []
    obv = 0.0
    result = []
    vol_offset = 1 if len(volumes) >= len(closes) else 0
    for i in range(1, len(closes)):
        c_prev = closes[i - 1]
        c_curr = closes[i]
        vol = volumes[i if vol_offset else (i - 1)]
        if c_curr > c_prev:
            obv += vol
        elif c_curr < c_prev:
            obv -= vol
        result.append(obv)
    return result


def obv_1w_change(closes: Sequence[float], volumes: Sequence[float], lookback: int = 5) -> Optional[float]:
    """1W Change in OBV (%) = (OBV / OBV[-5] - 1) * 100."""
    obv_s = on_balance_volume_series(closes, volumes)
    if len(obv_s) <= lookback:
        return None
    prev = obv_s[-1 - lookback]
    if prev == 0:
        return None
    return ((obv_s[-1] / prev) - 1.0) * 100.0


def ad_line_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    volumes: Sequence[float],
) -> List[float]:
    """Accumulation / Distribution Line:
    MFM = ((C - L) - (H - C)) / (H - L), MFV = MFM * Vol, AD = running sum of MFV.
    """
    n = min(len(highs), len(lows), len(closes), len(volumes))
    ad = 0.0
    res = []
    for i in range(n):
        h, l, c, v = highs[i], lows[i], closes[i], volumes[i]
        hl = h - l
        mfm = (((c - l) - (h - c)) / hl) if hl > 0 else 0.0
        ad += mfm * v
        res.append(ad)
    return res


def ad_1w_change(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    volumes: Sequence[float],
    lookback: int = 5,
) -> Optional[float]:
    """1W Change in AD Line (%) = (AD / AD[-5] - 1) * 100."""
    ad_s = ad_line_series(highs, lows, closes, volumes)
    if len(ad_s) <= lookback:
        return None
    prev = ad_s[-1 - lookback]
    if prev == 0:
        return None
    return ((ad_s[-1] / prev) - 1.0) * 100.0


def rsi_14d(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Simple 14-day RSI (arithmetic mean of trailing gains and losses)."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / float(period)
    avg_loss = sum(losses) / float(period)
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def rsi_exponential_14d(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Wilder-smoothed exponential 14-day RSI."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(0.0, d) for d in deltas]
    losses = [max(0.0, -d) for d in deltas]
    avg_gain = sum(gains[:period]) / float(period)
    avg_loss = sum(losses[:period]) / float(period)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / float(period)
        avg_loss = (avg_loss * (period - 1) + losses[i]) / float(period)
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def adx_14(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Computes (ADX, +DI, -DI) using Wilder's smoothing over period=14."""
    n = min(len(highs), len(lows), len(closes))
    if n < 2 * period + 1:
        return None, None, None

    trs, plus_dms, minus_dms = [], [], []
    for i in range(1, n):
        h, l, pc = highs[i], lows[i], closes[i - 1]
        ph, pl = highs[i - 1], lows[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        up = h - ph
        dn = pl - l
        plus_dm = up if (up > dn and up > 0) else 0.0
        minus_dm = dn if (dn > up and dn > 0) else 0.0
        trs.append(tr)
        plus_dms.append(plus_dm)
        minus_dms.append(minus_dm)

    sm_tr = sum(trs[:period])
    sm_plus = sum(plus_dms[:period])
    sm_minus = sum(minus_dms[:period])

    dx_vals = []
    plus_di = 0.0
    minus_di = 0.0
    for i in range(period, len(trs)):
        sm_tr = sm_tr - (sm_tr / period) + trs[i]
        sm_plus = sm_plus - (sm_plus / period) + plus_dms[i]
        sm_minus = sm_minus - (sm_minus / period) + minus_dms[i]
        if sm_tr == 0:
            continue
        plus_di = 100.0 * (sm_plus / sm_tr)
        minus_di = 100.0 * (sm_minus / sm_tr)
        denom = plus_di + minus_di
        dx = 100.0 * abs(plus_di - minus_di) / denom if denom > 0 else 0.0
        dx_vals.append(dx)

    if len(dx_vals) < period:
        return None, None, None
    adx = sum(dx_vals[:period]) / float(period)
    for dx in dx_vals[period:]:
        adx = (adx * (period - 1) + dx) / float(period)
    return adx, plus_di, minus_di


def macd(closes: Sequence[float]) -> Tuple[Optional[float], Optional[float]]:
    """MACD Line 1 = EMA12 - EMA26; MACD Line 2 = MACD - EMA9(MACD)."""
    if len(closes) < 35:
        return None, None
    e12 = ema_series(closes, 12)
    e26 = ema_series(closes, 26)
    offset = len(e12) - len(e26)
    macd_series = [e12[offset + i] - e26[i] for i in range(len(e26))]
    sig_series = ema_series(macd_series, 9)
    if not sig_series:
        return macd_series[-1], None
    return macd_series[-1], macd_series[-1] - sig_series[-1]


def bollinger_bands(closes: Sequence[float], period: int = 20, num_sd: float = 2.0) -> Optional[Tuple[float, float, float]]:
    """Returns (Upper Band, Middle SMA, Lower Band) over period."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    mean = sum(window) / float(period)
    variance = sum((x - mean) ** 2 for x in window) / float(period)
    sd = math.sqrt(variance)
    return (mean + num_sd * sd, mean, mean - num_sd * sd)


def bollinger_distances(closes: Sequence[float], period: int = 20) -> Tuple[Optional[float], Optional[float]]:
    """Returns (% From Upper BB, % From Lower BB) = (Close/Band - 1) * 100."""
    bb = bollinger_bands(closes, period=period)
    if not bb:
        return None, None
    upper, _, lower = bb
    c = closes[-1]
    u_pct = ((c / upper) - 1.0) * 100.0 if upper > 0 else None
    l_pct = ((c / lower) - 1.0) * 100.0 if lower > 0 else None
    return u_pct, l_pct


def parabolic_sar(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    af_start: float = 0.02,
    af_step: float = 0.02,
    af_max: float = 0.20,
) -> Optional[float]:
    """Returns % distance of latest Close from Parabolic SAR = (Close / SAR - 1) * 100."""
    n = min(len(highs), len(lows), len(closes))
    if n < 5:
        return None
    bull = closes[1] >= closes[0]
    sar = lows[0] if bull else highs[0]
    ep = highs[1] if bull else lows[1]
    af = af_start

    for i in range(2, n):
        sar = sar + af * (ep - sar)
        if bull:
            sar = min(sar, lows[i - 1], lows[i - 2])
            if lows[i] < sar:
                bull = False
                sar = ep
                ep = lows[i]
                af = af_start
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af_max, af + af_step)
        else:
            sar = max(sar, highs[i - 1], highs[i - 2])
            if highs[i] > sar:
                bull = True
                sar = ep
                ep = highs[i]
                af = af_start
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af_max, af + af_step)

    if sar <= 0:
        return None
    return ((closes[-1] / sar) - 1.0) * 100.0


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


def stochastic_d(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], k_period: int = 14, d_period: int = 3) -> Optional[float]:
    """Stochastic %D = SMA3(%K)."""
    n = min(len(highs), len(lows), len(closes))
    if n < k_period + d_period - 1:
        return None
    ks = []
    for end in range(n - d_period + 1, n + 1):
        val = stochastic_k(highs[:end], lows[:end], closes[:end], period=k_period)
        if val is None:
            return None
        ks.append(val)
    return sum(ks) / float(len(ks))


def supertrend(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    atr_period: int = 10,
    multiplier: float = 3.0,
) -> Tuple[Optional[float], Optional[int]]:
    """SuperTrend (ATR 10, mult 3): returns (signed % distance (Close / SuperTrend - 1) * 100, trend 1/-1)."""
    n = min(len(highs), len(lows), len(closes))
    if n < atr_period + 2:
        return None, None

    trs = [highs[0] - lows[0]]
    for i in range(1, n):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))

    atrs = [0.0] * n
    atrs[atr_period - 1] = sum(trs[:atr_period]) / float(atr_period)
    for i in range(atr_period, n):
        atrs[i] = (atrs[i - 1] * (atr_period - 1) + trs[i]) / float(atr_period)

    final_ub = [0.0] * n
    final_lb = [0.0] * n
    trend = [1] * n
    st_val = [0.0] * n

    for i in range(atr_period - 1, n):
        hl2 = (highs[i] + lows[i]) / 2.0
        basic_ub = hl2 + multiplier * atrs[i]
        basic_lb = hl2 - multiplier * atrs[i]
        if i == atr_period - 1:
            final_ub[i] = basic_ub
            final_lb[i] = basic_lb
            trend[i] = 1
            st_val[i] = final_lb[i]
        else:
            final_ub[i] = basic_ub if (basic_ub < final_ub[i - 1] or closes[i - 1] > final_ub[i - 1]) else final_ub[i - 1]
            final_lb[i] = basic_lb if (basic_lb > final_lb[i - 1] or closes[i - 1] < final_lb[i - 1]) else final_lb[i - 1]
            if trend[i - 1] == 1:
                trend[i] = -1 if closes[i] < final_lb[i] else 1
            else:
                trend[i] = 1 if closes[i] > final_ub[i] else -1
            st_val[i] = final_lb[i] if trend[i] == 1 else final_ub[i]

    last_st = st_val[-1]
    if last_st <= 0:
        return None, trend[-1]
    pct_dist = ((closes[-1] / last_st) - 1.0) * 100.0
    return pct_dist, trend[-1]


def relative_volume(volumes: Sequence[float], short_win: int = 10, long_win: int = 91) -> Optional[float]:
    """Relative Volume = avg_vol(10D) / avg_vol(91D)."""
    if len(volumes) < long_win or short_win <= 0 or long_win <= 0:
        return None
    avg_short = sum(volumes[-short_win:]) / float(short_win)
    avg_long = sum(volumes[-long_win:]) / float(long_win)
    if avg_long <= 0:
        return None
    return avg_short / avg_long


def max_drawdown_1y(closes: Sequence[float], lookback: int = 250) -> Optional[float]:
    """1Y Max Loss: worst peak-to-trough drawdown where peak occurs before trough."""
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
    """Annualized volatility of daily log returns over lookback days (* sqrt(252) * 100)."""
    if len(daily_closes) < lookback + 1:
        return None
    sub = daily_closes[-(lookback + 1):]
    log_returns = [math.log(sub[i] / sub[i - 1]) for i in range(1, len(sub)) if sub[i - 1] > 0 and sub[i] > 0]
    n = len(log_returns)
    if n < 2:
        return None
    mean_r = sum(log_returns) / float(n)
    var = sum((r - mean_r) ** 2 for r in log_returns) / float(n - 1)
    return math.sqrt(var) * math.sqrt(252.0) * 100.0


def beta_and_alpha(
    stock_weekly_closes: Sequence[float],
    benchmark_weekly_closes: Sequence[float],
    lookback_weeks: int = 104,
) -> Tuple[Optional[float], Optional[float]]:
    """Beta = cov(r_stock, r_bench) / var(r_bench) over 104 weekly closes.
    Alpha = total stock return - total benchmark return (simple excess return).
    """
    if len(stock_weekly_closes) < lookback_weeks + 1 or len(benchmark_weekly_closes) < lookback_weeks + 1:
        return None, None
    s_closes = stock_weekly_closes[-(lookback_weeks + 1):]
    b_closes = benchmark_weekly_closes[-(lookback_weeks + 1):]

    r_s = [s_closes[i] / s_closes[i - 1] - 1.0 for i in range(1, len(s_closes))]
    r_b = [b_closes[i] / b_closes[i - 1] - 1.0 for i in range(1, len(b_closes))]

    mean_s = sum(r_s) / float(len(r_s))
    mean_b = sum(r_b) / float(len(b_closes) - 1)

    cov = sum((r_s[i] - mean_s) * (r_b[i] - mean_b) for i in range(len(r_s))) / float(len(r_s) - 1)
    var_b = sum((r_b[i] - mean_b) ** 2 for i in range(len(r_b))) / float(len(r_b) - 1)

    if var_b <= 0:
        return None, None
    beta = cov / var_b
    tot_s = (s_closes[-1] / s_closes[0] - 1.0) * 100.0
    tot_b = (b_closes[-1] / b_closes[0] - 1.0) * 100.0
    return beta, tot_s - tot_b


def sharpe_ratio(excess_return: float, volatility: float) -> Optional[float]:
    """Sharpe Ratio = (Stock Return - Benchmark Return) / Volatility."""
    if volatility <= 0:
        return None
    return excess_return / volatility


def return_window(closes: Sequence[float], days: int) -> Optional[float]:
    """Price return over trailing `days` trading sessions (%)."""
    if len(closes) <= days or days <= 0:
        return None
    prev = closes[-1 - days]
    if prev <= 0:
        return None
    return ((closes[-1] / prev) - 1.0) * 100.0
