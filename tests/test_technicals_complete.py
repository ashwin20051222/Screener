"""tests/test_technicals_complete.py
Tests all Step 4.6 Technical Indicators & trailing Price/Volume metrics pipeline.
"""
from __future__ import annotations

from datetime import date, timedelta
import duckdb
import pytest

from app import db
from app.metrics.technicals import (
    ad_1w_change,
    ad_line_series,
    adx_14,
    annualized_volatility,
    beta_and_alpha,
    bollinger_distances,
    macd,
    max_drawdown_1y,
    obv_1w_change,
    parabolic_sar,
    relative_volume,
    return_window,
    rsi_14d,
    rsi_exponential_14d,
    stochastic_d,
    stochastic_k,
    supertrend,
    williams_r,
)
from ingest.technicals_job import compute_technicals_for_symbol, run_technicals_job


@pytest.fixture()
def db_con(tmp_path):
    c = duckdb.connect(str(tmp_path / "tech.duckdb"))
    db.init_schema(c)
    yield c
    c.close()


def _uptrend_series(n: int = 270):
    base_dt = date(2025, 1, 1)
    closes, highs, lows, vols = [], [], [], []
    rows = []
    for i in range(n):
        c = 100.0 + i * 0.4 + (2.0 if i % 5 == 0 else -0.5)
        h = c + 2.5
        l = c - 2.0
        v = 100000 + (i % 7) * 5000
        dt = base_dt + timedelta(days=i)
        closes.append(c)
        highs.append(h)
        lows.append(l)
        vols.append(v)
        rows.append({
            "symbol": "TESTSTK",
            "date": dt,
            "open": c - 0.5,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        })
    return rows, highs, lows, closes, vols


def test_all_technical_indicators_compute_cleanly():
    rows, highs, lows, closes, vols = _uptrend_series(270)
    r_s = rsi_14d(closes, 14)
    r_e = rsi_exponential_14d(closes, 14)
    assert r_s is not None and 50 < r_s <= 100
    assert r_e is not None and 50 < r_e <= 100

    adx_v, pdi, mdi = adx_14(highs, lows, closes, 14)
    assert adx_v is not None and pdi is not None and mdi is not None
    assert pdi > mdi  # sustained uptrend

    m1, m2 = macd(closes)
    assert m1 is not None and m2 is not None

    u_bb, l_bb = bollinger_distances(closes, 20)
    assert u_bb is not None and l_bb is not None and u_bb < l_bb

    sar = parabolic_sar(highs, lows, closes)
    assert sar is not None

    st_pct, st_sig = supertrend(highs, lows, closes)
    assert st_pct is not None and st_sig in (1, -1)

    sd = stochastic_d(highs, lows, closes, 14, 3)
    assert sd is not None and 0 <= sd <= 100

    ad_s = ad_line_series(highs, lows, closes, vols)
    assert len(ad_s) == 270
    assert ad_1w_change(highs, lows, closes, vols) is not None
    assert obv_1w_change(closes, vols) is not None
    assert relative_volume(vols) is not None
    assert max_drawdown_1y(closes) <= 0.0
    assert annualized_volatility(closes, 200) > 0.0
    assert return_window(closes, 20) > 0.0


def test_technicals_job_with_corp_actions_and_nifty(db_con):
    rows, _, _, _, _ = _uptrend_series(550)
    # Insert TESTSTK and NIFTY 50 into px_daily
    px_rows = []
    for i, r in enumerate(rows):
        px_rows.append({
            "source": "NSE",
            "date": r["date"],
            "symbol": "TESTSTK",
            "series": "EQ",
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"],
        })
        px_rows.append({
            "source": "NSE",
            "date": r["date"],
            "symbol": "NIFTY 50",
            "series": "EQ",
            "open": 20000 + i * 5,
            "high": 20050 + i * 5,
            "low": 19950 + i * 5,
            "close": 20000 + i * 5,
            "volume": 1000000,
        })
    db.upsert_rows(db_con, "px_daily", px_rows, keys=["source", "symbol", "date", "series"])

    res = run_technicals_job(db_con, source="NSE")
    assert res["status"] == "ok" and res["rows"] == 2

    snap = db_con.execute(
        """
        SELECT sma_200d, ema_200d, adx_rating, beta, alpha, sharpe_ratio, ret_1m, ret_1m_vs_nifty
        FROM tech_daily WHERE symbol = 'TESTSTK'
        """
    ).fetchone()
    assert snap[0] is not None and snap[1] is not None and snap[2] is not None
    assert snap[3] is not None  # beta over 104+ weekly points (550 days -> 110 weekly points!)
    assert snap[4] is not None  # alpha
    assert snap[6] is not None and snap[7] is not None

    # Re-run with incremental=True -> skips both symbols cleanly without recompute
    res_inc = run_technicals_job(db_con, source="NSE", incremental=True)
    assert res_inc["rows"] == 0
    assert res_inc["skipped_incremental"] == 2


def test_backfill_holidays_cache_skip_resume_abort_and_short_history(db_con, tmp_path, monkeypatch):
    from app import config
    from ingest import backfill as bf_mod
    from ingest.http import FetchResult
    import io, zipfile

    monkeypatch.setattr(config, "data_path", lambda rel: tmp_path / rel)
    # Seed 10 days of NEWIPO directly into px_daily to verify short history returns None (not 0) for SMA200/1Y return
    new_px = []
    for i in range(10):
        new_px.append({
            "source": "NSE", "date": date(2026, 11, 2) - timedelta(days=9 - i),
            "symbol": "NEWIPO", "series": "EQ", "open": 100.0 + i, "high": 102.0 + i,
            "low": 99.0 + i, "close": 101.0 + i, "volume": 10000,
        })
    db.upsert_rows(db_con, "px_daily", new_px, keys=["source", "symbol", "date", "series"])

    def _make_udiff_zip(d: date, close_px: float) -> bytes:
        buf = io.BytesIO()
        csv_txt = (
            "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,"
            "StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,"
            "OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4\n"
            f"{d},{d},CM,NSE,STK,1,INE001,INFY,EQ,,,0,,INFOSYS,{close_px},{close_px+1},{close_px-1},{close_px},{close_px},{close_px-0.5},,,0,0,50000,50000000,100,F,1,,,,,\n"
        )
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"BhavCopy_NSE_CM_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv", csv_txt)
        return buf.getvalue()

    calls = []
    def fake_fetch(url, **kwargs):
        calls.append(url)
        if "20261106" in url:  # Friday -> 404 holiday
            return FetchResult(404, None, url, error="http:404")
        if "20261105" in url:  # Thursday -> ok
            return FetchResult(200, _make_udiff_zip(date(2026, 11, 5), 1500.0), url)
        if "20261104" in url:  # Wednesday -> 403 stop immediately
            return FetchResult(403, None, url, error="http:403")
        return FetchResult(404, None, url, error="http:404")

    monkeypatch.setattr(bf_mod.http, "fetch", fake_fetch)
    res = bf_mod.backfill_prices(
        db_con, trading_days=5, fo_days=0, resume=True, sync_actions=False, start_date=date(2026, 11, 8),  # Sunday -> skip Sat/Sun
    )
    assert res["blocked"] is True
    # Weekends (Nov 7, Nov 8) skipped without network; Nov 6 holiday (404), Nov 5 ok, Nov 4 403 -> stopped
    assert not any("20261107" in u or "20261108" in u for u in calls)
    assert any("20261106" in u for u in calls)
    assert res["cm_holidays_marked"] >= 1
    prog_hol = db.get_progress_keys(db_con, "backfill_cm", statuses=("holiday",))
    assert "2026-11-06" in prog_hol

    # Insufficient history check: NEWIPO has sma_10d populated, sma_200d and ret_1y strictly None (never 0)
    short_row = db_con.execute(
        "SELECT sma_10d, sma_200d, ret_1d, ret_1y, away_52w_high FROM tech_daily WHERE symbol = 'NEWIPO'"
    ).fetchone()
    assert short_row[0] is not None
    assert short_row[1] is None
    assert short_row[2] is not None
    assert short_row[3] is None
    assert short_row[4] is not None  # >= 2 days present

