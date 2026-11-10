"""ingest/financials.py
Financial statements ingestion (NSE API + XBRL + inbox) & Section 10.2/10.3/10.4/10.8/10.10/10.11
fundamental ratios aggregator. Consolidated statements first with standalone fallback.
"""
from __future__ import annotations

import hashlib
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
) -> dict:
    parsed = parse_indas_xbrl(
        payload,
        symbol=symbol,
        isin=isin,
        statement_type=statement_type,
        template_type=template_type,
        scale_to_cr=scale_to_cr,
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
        "url": f"(XBRL {symbol or 'file'})",
        "saved_path": "n/a",
        "bytes": len(payload),
        "rows": 1 if parsed["annual"] or parsed["quarterly"] else 0,
    }], keys=["sha256"])
    return res


def sync_financials_for_symbol(con, symbol: str, *, max_filings: int = 4) -> dict:
    """Fetches NSE quarterly & annual Ind-AS XBRL filings (consolidated preferred over standalone)."""
    s = bootstrap_nse_session()
    saved = 0
    for period in ("Annual", "Quarterly"):
        url = f"https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol={symbol}&period={period}"
        data = fetch_json(url, source="nse-api", session=s)
        if not isinstance(data, list):
            continue
        # Sort consolidated first, then most recent
        data.sort(key=lambda x: (0 if "consolidat" in str(x.get("consolidated", "")).lower() and "non" not in str(x.get("consolidated", "")).lower() else 1))
        for item in data[:max_filings]:
            x_url = item.get("xbrl")
            if not x_url:
                continue
            r = http.fetch(x_url, source="nse-xbrl", session=s, save_name=f"FIN_{symbol}_{period}_{item.get('toDate','')}.xml")
            if r.ok():
                stmt_tp = (
                    "consolidated"
                    if "consolidat" in str(item.get("consolidated", "")).lower() and "non" not in str(item.get("consolidated", "")).lower()
                    else "standalone"
                )
                tpl = "banks" if item.get("bank") == "Y" else None
                ingest_financial_xbrl_bytes(con, r.bytes, symbol=symbol, isin=item.get("isin"), statement_type=stmt_tp, template_type=tpl)
                saved += 1
    return {"status": "ok", "symbol": symbol, "filings": saved}


def _select_annual_history(con, symbol: str) -> tuple[str, List[Dict[str, Any]]]:
    """Selects consolidated annual statements first; falls back cleanly to standalone if consolidated absent."""
    stmt = "consolidated"
    rows = con.execute(
        "SELECT * FROM fin_annual WHERE symbol = ? AND statement_type = 'consolidated' ORDER BY fiscal_year_end DESC LIMIT 6",
        [symbol],
    ).fetchdf()
    if len(rows) == 0:
        stmt = "standalone"
        rows = con.execute(
            "SELECT * FROM fin_annual WHERE symbol = ? AND statement_type = 'standalone' ORDER BY fiscal_year_end DESC LIMIT 6",
            [symbol],
        ).fetchdf()
    return stmt, rows.to_dict("records")


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

    out: Dict[str, Any] = {"statement_type_used": stmt_used if annuals else None}
    if not annuals:
        return out

    fy0 = annuals[0]
    fy1 = annuals[1] if len(annuals) >= 2 else {}
    shares_eff = shares_outstanding or fy0.get("common_shares_out")
    mc = (close_price * float(shares_eff) / 1e7) if (close_price and shares_eff) else None
    out["market_cap"] = mc

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
    out["total_assets"] = fy0.get("total_assets")
    out["accounts_payable"] = fy0.get("accounts_payable")
    out["total_deposits"] = fy0.get("total_deposits")
    out["total_current_liabilities"] = fy0.get("total_current_liabilities")
    out["total_long_term_debt"] = fy0.get("total_long_term_debt")
    out["total_debt"] = fy0.get("total_debt")
    out["deferred_income_tax"] = fy0.get("deferred_income_tax")
    out["minority_interest"] = fy0.get("minority_interest")
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
    out["policy_liabilities"] = fy0.get("policy_liabilities")
    out["cash_flow_operating_activities"] = fy0.get("cfo")
    out["capital_expenditures"] = fy0.get("capex")
    out["cash_investing_activities"] = fy0.get("cfi")
    out["total_cash_dividends_paid"] = fy0.get("dividends_paid")
    out["cash_financing_activities"] = fy0.get("cff")

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

    # Quarterly & TTM PE
    q_rows = con.execute(
        "SELECT * FROM fin_quarterly WHERE symbol = ? AND statement_type = ? ORDER BY quarter_end DESC LIMIT 4",
        [symbol, stmt_used],
    ).fetchdf().to_dict("records")
    if q_rows:
        q0 = q_rows[0]
        for k in ("total_revenue_q", "net_income_q", "eps_q", "ebitda_q", "operating_and_other_expenses_q", "pbit_q", "pbt_q"):
            src_k = "operating_other_expenses_q" if k == "operating_and_other_expenses_q" else k
            out[k] = q0.get(src_k)
        if len(q_rows) == 4 and all(r.get("eps_q") is not None for r in q_rows):
            ttm_eps = sum(float(r["eps_q"]) for r in q_rows)
            out["ttm_pe_ratio"] = pe_ratio(close_price, ttm_eps)

    return out
