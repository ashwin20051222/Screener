"""ingest/xbrl.py
Ind-AS XBRL XML parser supporting NSE/BSE financial filings across 4 sector templates
(industrials, utilities, banks, insurers) with unit scaling (INR -> Rs Cr), consolidated-first
selection, and Balance Sheet Integrity verification (Assets == Liabilities + Equity -> fin_quarantine).
"""
from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app import db
from app.metrics.formulas import bank_net_loans, validate_balance_sheet

log = logging.getLogger(__name__)

_INR_TO_CR = 1e7


def _num(v: Any) -> Optional[float]:
    if v is None or v == "" or v == "-":
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def _parse_dt(v: str | None) -> Optional[date]:
    if not v:
        return None
    s = str(v).strip().split()[0]
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _is_bank_tag_set(tags: Dict[str, str]) -> bool:
    return "InterestEarned" in tags or "InterestExpended" in tags or "Advances" in tags


def _is_insurer_tag_set(tags: Dict[str, str]) -> bool:
    return "PremiumsEarnedNet" in tags or "PolicyholdersFunds" in tags or "ClaimsIncurredNet" in tags


def parse_indas_xbrl(
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
) -> Dict[str, Any]:
    """Parses one NSE/BSE Ind-AS XBRL instance XML into normalized annual & quarterly records + quarantine status."""
    root = ET.fromstring(payload)
    by_ctx: Dict[str, Dict[str, float]] = {}
    meta: Dict[str, str] = {}
    unit_scale_detected = 1.0 / _INR_TO_CR  # NSE Ind-AS stores raw INR (divide by 1e7 -> Rs Cr)

    for el in root.iter():
        tag = el.tag.split("}")[-1]
        ctx = el.attrib.get("contextRef", "")
        txt = (el.text or "").strip()
        if not txt:
            continue
        val = _num(txt)
        if ctx and val is not None:
            by_ctx.setdefault(ctx, {})[tag] = val
        elif txt and tag not in meta:
            meta[tag] = txt

    sym = (symbol or meta.get("Symbol") or meta.get("ScripCode") or "").strip().upper()
    isin_val = (isin or meta.get("ISIN") or "").strip().upper() or None
    stmt_tp = statement_type or (
        "consolidated"
        if "consolidat" in (meta.get("NatureOfReportStandaloneConsolidated") or "").lower()
        else "standalone"
    )

    period_end = _parse_dt(meta.get("DateOfEndOfReportingPeriod") or meta.get("ReportingPeriodEndDate"))
    if period_end is None:
        # Check XML contexts for latest instant or endDate
        all_dts = []
        for el in root.iter():
            t = el.tag.split("}")[-1]
            if t in ("endDate", "instant") and el.text:
                d = _parse_dt(el.text.strip())
                if d:
                    all_dts.append(d)
        period_end = max(all_dts) if all_dts else date.today()

    # Detect annual vs quarterly/half-yearly filing so interim filings NEVER pollute fin_annual
    rp_hint = (report_period or "").strip().lower()
    rq_xml = (meta.get("ReportingQuarter") or "").strip().lower()
    period_start = _parse_dt(meta.get("DateOfStartOfReportingPeriod") or meta.get("ReportingPeriodStartDate"))
    span_days = (period_end - period_start).days if (period_start and period_end) else None

    is_explicit_quarterly = (
        rp_hint.startswith(("quarter", "half", "nine", "q1", "q2", "q3"))
        or any(tok in rq_xml for tok in ("quarter", "half", "nine"))
    )
    is_explicit_annual = (
        "annual" in rp_hint
        or rq_xml in ("yearly", "annual", "fourth quarter annual", "q4 audited", "full year")
        or ("annual" in rq_xml and "half" not in rq_xml and "quarter" not in rq_xml)
    )
    if is_explicit_quarterly:
        is_annual_filing = False
    elif span_days is not None and span_days < 300 and not is_explicit_annual:
        is_annual_filing = False
    else:
        is_annual_filing = bool(
            is_explicit_annual
            or ("FourD" in by_ctx)
            or ("OneI" in by_ctx and not is_explicit_quarterly)
        )

    # Prefer full-year 'FourD' for annual P&L if available, else 'OneD' for quarterly; 'OneI' for Balance Sheet instant
    pl_tags = (by_ctx.get("FourD") or by_ctx.get("MainD") or {}) if is_annual_filing else {}
    if is_annual_filing and not pl_tags:
        pl_tags = by_ctx.get("OneD") or {}
    q_tags = by_ctx.get("OneD") or {}
    bs_tags = by_ctx.get("OneI") or by_ctx.get("MainI") or {}
    cf_tags = (by_ctx.get("FourD") or by_ctx.get("MainD") or by_ctx.get("OneD") or {}) if is_annual_filing else (by_ctx.get("OneD") or {})

    if is_annual_filing and not pl_tags and by_ctx:
        # Fallback: flatten first numeric context for synthetic unit-test fixtures
        first_ctx = next(iter(by_ctx.values()))
        pl_tags = first_ctx
        if not q_tags:
            q_tags = first_ctx
    elif not is_annual_filing and not q_tags and by_ctx:
        q_tags = next(iter(by_ctx.values()))

    all_seen = {**pl_tags, **q_tags, **bs_tags, **cf_tags}
    tpl = template_type
    if not tpl:
        if _is_insurer_tag_set(all_seen):
            tpl = "insurers"
        elif _is_bank_tag_set(all_seen):
            tpl = "banks"
        elif "PowerAndFuel" in all_seen and "RevenueFromOperations" in all_seen:
            tpl = "industries"  # can also be overridden by sector_map ('utilities')
        else:
            tpl = "industrials"

    # Decide scaling: if explicit override false, keep 1.0; if raw INR detected (default for NSE Ind-AS), divide by 1e7
    if scale_to_cr is False:
        cr_mul = 1.0
    elif scale_to_cr is True:
        cr_mul = unit_scale_detected
    else:
        # Auto-detect: PaidUpValue > 1e6 or RevenueFromOperations > 1e6 indicates raw INR rather than Rs Cr
        sample_mag = max(
            abs(all_seen.get("RevenueFromOperations") or 0.0),
            abs(all_seen.get("Assets") or 0.0),
            abs(all_seen.get("PaidUpValueOfEquityShareCapital") or 0.0),
            0.0,
        )
        cr_mul = unit_scale_detected if sample_mag >= 1_000_000.0 else 1.0

    def _m(src: Dict[str, float], *keys: str) -> Optional[float]:
        for k in keys:
            if k in src:
                return round(src[k] * cr_mul, 4)
        return None

    def _raw(src: Dict[str, float], *keys: str) -> Optional[float]:
        for k in keys:
            if k in src:
                return src[k]
        return None

    def _msum(src: Dict[str, float], *keys: str) -> Optional[float]:
        vals = [src[k] for k in keys if k in src]
        return round(sum(vals) * cr_mul, 4) if vals else None

    # Common P&L extraction
    rev_ops = _m(pl_tags, "RevenueFromOperations", "InterestEarned", "PremiumsEarnedNet")
    other_inc = _m(pl_tags, "OtherIncome") or 0.0
    tot_rev = _m(pl_tags, "Income") or (round(rev_ops + other_inc, 4) if rev_ops is not None else None)

    raw_mat = _m(pl_tags, "CostOfMaterialsConsumed")
    purchases = _m(pl_tags, "PurchasesOfStockInTrade")
    inv_chg = _m(pl_tags, "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade")
    power_fuel = _m(pl_tags, "PowerAndFuel")
    emp_cost = _m(pl_tags, "EmployeeBenefitExpense")
    sga = _m(pl_tags, "SellingAndAdministrativeExpenses", "AdvertisingAndMarketingExpense")
    rd_exp = _m(pl_tags, "ResearchAndDevelopmentExpense")
    other_exp = _m(pl_tags, "OtherExpenses")
    fin_cost = _m(pl_tags, "FinanceCosts", "InterestExpended")
    da = _m(pl_tags, "DepreciationDepletionAndAmortisationExpense")
    pbt = _m(pl_tags, "ProfitBeforeTax", "ProfitBeforeExceptionalItemsAndTax")
    taxes = _m(pl_tags, "TaxExpense", "CurrentTax")
    net_inc = _m(pl_tags, "ProfitLossForPeriod", "ProfitLossForPeriodFromContinuingOperations")
    eps = _raw(pl_tags, "BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations", "BasicEarningsPerShare")
    dps = _raw(pl_tags, "DividendPerShare")

    # Sector templates (Section 10.11 & 10.10)
    int_inc = _m(pl_tags, "InterestEarned", "InterestIncome")
    loan_loss = _m(pl_tags, "ProvisionsAndContingencies", "LoanLossProvision")
    cogs: Optional[float] = None
    cost_of_rev: Optional[float] = None
    nii: Optional[float] = None

    if tpl == "banks":
        cogs = None  # Null for lenders per Section 10.2
        cost_of_rev = fin_cost
        if int_inc is not None and fin_cost is not None:
            nii = round(int_inc - fin_cost, 4)
        op_other = round((emp_cost or 0.0) + (other_exp or 0.0) + (loan_loss or 0.0), 4)
    elif tpl == "insurers":
        cogs = None
        claims = _m(pl_tags, "ClaimsIncurredNet") or 0.0
        comm = _m(pl_tags, "CommissionExpense") or 0.0
        cost_of_rev = _m(pl_tags, "BenefitsPaid", "CostOfRevenue") or round(claims + comm, 4)
        op_other = other_exp
    elif tpl == "utilities":
        cogs = round((raw_mat or 0.0) + (power_fuel or 0.0), 4) if (raw_mat is not None or power_fuel is not None) else None
        cost_of_rev = _m(pl_tags, "CostOfRevenue") or cogs
        op_other = round((emp_cost or 0.0) + (other_exp or 0.0), 4) if (emp_cost is not None or other_exp is not None) else other_exp
    else:
        # industrials
        parts = [v for v in (raw_mat, purchases, inv_chg) if v is not None]
        cogs = round(sum(parts), 4) if parts else _m(pl_tags, "CostOfGoodsSold")
        cost_of_rev = _m(pl_tags, "CostOfRevenue") or cogs
        op_parts = [v for v in (emp_cost, sga, rd_exp, other_exp) if v is not None]
        op_other = round(sum(op_parts), 4) if op_parts else other_exp

    gross_profit = round(tot_rev - cost_of_rev, 4) if (tot_rev is not None and cost_of_rev is not None) else _m(pl_tags, "GrossProfit")
    pbit = round(pbt + (fin_cost or 0.0), 4) if pbt is not None else _m(pl_tags, "PBIT", "OperatingProfit")
    ebitda = round(pbit + (da or 0.0), 4) if pbit is not None else (
        round(gross_profit - (op_other or 0.0), 4) if gross_profit is not None else None
    )

    # Balance sheet extraction (BS tags)
    if any(k in bs_tags for k in ("CashAndCashEquivalents", "BankBalanceOtherThanCashAndCashEquivalents", "CurrentInvestments")):
        bank_bal = (
            bs_tags.get("BankBalanceOtherThanCashAndCashEquivalents")
            if "BankBalanceOtherThanCashAndCashEquivalents" in bs_tags
            else bs_tags.get("BalancesWithBanksOtherThanCashAndCashEquivalents", 0.0)
        )
        cash_raw = (
            bs_tags.get("CashAndCashEquivalents", 0.0)
            + (bank_bal or 0.0)
            + bs_tags.get("CurrentInvestments", 0.0)
        )
        cash_st = round(cash_raw * cr_mul, 4)
    else:
        cash_st = _m(bs_tags, "CashAndCashEquivalents", "BalancesWithBanksOtherThanCashAndCashEquivalents", "CurrentInvestments")

    receivables = _m(bs_tags, "TradeReceivables")
    if receivables is None:
        receivables = _msum(bs_tags, "TradeReceivablesCurrent", "TradeReceivablesNoncurrent", "TradeReceivablesNonCurrent")

    inventory = _m(bs_tags, "Inventories")
    other_ca = _msum(bs_tags, "OtherCurrentAssets", "OtherCurrentFinancialAssets") or _m(bs_tags, "OtherCurrentAssets")
    tot_ca = _m(bs_tags, "CurrentAssets")
    gross_loans = _m(bs_tags, "GrossAdvances", "Loans", "Advances")
    npa_prov = _m(bs_tags, "NPAProvisions", "ProvisionForNonPerformingAssets") or 0.0
    net_loans = bank_net_loans(gross_loans, npa_prov) if gross_loans is not None else None
    net_ppe = _m(bs_tags, "PropertyPlantAndEquipment")
    goodwill = _msum(bs_tags, "Goodwill", "OtherIntangibleAssets", "IntangibleAssetsUnderDevelopment")
    lt_inv = _m(bs_tags, "NoncurrentInvestments", "NonCurrentInvestments", "Investments")
    other_assets = _msum(
        bs_tags,
        "OtherNoncurrentAssets",
        "OtherNonCurrentAssets",
        "OtherNoncurrentFinancialAssets",
        "DeferredTaxAssetsNet",
    )
    tot_assets = _m(bs_tags, "Assets")

    ap = _m(bs_tags, "TradePayables")
    if ap is None:
        ap = _msum(bs_tags, "TradePayablesCurrent", "TradePayablesNoncurrent", "TradePayablesNonCurrent")

    tot_deposits = _m(bs_tags, "Deposits")
    other_cl = _msum(bs_tags, "OtherCurrentLiabilities", "OtherCurrentFinancialLiabilities", "CurrentTaxLiabilities")
    tot_cl = _m(bs_tags, "CurrentLiabilities")
    lt_debt = _m(bs_tags, "BorrowingsNoncurrent", "BorrowingsNonCurrent", "LongTermBorrowings")
    st_debt = _m(bs_tags, "BorrowingsCurrent", "ShortTermBorrowings") or 0.0
    tot_debt = _m(bs_tags, "TotalDebt", "Borrowings") or (
        round((lt_debt or 0.0) + st_debt, 4)
        if (lt_debt is not None or "BorrowingsCurrent" in bs_tags or "ShortTermBorrowings" in bs_tags)
        else None
    )
    def_tax = _m(bs_tags, "DeferredTaxLiabilitiesNet")
    minority = _m(bs_tags, "NonControllingInterests", "MinorityInterest")
    other_liab = _msum(bs_tags, "OtherNoncurrentLiabilities", "OtherNonCurrentLiabilities", "OtherNoncurrentFinancialLiabilities")
    tot_liab = _m(bs_tags, "Liabilities")
    common_stk = _m(bs_tags, "EquityShareCapital", "PaidUpValueOfEquityShareCapital")
    apic = _m(bs_tags, "SecuritiesPremium", "AdditionalPaidInCapital")
    retained_eq = _m(bs_tags, "RetainedEarnings", "ReserveExcludingRevaluationReserves", "ReservesAndSurplus")
    other_eq = _m(bs_tags, "OtherEquity", "ReservesAndSurplus")
    tot_eq = _m(bs_tags, "Equity") or (
        round(common_stk + other_eq + (minority or 0.0), 4) if (common_stk is not None and other_eq is not None) else None
    )
    if tot_liab is None and _m(bs_tags, "EquityAndLiabilities") is not None and tot_eq is not None:
        tot_liab = round(_m(bs_tags, "EquityAndLiabilities") - tot_eq, 4)

    policy_liab = _m(bs_tags, "PolicyholdersFunds", "PolicyLiabilities")

    # Shares outstanding from PaidUpValue / FaceValue (check all_seen incl. OneI/FourD)
    paid_up_raw = _raw({**bs_tags, **all_seen}, "PaidUpValueOfEquityShareCapital", "EquityShareCapital")
    fv_raw = _raw({**bs_tags, **all_seen}, "FaceValueOfEquityShareCapital")
    shares_out: Optional[int] = None
    if paid_up_raw and fv_raw and fv_raw > 0:
        # Paid up in INR if cr_mul < 1 else Rs Cr * 1e7
        paid_inr = paid_up_raw if cr_mul < 1 else paid_up_raw * _INR_TO_CR
        shares_out = int(round(paid_inr / fv_raw))

    # Cash Flow extraction
    changes_wc = _m(cf_tags, "ChangesInWorkingCapital")
    if changes_wc is None:
        wc_keys = (
            "AdjustmentsForDecreaseIncreaseInInventories",
            "AdjustmentsForDecreaseIncreaseInTradeReceivablesCurrent",
            "AdjustmentsForDecreaseIncreaseInTradeReceivablesNoncurrent",
            "AdjustmentsForDecreaseIncreaseInOtherCurrentAssets",
            "AdjustmentsForDecreaseIncreaseInOtherNoncurrentAssets",
            "AdjustmentsForDecreaseIncreaseInOtherFinancialAssetsCurrent",
            "AdjustmentsForDecreaseIncreaseInOtherFinancialAssetsNoncurrent",
            "AdjustmentsForIncreaseDecreaseInTradePayablesCurrent",
            "AdjustmentsForIncreaseDecreaseInTradePayablesNoncurrent",
            "AdjustmentsForIncreaseDecreaseInOtherCurrentLiabilities",
            "AdjustmentsForIncreaseDecreaseInOtherNoncurrentLiabilities",
            "AdjustmentsForIncreaseDecreaseInOtherFinancialLiabilitiesCurrent",
            "AdjustmentsForOtherFinancialLiabilitiesCurrent",
            "AdjustmentsForOtherFinancialLiabilitiesNoncurrent",
        )
        changes_wc = _msum(cf_tags, *wc_keys)
    cfo = _m(cf_tags, "NetCashFlowsFromUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities")
    capex = _m(
        cf_tags,
        "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        "PurchaseOfPropertyPlantAndEquipment",
        "CapitalExpenditure",
    )
    if capex is not None and capex < 0:
        capex = abs(capex)
    cfi = _m(cf_tags, "NetCashFlowsFromUsedInInvestingActivities", "CashFlowsFromUsedInInvestingActivities")
    div_paid = _m(cf_tags, "DividendsPaidClassifiedAsFinancingActivities", "DividendsPaid")
    cff = _m(cf_tags, "NetCashFlowsFromUsedInFinancingActivities", "CashFlowsFromUsedInFinancingActivities")
    fx_effects = _m(cf_tags, "EffectOfExchangeRateChangesOnCashAndCashEquivalents")
    net_change_cash = _m(cf_tags, "IncreaseDecreaseInCashAndCashEquivalents", "NetIncreaseDecreaseInCashAndCashEquivalents")

    # Balance Sheet Integrity Verification (only applies when an annual record is being produced)
    quarantine_row = None
    if is_annual_filing and tot_assets is not None and tot_liab is not None and tot_eq is not None:
        if not validate_balance_sheet(tot_assets, tot_liab, tot_eq, tolerance=max(1.0, tot_assets * 0.005)):
            diff = round(tot_assets - (tot_liab + tot_eq), 4)
            quarantine_row = {
                "symbol": sym,
                "fiscal_year_end": period_end,
                "statement_type": stmt_tp,
                "reason": f"Assets ({tot_assets}) != Liabilities ({tot_liab}) + Equity ({tot_eq})",
                "total_assets": tot_assets,
                "total_liabilities": tot_liab,
                "total_equity": tot_eq,
                "diff": diff,
            }

    annual_row = None
    if is_annual_filing:
        annual_row = {
            "symbol": sym,
            "isin": isin_val,
            "fiscal_year_end": period_end,
            "period_months": 12,
            "statement_type": stmt_tp,
            "template_type": tpl,
            "total_revenue": tot_rev,
            "cost_of_revenue": cost_of_rev,
            "cost_of_goods_sold": cogs,
            "gross_profit": gross_profit,
            "ebitda": ebitda,
            "depreciation_amortization": da,
            "pbit": pbit,
            "interest_expense": fin_cost,
            "pbt": pbt,
            "taxes": taxes,
            "net_income": net_inc,
            "eps": eps,
            "dps": dps,
            "power_fuel_cost": power_fuel,
            "raw_materials": raw_mat,
            "employee_cost": emp_cost,
            "sga_expense": sga,
            "rd_expense": rd_exp,
            "operating_other_expenses": op_other,
            "interest_income": int_inc,
            "net_interest_income": nii,
            "loan_loss_provision": loan_loss,
            "cash_and_st_inv": cash_st,
            "total_receivables": receivables,
            "total_inventory": inventory,
            "other_current_assets": other_ca,
            "total_current_assets": tot_ca,
            "gross_loans": gross_loans,
            "npa_provisions": npa_prov if gross_loans is not None else None,
            "net_loans": net_loans,
            "net_ppe": net_ppe,
            "goodwill_intangibles": goodwill,
            "long_term_investments": lt_inv,
            "other_assets": other_assets,
            "total_assets": tot_assets,
            "accounts_payable": ap,
            "total_deposits": tot_deposits,
            "other_current_liabilities": other_cl,
            "total_current_liabilities": tot_cl,
            "total_long_term_debt": lt_debt,
            "total_debt": tot_debt,
            "deferred_income_tax": def_tax,
            "minority_interest": minority,
            "other_liabilities": other_liab,
            "total_liabilities": tot_liab,
            "common_stock": common_stk,
            "apic": apic,
            "retained_earnings": retained_eq,
            "other_equity": other_eq,
            "total_equity": tot_eq,
            "common_shares_out": shares_out,
            "policy_liabilities": policy_liab,
            "changes_working_capital": changes_wc,
            "cfo": cfo,
            "capex": capex,
            "cfi": cfi,
            "dividends_paid": div_paid,
            "cff": cff,
            "fx_effects": fx_effects,
            "net_change_cash": net_change_cash,
            "source": f"Ind-AS XBRL ({stmt_tp})",
            "raw_file_sha": hashlib.sha256(payload).hexdigest(),
            "filing_url": filing_url,
            "filing_date": filing_date,
            "parser_version": "2.0",
        }

    # Quarterly P&L record if OneD is present
    quarterly_row = None
    if q_tags:
        q_rev = _m(q_tags, "Income", "RevenueFromOperations")
        q_pbt = _m(q_tags, "ProfitBeforeTax")
        q_fin = _m(q_tags, "FinanceCosts") or 0.0
        q_da = _m(q_tags, "DepreciationDepletionAndAmortisationExpense") or 0.0
        q_pbit = round(q_pbt + q_fin, 4) if q_pbt is not None else None
        q_ebitda = round(q_pbit + q_da, 4) if q_pbit is not None else None
        q_op = round((_m(q_tags, "EmployeeBenefitExpense") or 0.0) + (_m(q_tags, "OtherExpenses") or 0.0), 4)
        q_ni = _m(q_tags, "ProfitLossForPeriod")
        q_eps = _raw(q_tags, "BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations", "BasicEarningsPerShare")
        quarterly_row = {
            "symbol": sym,
            "isin": isin_val,
            "quarter_end": period_end,
            "statement_type": stmt_tp,
            "total_revenue_q": q_rev,
            "ebitda_q": q_ebitda,
            "operating_other_expenses_q": q_op,
            "pbit_q": q_pbit,
            "pbt_q": q_pbt,
            "net_income_q": q_ni,
            "eps_q": q_eps,
            "source": f"Ind-AS XBRL ({stmt_tp})",
            "filing_url": filing_url,
            "filing_date": filing_date,
            "parser_version": "2.0",
        }

    return {
        "annual": None if quarantine_row else annual_row,
        "quarterly": quarterly_row,
        "quarantine": quarantine_row,
        "shares_outstanding": shares_out,
    }
