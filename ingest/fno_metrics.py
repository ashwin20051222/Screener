"""ingest/fno_metrics.py
Computes all Section 10.6 Futures & Options derived metrics from stored UDiFF F&O bhavcopies,
cash spot closes (px_daily), lot sizes (ref_fno_lot), and manual FBIL 3M MIBOR (ref_fbil_mibor).
Non-F&O-eligible stocks remain NULL; missing FBIL MIBOR marks fair_value fields NULL cleanly.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from app import db
from app.metrics.formulas import (
    cash_and_carry_profit,
    fair_value_spread,
    futures_basis,
    futures_fair_value,
    oi_change_pct,
    percentage_rollover,
    put_call_ratio,
    rollover_cost,
)

log = logging.getLogger(__name__)


def compute_fno_metrics_for_date(con, target_date: Optional[date] = None, source: str = "NSE") -> dict:
    """Computes and upserts fno_metrics_daily for all F&O underlyings on target_date."""
    if target_date is None:
        r = con.execute("SELECT max(date) FROM fno_daily WHERE source = ?", [source]).fetchone()
        if not r or not r[0]:
            return {"status": "skip", "message": "no fno_daily rows"}
        target_date = r[0]

    # Previous 1D and 1W (5th prior trading day) dates in fno_daily
    dates_rows = con.execute(
        "SELECT DISTINCT date FROM fno_daily WHERE source = ? AND date <= ? ORDER BY date DESC LIMIT 6",
        [source, target_date],
    ).fetchall()
    avail_dates = [r[0] for r in dates_rows]
    d_1d = avail_dates[1] if len(avail_dates) >= 2 else None
    d_1w = avail_dates[5] if len(avail_dates) >= 6 else (avail_dates[-1] if len(avail_dates) >= 2 else None)

    # Fetch latest FBIL 3M MIBOR rate
    mibor_row = con.execute(
        "SELECT rate_pct, rate_date FROM ref_fbil_mibor WHERE tenor = 'mibor_3m' AND rate_date <= ? ORDER BY rate_date DESC LIMIT 1",
        [target_date],
    ).fetchone()
    r_mibor = (float(mibor_row[0]) / 100.0) if mibor_row else None

    # Fetch spot close prices for target_date
    spot_rows = con.execute(
        "SELECT symbol, close FROM px_daily WHERE source = ? AND date = ?",
        [source, target_date],
    ).fetchall()
    spot_map: Dict[str, float] = {sym: float(c) for sym, c in spot_rows if c is not None}

    # Fetch lot sizes
    lot_rows = con.execute(
        """
        SELECT symbol, lot_size
        FROM ref_fno_lot
        QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY as_of DESC) = 1
        """
    ).fetchall()
    lot_map: Dict[str, Optional[int]] = {sym: l for sym, l in lot_rows}

    # Fetch all FO contracts for target_date
    fo_rows = con.execute(
        """
        SELECT underlying, expiry, instrument, option_type, strike, close, oi, volume, new_lot
        FROM fno_daily
        WHERE source = ? AND date = ? AND expiry >= ?
        ORDER BY underlying, expiry
        """,
        [source, target_date, target_date],
    ).fetchall()

    by_und: Dict[str, List[tuple]] = {}
    for row in fo_rows:
        by_und.setdefault(row[0], []).append(row)

    # Helper to load prior day/week totals & per-strike CE/PE OI
    def _load_prior_oi(prior_date: Optional[date]):
        fut_agg: Dict[str, Dict[str, float]] = {}
        opt_agg: Dict[str, Dict[str, float]] = {}
        strike_oi: Dict[str, Dict[tuple, int]] = {}
        if prior_date is None:
            return fut_agg, opt_agg, strike_oi

        rows = con.execute(
            """
            SELECT underlying, expiry, instrument, option_type, strike, oi, volume
            FROM fno_daily
            WHERE source = ? AND date = ? AND expiry >= ?
            ORDER BY underlying, expiry
            """,
            [source, prior_date, prior_date],
        ).fetchall()
        futs_by_u: Dict[str, List[tuple]] = {}
        for u, exp, inst, opt_tp, strike, oi, vol in rows:
            if inst in ("STF", "IDF"):
                futs_by_u.setdefault(u, []).append((exp, oi or 0, vol or 0))
            elif inst in ("STO", "IDO") and opt_tp in ("CE", "PE"):
                oa = opt_agg.setdefault(u, {"CE": 0, "PE": 0})
                oa[opt_tp] += (oi or 0)
                if strike is not None:
                    sk = strike_oi.setdefault(u, {})
                    key = (opt_tp, float(strike))
                    sk[key] = sk.get(key, 0) + (oi or 0)
        for u, flist in futs_by_u.items():
            flist.sort(key=lambda x: x[0])
            fut_agg[u] = {"oi": flist[0][1], "volume": flist[0][2]}
        return fut_agg, opt_agg, strike_oi

    fut_1d, opt_1d, strike_1d = _load_prior_oi(d_1d)
    fut_1w, opt_1w, strike_1w = _load_prior_oi(d_1w)

    out_rows: List[Dict[str, Any]] = []
    for und, contracts in by_und.items():
        futs = [c for c in contracts if c[2] in ("STF", "IDF") and c[5] is not None]
        futs.sort(key=lambda c: c[1])  # sort by expiry asc
        opts = [c for c in contracts if c[2] in ("STO", "IDO") and c[3] in ("CE", "PE")]

        near_fut = futs[0] if len(futs) >= 1 else None
        next_fut = futs[1] if len(futs) >= 2 else None
        far_fut = futs[2] if len(futs) >= 3 else None

        fut_close = float(near_fut[5]) if near_fut else None
        fut_vol = int(near_fut[7]) if near_fut and near_fut[7] is not None else None
        fut_oi = int(near_fut[6]) if near_fut and near_fut[6] is not None else None
        near_exp = near_fut[1] if near_fut else None
        lot_sz = lot_map.get(und) or (near_fut[8] if near_fut and near_fut[8] else None)

        spot = spot_map.get(und)
        basis_val = futures_basis(fut_close, spot)

        if r_mibor is not None and spot is not None and near_exp is not None:
            days_exp = max(0, (near_exp - target_date).days)
            fv_val = futures_fair_value(spot, r_mibor, days_exp)
            fvs_val = fair_value_spread(fv_val, fut_close)
            ccp_val = cash_and_carry_profit(fut_close, fv_val)
            fv_status = "computed"
        else:
            fv_val = None
            fvs_val = None
            ccp_val = None
            fv_status = "Unavailable: missing FBIL MIBOR" if r_mibor is None else "Unavailable: missing spot/expiry"

        next_close = float(next_fut[5]) if next_fut and next_fut[5] is not None else None
        roll_cost = rollover_cost(next_close, fut_close)
        cal_spread = (next_close - fut_close) if (next_close is not None and fut_close is not None) else None

        oi_near = float(near_fut[6] or 0) if near_fut else None
        oi_next = float(next_fut[6] or 0) if next_fut else None
        oi_far = float(far_fut[6] or 0) if far_fut else 0.0
        pct_roll = percentage_rollover(oi_next, oi_near, oi_far)

        # Future OI/Vol 1D and 1W changes
        p1_f = fut_1d.get(und, {})
        p5_f = fut_1w.get(und, {})
        chg_1d_foi = oi_change_pct(fut_oi, p1_f.get("oi"))
        chg_1w_foi = oi_change_pct(fut_oi, p5_f.get("oi"))
        chg_1d_fvol = oi_change_pct(fut_vol, p1_f.get("volume"))
        chg_1w_fvol = oi_change_pct(fut_vol, p5_f.get("volume"))

        # Options aggregations across strikes and expiries
        ce_by_strike: Dict[float, int] = {}
        pe_by_strike: Dict[float, int] = {}
        ce_total = 0
        pe_total = 0
        for _, _, _, opt_tp, strike, _, oi, _, _ in opts:
            oi_i = int(oi or 0)
            if opt_tp == "CE":
                ce_total += oi_i
                if strike is not None:
                    st_f = float(strike)
                    ce_by_strike[st_f] = ce_by_strike.get(st_f, 0) + oi_i
            elif opt_tp == "PE":
                pe_total += oi_i
                if strike is not None:
                    st_f = float(strike)
                    pe_by_strike[st_f] = pe_by_strike.get(st_f, 0) + oi_i

        pcr_val = put_call_ratio(pe_total if opts else None, ce_total if opts else None)
        p1_o = opt_1d.get(und, {})
        p5_o = opt_1w.get(und, {})
        chg_1d_ce = oi_change_pct(ce_total if opts else None, p1_o.get("CE"))
        chg_1w_ce = oi_change_pct(ce_total if opts else None, p5_o.get("CE"))
        chg_1d_pe = oi_change_pct(pe_total if opts else None, p1_o.get("PE"))
        chg_1w_pe = oi_change_pct(pe_total if opts else None, p5_o.get("PE"))

        hi_ce_strike = max(ce_by_strike.items(), key=lambda kv: kv[1])[0] if ce_by_strike else None
        hi_pe_strike = max(pe_by_strike.items(), key=lambda kv: kv[1])[0] if pe_by_strike else None

        def _best_oi_chg_strike(cur_map: Dict[float, int], prior_map: Dict[tuple, int], tp: str) -> Optional[float]:
            best_s = None
            best_pct = None
            for st_f, cur_oi in cur_map.items():
                prev_oi = prior_map.get((tp, st_f), 0)
                if prev_oi > 0 and cur_oi > prev_oi:
                    pct = (cur_oi / prev_oi - 1.0) * 100.0
                    if best_pct is None or pct > best_pct:
                        best_pct = pct
                        best_s = st_f
            return best_s

        s1_map = strike_1d.get(und, {})
        s5_map = strike_1w.get(und, {})
        hi_1d_ce = _best_oi_chg_strike(ce_by_strike, s1_map, "CE")
        hi_1d_pe = _best_oi_chg_strike(pe_by_strike, s1_map, "PE")
        hi_1w_ce = _best_oi_chg_strike(ce_by_strike, s5_map, "CE")
        hi_1w_pe = _best_oi_chg_strike(pe_by_strike, s5_map, "PE")

        out_rows.append({
            "source": source,
            "underlying": und,
            "date": target_date,
            "lot_size": lot_sz,
            "future_close_price": fut_close,
            "future_volume": fut_vol,
            "future_open_interest": fut_oi,
            "chg_1d_future_oi": chg_1d_foi,
            "chg_1w_future_oi": chg_1w_foi,
            "chg_1d_future_volume": chg_1d_fvol,
            "chg_1w_future_volume": chg_1w_fvol,
            "basis": basis_val,
            "fair_value": fv_val,
            "fair_value_spread": fvs_val,
            "cash_carry_profit": ccp_val,
            "rollover_cost": roll_cost,
            "percentage_rollover": pct_roll,
            "calendar_spread": cal_spread,
            "call_open_interest": ce_total if opts else None,
            "put_open_interest": pe_total if opts else None,
            "put_call_ratio": pcr_val,
            "chg_1d_call_oi": chg_1d_ce,
            "chg_1w_call_oi": chg_1w_ce,
            "chg_1d_put_oi": chg_1d_pe,
            "chg_1w_put_oi": chg_1w_pe,
            "highest_call_oi_strike": hi_ce_strike,
            "highest_put_oi_strike": hi_pe_strike,
            "highest_1d_oi_chg_ce_strike": hi_1d_ce,
            "highest_1d_oi_chg_pe_strike": hi_1d_pe,
            "highest_1w_oi_chg_ce_strike": hi_1w_ce,
            "highest_1w_oi_chg_pe_strike": hi_1w_pe,
            "fair_value_status": fv_status,
        })

    n = db.upsert_rows(con, "fno_metrics_daily", out_rows, keys=["source", "underlying", "date"])
    return {"status": "ok", "date": str(target_date), "rows": n}
