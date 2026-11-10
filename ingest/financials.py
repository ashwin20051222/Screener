"""ingest/financials.py
Financial statements ingestion (NSE API + XBRL + inbox) & Section 10.2/10.3/10.4/10.8/10.10/10.11
fundamental ratios aggregator. Consolidated statements first with standalone fallback.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional

from app import db
from app.metrics.formulas import (
    avg2,
    avg5,
    cagr,
    cash_conversion_cycle,
    current_ratio,
    debt_to_equity,
    dividend_yield,
    enterprise_value,
    ev_multiple,
    interest_coverage,
    margin,
    pb_ratio,
    pe_ratio,
    price_to_cashflow,
    ps_ratio,
    quick_ratio,
    return_on_assets,
    return_on_equity,
    return_on_investment,
    roce,
    safe_div,
)
from ingest import http
from ingest.http import bootstrap_nse_session, fetch_json
from ingest.xbrl import parse_indas_xbrl

log = logging.getLogger(__name__)


def ingest_financial_xbrl_bytes(
    con,
    payload: bytes,
    *,
    symbol: Optional[str] = None,
    isin: Optional[str] = None,
    statement_type: Optional[str] = None,
    template_type: Optional[str] = None,
    scale_to_cr: Optional[bool] = None,
    report_period: Optional[str] = None,
    filing_url: Optional[str] = None,
    filing_date: Optional[date] = None,
) -> dict:
    parsed = parse_indas_xbrl(
        payload,
        symbol=symbol,
        isin=isin,
        statement_type=statement_type,
        template_type=template_type,
        scale_to_cr=scale_to_cr,
        report_period=report_period,
        filing_url=filing_url,
        filing_date=filing_date,
    )
    res: Dict[str, Any] = {"status": "ok"}
    if parsed["quarantine"]:
        db.upsert_rows(con, "fin_quarantine", [parsed["quarantine"]], keys=["symbol", "fiscal_year_end", "statement_type"])
        res["status"] = "quarantined"
        res["quarantine"] = parsed["quarantine"]["reason"]
    if parsed["annual"]:
        db.upsert_rows(con, "fin_annual", [parsed["annual"]], keys=["symbol", "fiscal_year_end", "statement_type"])
        res["annual_rows"] = 1
    if parsed["quarterly"]:
        db.upsert_rows(con, "fin_quarterly", [parsed["quarterly"]], keys=["symbol", "quarter_end", "statement_type"])
        res["quarterly_rows"] = 1
    if parsed["shares_outstanding"] and (symbol or (parsed["annual"] or parsed["quarterly"])):
        sym = symbol or (parsed["annual"] or parsed["quarterly"])["symbol"]
        con.execute(
            "UPDATE ref_security SET shares_outstanding = COALESCE(shares_outstanding, ?) WHERE nse_symbol = ?",
            [parsed["shares_outstanding"], sym],
        )
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "NSE-XBRL",
        "url": filing_url or f"(XBRL {symbol or 'file'})",
        "saved_path": "n/a",
        "bytes": len(payload),
        "rows": 1 if parsed["annual"] or parsed["quarterly"] else 0,
    }], keys=["sha256"])
    return res


def sync_financials_for_symbol(
    con,
    symbol: str,
    *,
    max_annual: int = 6,
    max_quarterly: int = 4,
    max_filings: int | None = None,
    session=None,
    resume: bool = True,
) -> dict:
    """Fetches NSE quarterly & annual Ind-AS XBRL filings (consolidated preferred, checkpointed)."""
    s = session or bootstrap_nse_session()
    done_keys = db.get_progress_keys(con, "xbrl_filing", statuses=("ok",)) if resume else set()
    saved = 0
    skipped = 0
    quarantined = 0
    blocked = False
    requests_made = 0

    for period, default_limit in (("Annual", max_annual), ("Quarterly", max_quarterly)):
        limit = max_filings if max_filings is not None else default_limit
        url = f"https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol={symbol}&period={period}"
        r_meta = http.fetch(url, source="nse-api", session=s)
        requests_made += 1
        if r_meta.blocked():
            return {"status": "blocked", "symbol": symbol, "filings": saved, "requests": requests_made, "message": r_meta.error}
        if not r_meta.ok():
            continue
        try:
            data = json.loads(r_meta.bytes)
        except Exception:
            continue
        if not isinstance(data, list):
            continue

        def _parse_nse_dt_ord(raw_dt: Any) -> int:
            s = str(raw_dt or "").strip()[:11]
            if not s:
                return 0
            for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    from datetime import datetime as _dt
                    return _dt.strptime(s, fmt).date().toordinal()
                except ValueError:
                    continue
            return 0

        # Sort Annual before Quarterly/Half-Yearly, then most recent period-end DESC, then Consolidated before Standalone
        data.sort(
            key=lambda x: (
                0 if "annual" in str(x.get("period", "")).lower() else 1,
                -_parse_nse_dt_ord(x.get("toDate")),
                0 if (
                    "consolidat" in str(x.get("consolidated", "")).lower()
                    and "non" not in str(x.get("consolidated", "")).lower()
                ) else 1,
                -_parse_nse_dt_ord(x.get("filingDate")),
            )
        )
        def _parse_nse_dt(raw_dt: Any) -> Optional[date]:
            s = str(raw_dt or "").strip()[:11]
            if not s:
                return None
            from datetime import datetime as _dt
            for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return _dt.strptime(s, fmt).date()
                except ValueError:
                    continue
            return None

        # Deduplicate per (toDate, consolidated) preferring consolidated filings first across recent dates
        seen_periods: set[tuple[str, str]] = set()
        selected_items: List[Dict[str, Any]] = []
        for item in data:
            x_url = item.get("xbrl")
            if not x_url:
                continue
            stmt_tp = (
                "consolidated"
                if "consolidat" in str(item.get("consolidated", "")).lower()
                and "non" not in str(item.get("consolidated", "")).lower()
                else "standalone"
            )
            dk = (str(item.get("toDate") or ""), stmt_tp)
            if dk in seen_periods:
                continue
            seen_periods.add(dk)
            selected_items.append(item)
            if len(selected_items) >= limit:
                break

        from app.config import data_path, settings
        xbrl_raw_dir = data_path(settings()["data"]["raw_dir"]) / "nse-xbrl"

        for item in selected_items:
            x_url = item.get("xbrl")
            if not x_url:
                continue
            stmt_tp = (
                "consolidated"
                if "consolidat" in str(item.get("consolidated", "")).lower()
                and "non" not in str(item.get("consolidated", "")).lower()
                else "standalone"
            )
            to_dt_str = str(item.get("toDate") or "").strip()
            filing_dt = _parse_nse_dt(item.get("filingDate"))
            fkey = f"{symbol}::{period}::{to_dt_str}::{stmt_tp}"
            if resume and fkey in done_keys:
                skipped += 1
                continue

            # Cache-first check before network call
            payload_bytes: Optional[bytes] = None
            cached_matches = sorted(xbrl_raw_dir.glob(f"FIN_{symbol}_{period}_{to_dt_str}.xml*")) if xbrl_raw_dir.exists() else []
            if cached_matches and len(cached_matches) == 1:
                payload_bytes = cached_matches[0].read_bytes()
            else:
                r = http.fetch(
                    x_url,
                    source="nse-xbrl",
                    session=s,
                    save_name=f"FIN_{symbol}_{period}_{to_dt_str}.xml",
                )
                requests_made += 1
                if r.blocked():
                    db.mark_progress(con, "xbrl_filing", fkey, "fail", r.error or "http:403")
                    blocked = True
                    return {
                        "status": "blocked",
                        "symbol": symbol,
                        "filings": saved,
                        "skipped": skipped,
                        "quarantined": quarantined,
                        "requests": requests_made,
                        "message": r.error or "http:403",
                    }
                if r.ok():
                    payload_bytes = r.bytes

            if payload_bytes:
                tpl = "banks" if item.get("bank") == "Y" else None
                res_ing = ingest_financial_xbrl_bytes(
                    con,
                    payload_bytes,
                    symbol=symbol,
                    isin=item.get("isin"),
                    statement_type=stmt_tp,
                    template_type=tpl,
                    report_period=period,
                    filing_url=x_url,
                    filing_date=filing_dt,
                )
                saved += 1
                if res_ing.get("status") == "quarantined":
                    quarantined += 1
                db.mark_progress(con, "xbrl_filing", fkey, "ok", res_ing.get("status", "ok"))

    return {
        "status": "partial" if blocked else "ok",
        "symbol": symbol,
        "filings": saved,
        "skipped": skipped,
        "quarantined": quarantined,
        "requests": requests_made,
    }


def _pick_statement_series(
    con_rows: List[Dict[str, Any]],
    sa_rows: List[Dict[str, Any]],
) -> tuple[str, List[Dict[str, Any]]]:
    """Selects consolidated annuals unless absent or >14 months staler than standalone."""
    if con_rows and sa_rows:
        con_latest = con_rows[0].get("fiscal_year_end")
        sa_latest = sa_rows[0].get("fiscal_year_end")
        if con_latest and sa_latest and (sa_latest - con_latest).days > 420:
            return "standalone", sa_rows
        return "consolidated", con_rows
    if con_rows:
        return "consolidated", con_rows
    if sa_rows:
        return "standalone", sa_rows
    return "consolidated", []


def _select_annual_history(con, symbol: str) -> tuple[str, List[Dict[str, Any]]]:
    """Selects consolidated annual statements first (filtered to period_months >= 10), else standalone."""
    con_rows = _clean_rows_from_cursor(con.execute(
        """
        SELECT * FROM fin_annual
        WHERE symbol = ? AND statement_type = 'consolidated'
          AND (period_months IS NULL OR period_months >= 10)
        ORDER BY fiscal_year_end DESC LIMIT 6
        """,
        [symbol],
    ))
    sa_rows = _clean_rows_from_cursor(con.execute(
        """
        SELECT * FROM fin_annual
        WHERE symbol = ? AND statement_type = 'standalone'
          AND (period_months IS NULL OR period_months >= 10)
        ORDER BY fiscal_year_end DESC LIMIT 6
        """,
        [symbol],
    ))
    return _pick_statement_series(con_rows, sa_rows)


def _clean_rows_from_cursor(cur) -> List[Dict[str, Any]]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _compute_fundamentals_from_rows(
    annuals: List[Dict[str, Any]],
    q_rows: List[Dict[str, Any]],
    stmt_used: str,
    close_price: Optional[float],
    shares_outstanding: Optional[int],
    is_fin: bool,
) -> Dict[str, Any]:
    """Pure computation of all fundamental ratios, growth, margins, valuation, and FCF."""
    out: Dict[str, Any] = {"statement_type_used": stmt_used if (annuals or q_rows) else None}
    fy0 = annuals[0] if annuals else {}
    fy1 = annuals[1] if len(annuals) >= 2 else {}
    shares_eff = shares_outstanding or fy0.get("common_shares_out")
    mc = (close_price * float(shares_eff) / 1e7) if (close_price and shares_eff) else None
    out["market_cap"] = mc

    if not annuals:
        if q_rows:
            q0 = q_rows[0]
            for k in ("total_revenue_q", "net_income_q", "eps_q", "ebitda_q", "operating_and_other_expenses_q", "pbit_q", "pbt_q"):
                src_k = "operating_other_expenses_q" if k == "operating_and_other_expenses_q" else k
                out[k] = q0.get(src_k)
            if len(q_rows) == 4 and all(r.get("eps_q") is not None for r in q_rows):
                ttm_eps = sum(float(r["eps_q"]) for r in q_rows)
                out["ttm_pe_ratio"] = pe_ratio(close_price, ttm_eps)
        return out

    # Income Statement FY0 passthrough
    for k in (
        "total_revenue", "cost_of_revenue", "gross_profit", "ebitda",
        "depreciation_amortization", "pbit", "pbt", "taxes", "net_income",
        "dps", "power_fuel_cost", "raw_materials", "employee_cost",
        "sga_expense", "rd_expense", "operating_other_expenses",
        "interest_income", "net_interest_income", "loan_loss_provision",
    ):
        out[k] = fy0.get(k)
    out["dividend_per_share"] = fy0.get("dps")
    out["earnings_per_share"] = fy0.get("eps")
    out["interest_other_items"] = fy0.get("interest_expense")
    out["taxes_other_items"] = fy0.get("taxes")
    out["total_interest_expense"] = fy0.get("interest_expense")
    out["selling_administrative_expenses"] = fy0.get("sga_expense")
    out["research_development"] = fy0.get("rd_expense")
    out["operating_other_expenses"] = fy0.get("operating_other_expenses")

    # Payout ratio
    out["payout_ratio"] = safe_div(fy0.get("dps"), fy0.get("eps"), allow_negative_den=False)
    if out["payout_ratio"] is not None:
        out["payout_ratio"] *= 100.0

    # Balance Sheet & Cash Flow FY0
    out["book_value"] = fy0.get("total_equity")
    out["cash_short_term_investments"] = fy0.get("cash_and_st_inv")
    out["total_receivables"] = fy0.get("total_receivables")
    out["total_inventory"] = fy0.get("total_inventory")
    out["other_current_assets"] = fy0.get("other_current_assets")
    out["total_current_assets"] = fy0.get("total_current_assets")
    out["net_loans"] = fy0.get("net_loans")
    out["net_ppe"] = fy0.get("net_ppe")
    out["goodwill_intangibles"] = fy0.get("goodwill_intangibles")
    out["long_term_investments"] = fy0.get("long_term_investments")
    out["other_assets"] = fy0.get("other_assets")
    out["total_assets"] = fy0.get("total_assets")
    out["accounts_payable"] = fy0.get("accounts_payable")
    out["total_deposits"] = fy0.get("total_deposits")
    out["other_current_liabilities"] = fy0.get("other_current_liabilities")
    out["total_current_liabilities"] = fy0.get("total_current_liabilities")
    out["total_long_term_debt"] = fy0.get("total_long_term_debt")
    out["total_debt"] = fy0.get("total_debt")
    out["deferred_income_tax"] = fy0.get("deferred_income_tax")
    out["minority_interest"] = fy0.get("minority_interest")
    out["other_liabilities"] = fy0.get("other_liabilities")
    out["total_liabilities"] = fy0.get("total_liabilities")
    out["common_stock"] = fy0.get("common_stock")
    out["additional_paid_in_capital"] = fy0.get("apic")
    out["retained_earnings"] = fy0.get("retained_earnings")
    out["other_equity"] = fy0.get("other_equity")
    out["total_equity"] = fy0.get("total_equity")
    out["total_liabilities_shareholders_equity"] = (
        (fy0["total_liabilities"] + fy0["total_equity"])
        if fy0.get("total_liabilities") is not None and fy0.get("total_equity") is not None
        else fy0.get("total_assets")
    )
    out["total_common_shares_outstanding"] = shares_eff
    out["total_preferred_shares_outstanding"] = fy0.get("preferred_shares_out")
    out["policy_liabilities"] = fy0.get("policy_liabilities")
    out["changes_in_working_capital"] = fy0.get("changes_working_capital")
    out["cash_flow_operating_activities"] = fy0.get("cfo")
    out["capital_expenditures"] = fy0.get("capex")
    out["cash_investing_activities"] = fy0.get("cfi")
    out["total_cash_dividends_paid"] = fy0.get("dividends_paid")
    out["cash_financing_activities"] = fy0.get("cff")
    out["foreign_exchange_effects"] = fy0.get("fx_effects")
    out["net_change_in_cash"] = fy0.get("net_change_cash")

    fcf = (fy0["cfo"] - (fy0.get("capex") or 0.0)) if fy0.get("cfo") is not None else None

    # Profitability (Section 10.2)
    eq_avg = avg2(fy0.get("total_equity"), fy1.get("total_equity"))
    ast_avg = avg2(fy0.get("total_assets"), fy1.get("total_assets"))
    inv_cap_0 = (
        (fy0.get("total_equity") or 0.0) + (fy0.get("total_long_term_debt") or 0.0) + (fy0.get("other_liabilities") or 0.0)
        if fy0.get("total_equity") is not None
        else None
    )
    inv_cap_1 = (
        (fy1.get("total_equity") or 0.0) + (fy1.get("total_long_term_debt") or 0.0) + (fy1.get("other_liabilities") or 0.0)
        if fy1.get("total_equity") is not None
        else None
    )
    ic_avg = avg2(inv_cap_0, inv_cap_1)
    cap_emp = (
        fy0["total_assets"] - (fy0.get("total_current_liabilities") or 0.0)
        if fy0.get("total_assets") is not None
        else None
    )

    out["return_on_equity"] = return_on_equity(fy0.get("net_income"), eq_avg)
    out["return_on_assets"] = return_on_assets(fy0.get("net_income"), ast_avg)
    out["return_on_investment"] = return_on_investment(fy0.get("net_income"), ic_avg)
    out["roce"] = roce(fy0.get("pbit"), cap_emp)
    out["net_profit_margin"] = margin(fy0.get("net_income"), fy0.get("total_revenue"))
    out["ebitda_margin"] = margin(fy0.get("ebitda"), fy0.get("total_revenue"))
    out["operating_profit_margin"] = margin(fy0.get("pbit"), fy0.get("total_revenue"))
    out["cash_flow_margin"] = margin(fy0.get("cfo"), fy0.get("total_revenue"))
    out["cost_of_goods_sold"] = None if is_fin else fy0.get("cost_of_goods_sold")

    # 5Y Averages
    if len(annuals) >= 5:
        out["5y_avg_ebitda_margin"] = avg5([margin(a.get("ebitda"), a.get("total_revenue")) for a in annuals[:5]])
        out["5y_avg_net_profit_margin"] = avg5([margin(a.get("net_income"), a.get("total_revenue")) for a in annuals[:5]])
        out["5y_avg_cash_flow_margin"] = avg5([margin(a.get("cfo"), a.get("total_revenue")) for a in annuals[:5]])
        out["5y_avg_operating_profit_margin"] = avg5([margin(a.get("pbit"), a.get("total_revenue")) for a in annuals[:5]])
        out["5y_avg_return_on_investment"] = avg5([
            return_on_investment(
                annuals[i].get("net_income"),
                avg2(
                    (annuals[i].get("total_equity") or 0.0) + (annuals[i].get("total_long_term_debt") or 0.0) + (annuals[i].get("other_liabilities") or 0.0)
                    if annuals[i].get("total_equity") is not None else None,
                    (annuals[i + 1].get("total_equity") or 0.0) + (annuals[i + 1].get("total_long_term_debt") or 0.0) + (annuals[i + 1].get("other_liabilities") or 0.0)
                    if annuals[i + 1].get("total_equity") is not None else None,
                ),
            )
            for i in range(5)
        ]) if len(annuals) >= 6 else None
        if len(annuals) >= 6:
            out["5y_avg_return_on_equity"] = avg5([
                return_on_equity(annuals[i].get("net_income"), avg2(annuals[i].get("total_equity"), annuals[i + 1].get("total_equity")))
                for i in range(5)
            ])
            out["5y_avg_return_on_assets"] = avg5([
                return_on_assets(annuals[i].get("net_income"), avg2(annuals[i].get("total_assets"), annuals[i + 1].get("total_assets")))
                for i in range(5)
            ])

    # Historical Growth (Section 10.3)
    def _g1y(key: str) -> Optional[float]:
        v0, v1 = fy0.get(key), fy1.get(key)
        r = cagr(v1, v0, 1.0)
        return r * 100.0 if r is not None else None

    out["1y_historical_revenue_growth"] = _g1y("total_revenue")
    out["1y_historical_ebitda_growth"] = _g1y("ebitda")
    out["1y_historical_eps_growth"] = _g1y("eps")
    out["1y_hist_op_cash_flow_growth"] = _g1y("cfo")

    if len(annuals) >= 6:
        fy5 = annuals[5]
        for key, target in (
            ("total_revenue", "5y_historical_revenue_growth"),
            ("ebitda", "5y_historical_ebitda_growth"),
            ("eps", "5y_historical_eps_growth"),
            ("cfo", "5y_hist_op_cash_flow_growth"),
        ):
            r = cagr(fy5.get(key), fy0.get(key), 5.0)
            out[target] = r * 100.0 if r is not None else None

    if len(annuals) >= 4:
        r3 = cagr(annuals[3].get("dps"), fy0.get("dps"), 3.0)
        out["3y_historical_dividend_growth"] = r3 * 100.0 if r3 is not None else None

    # Valuation (Section 10.4)
    out["pe_ratio"] = pe_ratio(close_price, fy0.get("eps"))
    bvps = (fy0["total_equity"] * 1e7 / float(shares_eff)) if (fy0.get("total_equity") and shares_eff) else None
    sps = (fy0["total_revenue"] * 1e7 / float(shares_eff)) if (fy0.get("total_revenue") and shares_eff) else None
    out["pb_ratio"] = pb_ratio(close_price, bvps)
    out["ps_ratio"] = ps_ratio(close_price, sps)
    out["price_sales"] = out["ps_ratio"]
    out["dividend_yield"] = dividend_yield(fy0.get("dps"), close_price)

    ev = enterprise_value(mc, fy0.get("total_debt"), fy0.get("minority_interest"), fy0.get("cash_and_st_inv"))
    out["enterprise_value"] = ev
    out["ev_ebitda_ratio"] = ev_multiple(ev, fy0.get("ebitda"))
    out["ev_ebit_ratio"] = ev_multiple(ev, fy0.get("pbit"))
    out["ev_revenue_ratio"] = ev_multiple(ev, fy0.get("total_revenue"))
    out["ev_free_cash_flow"] = ev_multiple(ev, fcf)
    ic_tot = (
        (fy0.get("total_equity") or 0.0) + (fy0.get("total_debt") or 0.0) + (fy0.get("minority_interest") or 0.0)
        if fy0.get("total_equity") is not None
        else None
    )
    out["ev_invested_capital"] = ev_multiple(ev, ic_tot)
    out["price_cfo"] = price_to_cashflow(mc, fy0.get("cfo"))
    out["price_free_cash_flow"] = price_to_cashflow(mc, fcf)

    # Financial Ratios (Section 10.8) — bank/insurer exclusions strictly honored!
    out["current_ratio"] = current_ratio(fy0.get("total_current_assets"), fy0.get("total_current_liabilities"), is_fin)
    out["quick_ratio"] = quick_ratio(fy0.get("total_current_assets"), fy0.get("total_inventory"), fy0.get("total_current_liabilities"), is_fin)
    out["debt_to_equity"] = debt_to_equity(fy0.get("total_debt"), fy0.get("total_equity"), is_fin)
    out["long_term_debt_to_equity"] = debt_to_equity(fy0.get("total_long_term_debt"), fy0.get("total_equity"), is_fin)
    out["interest_coverage_ratio"] = interest_coverage(fy0.get("pbit"), fy0.get("interest_expense"))
    out["net_income_liabilities"] = safe_div(fy0.get("net_income"), fy0.get("total_liabilities"), allow_negative_den=False)
    out["earning_power"] = safe_div(fy0.get("pbit"), fy0.get("total_assets"), allow_negative_den=False)
    out["asset_turnover_ratio"] = safe_div(fy0.get("total_revenue"), ast_avg, allow_negative_den=False)

    if not is_fin:
        inv_avg = avg2(fy0.get("total_inventory"), fy1.get("total_inventory"))
        rec_avg = avg2(fy0.get("total_receivables"), fy1.get("total_receivables"))
        ap_avg = avg2(fy0.get("accounts_payable"), fy1.get("accounts_payable"))
        wc_0 = (fy0["total_current_assets"] - fy0["total_current_liabilities"]) if (fy0.get("total_current_assets") is not None and fy0.get("total_current_liabilities") is not None) else None
        wc_1 = (fy1["total_current_assets"] - fy1["total_current_liabilities"]) if (fy1.get("total_current_assets") is not None and fy1.get("total_current_liabilities") is not None) else None
        wc_avg = avg2(wc_0, wc_1)

        out["working_capital_turnover_ratio"] = safe_div(fy0.get("total_revenue"), wc_avg, allow_negative_den=False)
        out["inventory_turnover_ratio"] = safe_div(fy0.get("cost_of_goods_sold"), inv_avg, allow_negative_den=False)
        dio = safe_div(inv_avg, fy0.get("cost_of_goods_sold"), allow_negative_den=False)
        dso = safe_div(rec_avg, fy0.get("total_revenue"), allow_negative_den=False)
        dpo = safe_div(ap_avg, fy0.get("cost_of_goods_sold"), allow_negative_den=False)
        dio_d = dio * 365.0 if dio is not None else None
        dso_d = dso * 365.0 if dso is not None else None
        dpo_d = dpo * 365.0 if dpo is not None else None
        out["days_of_inventory_outstanding"] = dio_d
        out["days_of_sales_outstanding"] = dso_d
        out["days_payable_outstanding"] = dpo_d
        out["cash_conversion_cycle"] = cash_conversion_cycle(dio_d, dso_d, dpo_d, is_fin)

    if q_rows:
        q0 = q_rows[0]
        for k in ("total_revenue_q", "net_income_q", "eps_q", "ebitda_q", "operating_and_other_expenses_q", "pbit_q", "pbt_q"):
            src_k = "operating_other_expenses_q" if k == "operating_and_other_expenses_q" else k
            out[k] = q0.get(src_k)
        if len(q_rows) == 4 and all(r.get("eps_q") is not None for r in q_rows):
            ttm_eps = sum(float(r["eps_q"]) for r in q_rows)
            out["ttm_pe_ratio"] = pe_ratio(close_price, ttm_eps)

    return out


def compute_fundamental_metrics(
    con,
    symbol: str,
    close_price: Optional[float],
    shares_outstanding: Optional[int],
    is_financial_institution: Optional[bool] = None,
) -> Dict[str, Any]:
    """Computes complete fundamental ratios, growth, margins, valuation, and FCF for a stock."""
    stmt_used, annuals = _select_annual_history(con, symbol)
    sec_row = con.execute(
        "SELECT is_financial_institution, financial_template FROM ref_security WHERE nse_symbol = ? LIMIT 1",
        [symbol],
    ).fetchone()
    is_fin = bool(is_financial_institution if is_financial_institution is not None else (sec_row[0] if sec_row else False))
    if not annuals:
        return {"statement_type_used": None}
    q_rows = _clean_rows_from_cursor(con.execute(
        "SELECT * FROM fin_quarterly WHERE symbol = ? AND statement_type = ? ORDER BY quarter_end DESC LIMIT 4",
        [symbol, stmt_used],
    ))
    return _compute_fundamentals_from_rows(annuals, q_rows, stmt_used, close_price, shares_outstanding, is_fin)


def compute_all_fundamental_metrics_bulk(
    con,
    symbol_inputs: Dict[str, tuple[Optional[float], Optional[int], Optional[bool]]],
) -> Dict[str, Dict[str, Any]]:
    """Set-based bulk fundamentals computation across all symbols (replaces N+1 SQL queries)."""
    if not symbol_inputs:
        return {}

    ann_cur = con.execute(
        """
        SELECT * FROM fin_annual
        WHERE period_months IS NULL OR period_months >= 10
        QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, statement_type ORDER BY fiscal_year_end DESC) <= 6
        ORDER BY symbol, statement_type, fiscal_year_end DESC
        """
    )
    ann_map: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
    for row in _clean_rows_from_cursor(ann_cur):
        sym = row.get("symbol")
        st = row.get("statement_type")
        if sym and st:
            ann_map.setdefault((sym, st), []).append(row)

    q_cur = con.execute(
        """
        SELECT * FROM fin_quarterly
        QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, statement_type ORDER BY quarter_end DESC) <= 4
        ORDER BY symbol, statement_type, quarter_end DESC
        """
    )
    q_map: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
    for row in _clean_rows_from_cursor(q_cur):
        sym = row.get("symbol")
        st = row.get("statement_type")
        if sym and st:
            q_map.setdefault((sym, st), []).append(row)

    need_fin_flag = any(v[2] is None for v in symbol_inputs.values())
    fin_flag_map: Dict[str, bool] = {}
    if need_fin_flag:
        for sym, is_fi in con.execute(
            "SELECT nse_symbol, COALESCE(is_financial_institution, FALSE) FROM ref_security WHERE nse_symbol IS NOT NULL"
        ).fetchall():
            fin_flag_map[sym] = bool(is_fi)

    out: Dict[str, Dict[str, Any]] = {}
    for sym, (close_px, sh_out, is_fin_opt) in symbol_inputs.items():
        stmt_used, annuals = _pick_statement_series(ann_map.get((sym, "consolidated"), []), ann_map.get((sym, "standalone"), []))
        if not annuals:
            # Allow quarterly-only fallback when quarterly XBRL was ingested before annual
            if q_map.get((sym, "consolidated")):
                stmt_used = "consolidated"
            elif q_map.get((sym, "standalone")):
                stmt_used = "standalone"
            else:
                continue
        is_fin = bool(is_fin_opt if is_fin_opt is not None else fin_flag_map.get(sym, False))
        q_rows = q_map.get((sym, stmt_used), []) or q_map.get((sym, "standalone" if stmt_used == "consolidated" else "consolidated"), [])
        out[sym] = _compute_fundamentals_from_rows(annuals, q_rows, stmt_used, close_px, sh_out, is_fin)
    return out


def reingest_cached_xbrl_files(con) -> Dict[str, Any]:
    """Re-parses already cached `data/raw/nse-xbrl/FIN_*.xml*` files cleanly using the v2 parser."""
    from app.config import data_path, settings

    xbrl_dir = data_path(settings()["data"]["raw_dir"]) / "nse-xbrl"
    if not xbrl_dir.exists():
        return {"status": "skip", "files": 0, "annual": 0, "quarterly": 0}

    # Remove polluted < 10 month rows and stale legacy/cached rows for symbols being cleanly re-ingested
    con.execute("DELETE FROM fin_annual WHERE (period_months IS NOT NULL AND period_months < 10) OR filing_url LIKE 'cache://%' OR parser_version IS NULL")
    files = sorted(p for p in xbrl_dir.iterdir() if p.is_file() and p.name.startswith("FIN_"))
    n_ann = 0
    n_q = 0
    n_err = 0
    for p in files:
        # Format: FIN_{SYMBOL}_{Annual|Quarterly}_{toDate}.xml__sha.bin
        parts = p.name.split("_")
        sym_hint = parts[1].upper() if len(parts) > 1 else None
        period_hint = parts[2] if len(parts) > 2 else None
        try:
            res = ingest_financial_xbrl_bytes(
                con,
                p.read_bytes(),
                symbol=sym_hint,
                report_period=period_hint,
                filing_url=f"cache://{p.name}",
            )
            n_ann += int(res.get("annual_rows", 0))
            n_q += int(res.get("quarterly_rows", 0))
        except Exception as exc:
            n_err += 1
            log.warning("Failed reingesting cached %s: %s", p.name, exc)
    return {"status": "ok", "files": len(files), "annual": n_ann, "quarterly": n_q, "errors": n_err}

