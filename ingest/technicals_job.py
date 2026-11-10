"""ingest/technicals_job.py
Computes all 33 Technical Indicators + trailing Price & Volume statistics from stored px_daily
adjusted for official splits/bonuses (corp_action), persisted into tech_daily (Step 4.6).
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from app import db
from app.metrics.formulas import cagr
from app.metrics.technicals import (
    ad_1w_change,
    adx_14,
    annualized_volatility,
    beta_and_alpha,
    bollinger_distances,
    ema,
    macd,
    max_drawdown_1y,
    obv_1w_change,
    parabolic_sar,
    pct_above_ma,
    relative_volume,
    return_window,
    rsi_14d,
    rsi_exponential_14d,
    sharpe_ratio,
    sma,
    stochastic_d,
    stochastic_k,
    supertrend,
    williams_r,
)
from ingest.adjuster import adjust_price_series

log = logging.getLogger(__name__)


def _weekly_series(daily_closes: Sequence[float]) -> List[float]:
    """Samples every 5th trading day ending on the latest close."""
    if not daily_closes:
        return []
    return list(reversed(daily_closes[::-5]))


def compute_technicals_for_symbol(
    ohlcv_rows: Sequence[Dict[str, Any]],
    actions: Sequence[Dict[str, Any]],
    nifty_closes: Optional[Sequence[float]] = None,
) -> Optional[Dict[str, Any]]:
    """Computes full technicals & price/volume snapshot dict for the latest date of ohlcv_rows."""
    if not ohlcv_rows:
        return None
    adj = adjust_price_series(ohlcv_rows, actions)
    latest_dt = adj[-1]["date"]
    closes = [float(r["close"]) for r in adj if r.get("close") is not None]
    highs = [float(r.get("high") or r["close"]) for r in adj if r.get("close") is not None]
    lows = [float(r.get("low") or r["close"]) for r in adj if r.get("close") is not None]
    volumes = [float(r.get("volume") or 0.0) for r in adj if r.get("close") is not None]

    if not closes:
        return None
    cur_c = closes[-1]

    sma10 = sma(closes, 10)
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50)
    sma100 = sma(closes, 100)
    sma200 = sma(closes, 200)
    sma250 = sma(closes, 250)

    ema10 = ema(closes, 10)
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema100 = ema(closes, 100)
    ema200 = ema(closes, 200)

    adx_val, p_di, m_di = adx_14(highs, lows, closes, 14)
    m1, m2 = macd(closes)
    u_bb, l_bb = bollinger_distances(closes, 20)
    sar_pct = parabolic_sar(highs, lows, closes)
    st_pct, st_sig = supertrend(highs, lows, closes)

    vol_200 = annualized_volatility(closes, 200)

    ret_1d = return_window(closes, 1)
    ret_1w = return_window(closes, 5)
    ret_1m = return_window(closes, 20)
    ret_6m = return_window(closes, 126)
    ret_1y = return_window(closes, 252)
    cagr_5y = (cagr(closes[-1261], cur_c, 5.0) * 100.0) if len(closes) >= 1261 else None

    vol_vs_nifty = None
    ret_1w_nifty = None
    ret_1m_nifty = None
    ret_6m_nifty = None
    ret_1y_nifty = None
    beta_val = None
    alpha_val = None
    sharpe_val = None

    if nifty_closes:
        n_vol = annualized_volatility(nifty_closes, 200)
        if vol_200 is not None and n_vol is not None:
            vol_vs_nifty = vol_200 - n_vol
        n_1w = return_window(nifty_closes, 5)
        n_1m = return_window(nifty_closes, 20)
        n_6m = return_window(nifty_closes, 126)
        n_1y = return_window(nifty_closes, 252)
        if ret_1w is not None and n_1w is not None:
            ret_1w_nifty = ret_1w - n_1w
        if ret_1m is not None and n_1m is not None:
            ret_1m_nifty = ret_1m - n_1m
        if ret_6m is not None and n_6m is not None:
            ret_6m_nifty = ret_6m - n_6m
        if ret_1y is not None and n_1y is not None:
            ret_1y_nifty = ret_1y - n_1y

        w_stock = _weekly_series(closes)
        w_nifty = _weekly_series(nifty_closes)
        beta_val, alpha_val = beta_and_alpha(w_stock, w_nifty, lookback_weeks=104)
        if len(w_stock) >= 105 and len(w_nifty) >= 105:
            s_w_ret = [w_stock[-105 + i] / w_stock[-105 + i - 1] - 1.0 for i in range(1, 105)]
            b_w_ret = [w_nifty[-105 + i] / w_nifty[-105 + i - 1] - 1.0 for i in range(1, 105)]
            ex_w = [(s - b) * 100.0 for s, b in zip(s_w_ret, b_w_ret)]
            mean_ex = sum(ex_w) / float(len(ex_w))
            sd_ex = math.sqrt(sum((x - mean_ex) ** 2 for x in ex_w) / float(len(ex_w) - 1)) * math.sqrt(52.0)
            if alpha_val is not None and sd_ex > 0:
                sharpe_val = sharpe_ratio(alpha_val, sd_ex)

    win_52w_h = highs[-252:] if len(highs) >= 2 else highs
    win_52w_l = lows[-252:] if len(lows) >= 2 else lows
    high_52 = max(win_52w_h) if win_52w_h else None
    low_52 = min(win_52w_l) if win_52w_l else None
    away_h = ((high_52 / cur_c) - 1.0) * 100.0 if high_52 and cur_c > 0 else None
    away_l = ((cur_c / low_52) - 1.0) * 100.0 if low_52 and low_52 > 0 else None

    avg_v_1m = sma(volumes, 21)
    avg_v_3m = sma(volumes, 63)
    chg_1d_v = ((volumes[-1] / volumes[-2]) - 1.0) * 100.0 if len(volumes) >= 2 and volumes[-2] > 0 else None
    chg_1w_v = ((volumes[-1] / volumes[-6]) - 1.0) * 100.0 if len(volumes) >= 6 and volumes[-6] > 0 else None

    return {
        "symbol": ohlcv_rows[-1].get("symbol", ""),
        "date": latest_dt,
        "close_adj": cur_c,
        "sma_10d": sma10,
        "sma_50d": sma50,
        "sma_100d": sma100,
        "sma_200d": sma200,
        "ema_10d": ema10,
        "ema_50d": ema50,
        "ema_100d": ema100,
        "ema_200d": ema200,
        "price_above_1m_sma": pct_above_ma(cur_c, sma20),
        "price_above_12m_sma": pct_above_ma(cur_c, sma250),
        "price_above_1m_ema": pct_above_ma(cur_c, ema20),
        "rsi_14d": rsi_14d(closes, 14),
        "rsi_exp_14d": rsi_exponential_14d(closes, 14),
        "adx_rating": adx_val,
        "plus_di_14": p_di,
        "minus_di_14": m_di,
        "macd_line_1": m1,
        "macd_line_2": m2,
        "from_upper_bb": u_bb,
        "from_lower_bb": l_bb,
        "from_parabolic_sar": sar_pct,
        "williams_r": williams_r(highs, lows, closes, 14),
        "stochastic_k": stochastic_k(highs, lows, closes, 14),
        "stochastic_d": stochastic_d(highs, lows, closes, 14, 3),
        "chg_1w_obv": obv_1w_change(closes, volumes, 5),
        "chg_1w_ad_line": ad_1w_change(highs, lows, closes, volumes, 5),
        "super_trend": st_pct,
        "supertrend_signal": st_sig,
        "max_loss_1y": max_drawdown_1y(closes, 250),
        "volatility": vol_200,
        "volatility_vs_nifty": vol_vs_nifty,
        "beta": beta_val,
        "alpha": alpha_val,
        "sharpe_ratio": sharpe_val,
        "relative_volume": relative_volume(volumes, 10, 91),
        "ret_1d": ret_1d,
        "ret_1w": ret_1w,
        "ret_1m": ret_1m,
        "ret_6m": ret_6m,
        "ret_1y": ret_1y,
        "cagr_5y": cagr_5y,
        "ret_1w_vs_nifty": ret_1w_nifty,
        "ret_1m_vs_nifty": ret_1m_nifty,
        "ret_6m_vs_nifty": ret_6m_nifty,
        "ret_1y_vs_nifty": ret_1y_nifty,
        "away_52w_high": away_h,
        "away_52w_low": away_l,
        "avg_vol_1m": avg_v_1m,
        "avg_vol_3m": avg_v_3m,
        "chg_1d_volume": chg_1d_v,
        "chg_1w_volume": chg_1w_v,
    }


def run_technicals_job(con, source: str = "NSE") -> dict:
    """Computes technicals across all securities present in px_daily and upserts into tech_daily."""
    rows = con.execute(
        """
        SELECT symbol, date, open, high, low, close, volume
        FROM px_daily
        WHERE source = ? AND close IS NOT NULL
        ORDER BY symbol, date
        """,
        [source],
    ).fetchall()
    if not rows:
        return {"status": "skip", "rows": 0}

    act_rows = con.execute(
        "SELECT symbol, ex_date, purpose FROM corp_action ORDER BY ex_date"
    ).fetchall()
    actions_by_sym: Dict[str, List[Dict[str, Any]]] = {}
    for sym, ex_dt, purp in act_rows:
        actions_by_sym.setdefault(sym, []).append({"ex_date": ex_dt, "purpose": purp})

    by_sym: Dict[str, List[Dict[str, Any]]] = {}
    for sym, dt, o, h, l, c, v in rows:
        by_sym.setdefault(sym, []).append({
            "symbol": sym, "date": dt, "open": o, "high": h, "low": l, "close": c, "volume": v
        })

    nifty_closes = [r["close"] for r in by_sym.get("NIFTY 50", [])] or [r["close"] for r in by_sym.get("NIFTYBEES", [])]

    out = []
    for sym, ohlcv in by_sym.items():
        snap = compute_technicals_for_symbol(ohlcv, actions_by_sym.get(sym, []), nifty_closes=nifty_closes or None)
        if snap:
            out.append(snap)

    n = db.upsert_rows(con, "tech_daily", out, keys=["symbol", "date"])
    return {"status": "ok", "rows": n}
