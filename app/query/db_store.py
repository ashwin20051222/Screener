"""app/query/db_store.py
Assembles complete stock rows from DuckDB tables (`ref_security`, `px_daily`, `tech_daily`,
`fno_metrics_daily`, `ref_amfi_classification`, `etf_meta`, ownership, financials, quant scores)
with strict provenance (source + as_of date) on every metric. Never fabricates data when DB is empty.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app import db
from app.metrics.benchmarks import BenchmarkEngine
from app.metrics.scores import compute_all_quant_scores
from ingest.financials import compute_fundamental_metrics
from ingest.ownership import compute_ownership_snapshot

log = logging.getLogger(__name__)

CANONICAL_INDICES = [
    ("nifty50", "NIFTY50", "Nifty 50"),
    ("niftynext50", "NIFTYNEXT50", "Nifty Next 50"),
    ("nifty100", "NIFTY100", "Nifty 100"),
    ("nifty200", "NIFTY200", "Nifty 200"),
    ("nifty500", "NIFTY500", "Nifty 500"),
    ("niftymidcap100", "NIFTYMIDCAP100", "Nifty Midcap 100"),
    ("niftymidcap150", "NIFTYMIDCAP150", "Nifty Midcap 150"),
    ("niftysmallcap100", "NIFTYSMALLCAP100", "Nifty Smallcap 100"),
    ("niftysmallcap250", "NIFTYSMALLCAP250", "Nifty Smallcap 250"),
]


def get_universes_summary(con=None) -> List[Dict[str, Any]]:
    """Returns canonical index universe metadata from latest ref_index_constituent snapshot + All listed."""
    own = con is None
    if con is None:
        from app.config import data_path, settings
        db_p = data_path(settings()["data"]["db_path"])
        if not db_p.exists():
            return [
                {"id": cid, "label": lbl, "slug": slug, "count": 0, "as_of": None}
                for cid, slug, lbl in CANONICAL_INDICES
            ] + [{"id": "all_listed", "label": "All NSE + BSE listed", "slug": "ALL", "count": 0, "as_of": None}]
        try:
            con = db.connect(read_only=True)
        except Exception as exc:
            log.warning("DuckDB busy during get_universes_summary: %s", exc)
            return [
                {"id": cid, "label": lbl, "slug": slug, "count": 0, "as_of": None}
                for cid, slug, lbl in CANONICAL_INDICES
            ] + [{"id": "all_listed", "label": "All NSE + BSE listed", "slug": "ALL", "count": 0, "as_of": None}]

    try:
        idx_stats: Dict[str, tuple] = {}
        try:
            for idx_nm, cnt, dt in con.execute(
                """
                SELECT r.index_name, COUNT(DISTINCT r.symbol), MAX(r.as_of)
                FROM ref_index_constituent r
                JOIN (
                    SELECT index_name, MAX(as_of) AS max_as_of
                    FROM ref_index_constituent
                    GROUP BY index_name
                ) latest
                  ON r.index_name = latest.index_name AND r.as_of = latest.max_as_of
                GROUP BY r.index_name
                """
            ).fetchall():
                idx_stats[str(idx_nm).upper()] = (int(cnt), str(dt) if dt else None)
        except Exception:
            idx_stats = {}

        total_listed = 0
        max_sec_dt = None
        try:
            sec_stat = con.execute(
                """
                SELECT COUNT(*), MAX(CAST(updated_at AS DATE))
                FROM ref_security
                WHERE COALESCE(listing_status, 'listed') <> 'delisted' AND name IS NOT NULL
                """
            ).fetchone()
            if sec_stat:
                total_listed = int(sec_stat[0] or 0)
                max_sec_dt = str(sec_stat[1]) if sec_stat[1] else None
        except Exception:
            pass

        seen_slugs = set()
        out: List[Dict[str, Any]] = []
        for cid, slug, lbl in CANONICAL_INDICES:
            cnt, dt = idx_stats.get(slug, (0, None))
            seen_slugs.add(slug)
            out.append({"id": cid, "label": lbl, "slug": slug, "count": cnt, "as_of": dt})

        for slug, (cnt, dt) in sorted(idx_stats.items()):
            if slug not in seen_slugs:
                out.append({
                    "id": slug.lower(),
                    "label": slug,
                    "slug": slug,
                    "count": cnt,
                    "as_of": dt,
                })

        out.append({
            "id": "all_listed",
            "label": "All NSE + BSE listed",
            "slug": "ALL",
            "count": total_listed,
            "as_of": max_sec_dt,
        })
        return out
    finally:
        if own:
            con.close()


def load_market_dataset_from_db(con=None) -> Dict[str, Any]:
    """Loads full listed market dataset from DuckDB if synced; returns empty rows when DB has no data."""
    own = con is None
    if con is None:
        from app.config import data_path, settings
        db_p = data_path(settings()["data"]["db_path"])
        if not db_p.exists():
            return {"synced": False, "rows": [], "universes": {}, "as_of": {}}
        try:
            con = db.connect(read_only=True)
        except Exception as exc:
            log.warning("DuckDB busy during load_market_dataset_from_db: %s", exc)
            return {"synced": False, "sync_in_progress": True, "rows": [], "universes": {}, "as_of": {}}

    try:
        sec_rows = con.execute(
            """
            SELECT security_id, isin, nse_symbol, bse_code, name, face_value, shares_outstanding,
                   shares_source, shares_as_of,
                   sector, sub_sector, industry, financial_template, is_financial_institution,
                   is_etf, is_sme, fno_eligible
            FROM ref_security
            WHERE COALESCE(listing_status, 'listed') <> 'delisted'
              AND name IS NOT NULL
            """
        ).fetchall()
        if not sec_rows:
            return {"synced": False, "rows": [], "universes": {}, "as_of": {}}

        # Latest px_daily per symbol and per isin (NSE preferred over BSE if both exist)
        px_map: Dict[str, tuple] = {}
        px_by_isin: Dict[str, tuple] = {}
        for r in con.execute(
            """
            SELECT symbol, isin, date, close, volume, wap, source
            FROM px_daily
            QUALIFY ROW_NUMBER() OVER (PARTITION BY COALESCE(isin, symbol) ORDER BY CASE WHEN source = 'NSE' THEN 0 ELSE 1 END, date DESC) = 1
            """
        ).fetchall():
            if r[0]:
                px_map.setdefault(r[0], r)
            if r[1]:
                px_by_isin.setdefault(r[1], r)

        px_days_map: Dict[str, int] = dict(
            con.execute(
                "SELECT symbol, COUNT(DISTINCT date) FROM px_daily WHERE source = 'NSE' GROUP BY symbol"
            ).fetchall()
        )
        max_px_days = max(px_days_map.values()) if px_days_map else 0

        # Latest tech_daily per symbol
        tech_df = con.execute(
            "SELECT * FROM tech_daily QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) = 1"
        ).fetchdf()
        tech_map: Dict[str, Dict[str, Any]] = {
            r["symbol"]: r for r in tech_df.to_dict("records")
        } if len(tech_df) > 0 else {}

        # Latest fno_metrics_daily per underlying
        fno_df = con.execute(
            "SELECT * FROM fno_metrics_daily QUALIFY ROW_NUMBER() OVER (PARTITION BY underlying ORDER BY date DESC) = 1"
        ).fetchdf()
        fno_map: Dict[str, Dict[str, Any]] = {
            r["underlying"]: r for r in fno_df.to_dict("records")
        } if len(fno_df) > 0 else {}

        # AMFI latest categorisation
        amfi_map: Dict[str, tuple] = {}
        for isin, rank, cls, avg_mc, dt in con.execute(
            "SELECT isin, rank, classification, avg_mcap_crs, as_of_date FROM ref_amfi_classification QUALIFY ROW_NUMBER() OVER (PARTITION BY isin ORDER BY as_of_date DESC) = 1"
        ).fetchall():
            amfi_map[isin] = (rank, cls, avg_mc, dt)

        # ETF metadata
        etf_map: Dict[str, tuple] = {}
        for sym, er, er_dt, te, te_dt in con.execute(
            "SELECT symbol, expense_ratio, ter_as_of, tracking_error, te_as_of FROM etf_meta"
        ).fetchall():
            etf_map[sym] = (er, er_dt, te, te_dt)

        # Index memberships from latest snapshot per index
        univ_members: Dict[str, List[str]] = {}
        for idx_nm, sym in con.execute(
            """
            SELECT DISTINCT r.index_name, r.symbol
            FROM ref_index_constituent r
            JOIN (
                SELECT index_name, MAX(as_of) AS max_as_of
                FROM ref_index_constituent
                GROUP BY index_name
            ) latest
              ON r.index_name = latest.index_name AND r.as_of = latest.max_as_of
            """
        ).fetchall():
            univ_members.setdefault(str(idx_nm).upper(), []).append(sym)

        stocks: List[Dict[str, Any]] = []
        for s in sec_rows:
            (sid, isin, sym, bse_code, name, fv, sh_out, sh_src, sh_asof,
             sec, sub_sec, ind, tpl, is_fin, is_etf, is_sme, fno_elig) = s
            key_sym = sym or f"BSE:{bse_code}"
            px = (px_map.get(sym) if sym else None) or (px_by_isin.get(isin) if isin else None)
            close_px = float(px[3]) if (px and px[3] is not None) else None
            mc = (close_px * float(sh_out) / 1e7) if (close_px and sh_out) else None

            row: Dict[str, Any] = {
                "security_id": sid,
                "isin": isin,
                "nse_symbol": sym,
                "bse_code": bse_code,
                "name": name,
                "sector": "ETF" if is_etf else (sec or "Unclassified"),
                "sub_sector": sub_sec or ind or ("ETF" if is_etf else "Unclassified"),
                "is_financial_institution": bool(is_fin),
                "is_etf": bool(is_etf),
                "is_sme": bool(is_sme),
                "fno_eligible": bool(fno_elig),
                "face_value": fv,
                "close_price": close_px,
                "daily_volume": int(px[4]) if (px and px[4] is not None) else None,
                "vwap": float(px[5]) if (px and px[5] is not None) else None,
                "market_cap": round(mc, 2) if mc is not None else None,
                "_provenance": {
                    "price_source": px[6] if px else None,
                    "price_as_of": str(px[2]) if px else None,
                    "shares_source": sh_src,
                    "shares_as_of": str(sh_asof) if sh_asof else None,
                    "px_days": int(px_days_map.get(sym, 0)) if sym else 0,
                },
            }

            if isin and isin in amfi_map:
                rank, cls, avg_mc, amfi_dt = amfi_map[isin]
                row["amfi_rank"] = rank
                row["amfi_category"] = cls
                row["amfi_avg_mcap_crs"] = round(float(avg_mc), 2) if avg_mc is not None else None
                row["_provenance"]["amfi_as_of"] = str(amfi_dt)

            if sym and sym in tech_map:
                tm = tech_map[sym]
                for tk in (
                    "sma_10d", "sma_50d", "sma_100d", "sma_200d",
                    "ema_10d", "ema_50d", "ema_100d", "ema_200d",
                    "price_above_1m_sma", "price_above_12m_sma", "price_above_1m_ema",
                    "rsi_14d", "macd_line_1", "macd_line_2", "williams_r",
                    "stochastic_k", "stochastic_d", "volatility", "volatility_vs_nifty",
                    "beta", "alpha", "sharpe_ratio", "relative_volume", "adx_rating",
                ):
                    if tk in tm:
                        row[tk] = tm[tk]
                row["rsi_exponential_14d"] = tm.get("rsi_exp_14d")
                row["1y_max_loss"] = tm.get("max_loss_1y")
                row["from_upper_bollinger_band"] = tm.get("from_upper_bb")
                row["from_lower_bollinger_band"] = tm.get("from_lower_bb")
                row["from_parabolic_sar"] = tm.get("from_parabolic_sar")
                row["1w_change_in_obv"] = tm.get("chg_1w_obv")
                row["1w_change_in_ad_line"] = tm.get("chg_1w_ad_line")
                row["super_trend"] = tm.get("super_trend")
                row["1d_return"] = tm.get("ret_1d")
                row["1w_return"] = tm.get("ret_1w")
                row["1m_return"] = tm.get("ret_1m")
                row["6m_return"] = tm.get("ret_6m")
                row["1y_return"] = tm.get("ret_1y")
                row["5y_cagr"] = tm.get("cagr_5y")
                row["1w_return_vs_nifty"] = tm.get("ret_1w_vs_nifty")
                row["1m_return_vs_nifty"] = tm.get("ret_1m_vs_nifty")
                row["6m_return_vs_nifty"] = tm.get("ret_6m_vs_nifty")
                row["1y_return_vs_nifty"] = tm.get("ret_1y_vs_nifty")
                row["away_from_52w_high"] = tm.get("away_52w_high")
                row["away_from_52w_low"] = tm.get("away_52w_low")
                row["1m_average_volume"] = tm.get("avg_vol_1m")
                row["3m_average_volume"] = tm.get("avg_vol_3m")
                row["1d_change_in_volume"] = tm.get("chg_1d_volume")
                row["1w_change_in_volume"] = tm.get("chg_1w_volume")

            if sym and sym in fno_map:
                fm = fno_map[sym]
                for fk in (
                    "lot_size", "future_close_price", "future_volume", "future_open_interest",
                    "basis", "fair_value", "fair_value_spread", "cash_carry_profit",
                    "rollover_cost", "percentage_rollover", "calendar_spread",
                    "call_open_interest", "put_open_interest", "put_call_ratio",
                    "highest_call_oi_strike", "highest_put_oi_strike",
                ):
                    row[fk] = fm.get(fk)
                row["1d_change_in_future_oi"] = fm.get("chg_1d_future_oi")
                row["1w_change_in_future_oi"] = fm.get("chg_1w_future_oi")
                row["1d_change_in_future_volume"] = fm.get("chg_1d_future_volume")
                row["1w_change_in_future_volume"] = fm.get("chg_1w_future_volume")
                row["1d_change_in_call_oi"] = fm.get("chg_1d_call_oi")
                row["1w_change_in_call_oi"] = fm.get("chg_1w_call_oi")
                row["1d_change_in_put_oi"] = fm.get("chg_1d_put_oi")
                row["1w_change_in_put_oi"] = fm.get("chg_1w_put_oi")
                row["highest_1d_oi_change_ce_strike"] = fm.get("highest_1d_oi_chg_ce_strike")
                row["highest_1d_oi_change_pe_strike"] = fm.get("highest_1d_oi_chg_pe_strike")
                row["highest_1w_oi_change_ce_strike"] = fm.get("highest_1w_oi_chg_ce_strike")
                row["highest_1w_oi_change_pe_strike"] = fm.get("highest_1w_oi_chg_pe_strike")
                row["_provenance"]["fair_value_status"] = fm.get("fair_value_status")

            if sym and sym in etf_map:
                er, er_dt, te, te_dt = etf_map[sym]
                row["expense_ratio"] = er
                row["tracking_error"] = te

            if sym:
                own_snap = compute_ownership_snapshot(con, sym)
                row.update(own_snap)
                fin_snap = compute_fundamental_metrics(con, sym, close_px, sh_out, is_fin)
                if fin_snap.get("statement_type_used"):
                    row["_provenance"]["statement_type"] = fin_snap.pop("statement_type_used")
                    row.update(fin_snap)

            stocks.append(row)

        # Market-wide Sector Benchmarks & Quant Scores
        be = BenchmarkEngine()
        sec_b = be.compute_benchmarks(stocks, group_key="sector")
        sub_b = be.compute_benchmarks(stocks, group_key="sub_sector")
        stocks = [be.enrich_stock_with_benchmarks(r, sec_b, sub_b) for r in stocks]

        q_scores = compute_all_quant_scores(stocks)
        for r in stocks:
            k = str(r.get("nse_symbol") or r.get("name"))
            if k in q_scores:
                r.update(q_scores[k])
                r["_provenance"]["quant_badge"] = "Approximate - computed locally"

        max_px_dt = con.execute("SELECT MAX(date) FROM px_daily").fetchone()[0]
        max_master_dt = con.execute("SELECT MAX(as_of) FROM ref_index_constituent").fetchone()[0]
        max_fin_dt = con.execute("SELECT MAX(fiscal_year_end) FROM fin_annual").fetchone()[0]
        max_shp_dt = con.execute("SELECT MAX(quarter_end) FROM ownership_quarterly").fetchone()[0]
        max_amfi_dt = con.execute("SELECT MAX(as_of_date) FROM ref_amfi_classification").fetchone()[0]
        return {
            "synced": True,
            "rows": stocks,
            "universes": univ_members,
            "as_of": {
                "price": str(max_px_dt) if max_px_dt else None,
                "masters": str(max_master_dt) if max_master_dt else None,
                "filings": str(max_fin_dt or max_shp_dt) if (max_fin_dt or max_shp_dt) else None,
                "amfi": str(max_amfi_dt) if max_amfi_dt else None,
                "max_px_days": int(max_px_days),
            },
        }
    finally:
        if own:
            con.close()

