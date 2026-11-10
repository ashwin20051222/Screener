"""ingest/ownership.py
Shareholding patterns (XBRL + JSON), Promoter Pledges, Bulk/Block deals, and SEBI PIT Insider Trades
(Phase 4.4, Section 10.5).
Uses verified official NSE schemas observed 2026-11-10:
- SHP XBRL fractions (0.5044 -> 50.44%) with exact SEBI/NSE context names
- Bulk/Block deals from /api/snapshot-capital-market-largedeal (BULK_DEALS_DATA / BLOCK_DEALS_DATA)
- Insider trades from /api/corporates-pit + CSV manual inbox fallback.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app import db
from ingest import http
from ingest.http import bootstrap_nse_session, fetch_json

log = logging.getLogger(__name__)


def _parse_date_any(v: str | None) -> Optional[date]:
    if not v:
        return None
    s = str(v).strip().split()[0]
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _num(v: Any) -> Optional[float]:
    if v is None or v == "" or v == "-":
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def _int_val(v: Any) -> Optional[int]:
    f = _num(v)
    return int(round(f)) if f is not None else None


# ------------------------------------------------------------------ Shareholding XBRL Parser

def parse_shp_xbrl(payload: bytes, *, symbol: Optional[str] = None, isin: Optional[str] = None) -> Dict[str, Any]:
    """Parses official NSE/BSE Shareholding Pattern XBRL XML (SHP_*_WEB.xml).
    Values in NSE SHP XBRL `ShareholdingAsAPercentageOfTotalNumberOfShares` are fractions (e.g. 0.5044 = 50.44%),
    so values <= 1.0 are multiplied by 100.0 cleanly (or normalized if > 1.0).
    """
    root = ET.fromstring(payload)
    by_ctx: Dict[str, Dict[str, str]] = {}
    meta: Dict[str, str] = {}

    for el in root.iter():
        tag = el.tag.split("}")[-1]
        ctx = el.attrib.get("contextRef", "")
        txt = (el.text or "").strip()
        if not txt:
            continue
        if ctx:
            by_ctx.setdefault(ctx, {})[tag] = txt
        else:
            meta[tag] = txt

    # Symbol / ISIN / Quarter-end resolution
    sym = symbol or by_ctx.get("MainI", {}).get("Symbol") or by_ctx.get("OneI", {}).get("Symbol")
    isin_val = isin or by_ctx.get("MainI", {}).get("ISIN") or by_ctx.get("OneI", {}).get("ISIN")

    q_dt = None
    for ctx_key in ("MainI", "OneI", "ShareholdingPattern_ContextI"):
        d_txt = by_ctx.get(ctx_key, {}).get("DateOfReport") or by_ctx.get(ctx_key, {}).get("PeriodEndDate")
        if d_txt:
            q_dt = _parse_date_any(d_txt)
            if q_dt:
                break
    if q_dt is None:
        # Look for XML <endDate> or <instant> inside <context>
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            if tag in ("instant", "endDate") and el.text:
                q_dt = _parse_date_any(el.text.strip())
                if q_dt:
                    break
    if q_dt is None:
        q_dt = date.today()

    def _pct_from_ctx(*ctx_names: str) -> Optional[float]:
        for cn in ctx_names:
            d = by_ctx.get(cn)
            if not d:
                continue
            v = _num(
                d.get("ShareholdingAsAPercentageOfTotalNumberOfShares")
                or d.get("ShareholdingAsAPercentageAssumingFullConversionOfConvertibleSecuritiesWarrantsAndESOP")
            )
            if v is not None:
                return round(v * 100.0 if v <= 1.0 else v, 4)
        return None

    def _shares_from_ctx(*ctx_names: str) -> Optional[int]:
        for cn in ctx_names:
            d = by_ctx.get(cn)
            if d and d.get("NumberOfShares"):
                return _int_val(d["NumberOfShares"])
        return None

    promoter_pct = _pct_from_ctx("ShareholdingOfPromoterAndPromoterGroup_ContextI")
    mf_pct = _pct_from_ctx("MutualFundsOrUTI_ContextI")
    dii_pct = _pct_from_ctx("InstitutionsDomestic_ContextI")
    fii_pct = _pct_from_ctx("InstitutionsForeign_ContextI")
    if fii_pct is None:
        fpi1 = _pct_from_ctx("InstitutionsForeignPortfolioInvestorCategoryOne_ContextI")
        fpi2 = _pct_from_ctx("InstitutionsForeignPortfolioInvestorCategoryTwo_ContextI")
        if fpi1 is not None or fpi2 is not None:
            fii_pct = round((fpi1 or 0.0) + (fpi2 or 0.0), 4)
    ins_pct = _pct_from_ctx("InsuranceCompanies_ContextI")

    retail_u2l = _pct_from_ctx("ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh_ContextI")
    retail_o2l = _pct_from_ctx("ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh_ContextI")
    if retail_u2l is not None or retail_o2l is not None:
        retail_pct = round((retail_u2l or 0.0) + (retail_o2l or 0.0), 4)
    else:
        retail_pct = _pct_from_ctx("NonInstitutions_ContextI")

    # Promoter Pledged / Encumbered %
    prom_shares = _shares_from_ctx("ShareholdingOfPromoterAndPromoterGroup_ContextI")
    tot_shares = _shares_from_ctx("ShareholdingPattern_ContextI", "PublicShareholding_ContextI")
    if tot_shares is None:
        s_pub = _shares_from_ctx("PublicShareholding_ContextI") or 0
        s_np = _shares_from_ctx("SharesHeldByNonPromotersNonPublic_ContextI") or 0
        tot_sum = (prom_shares or 0) + s_pub + s_np
        tot_shares = tot_sum if tot_sum > 0 else None
    pledged_shares = None
    prom_ctx = by_ctx.get("ShareholdingOfPromoterAndPromoterGroup_ContextI", {})
    for k in ("NumberOfSharesPledgedOrOtherwiseEncumbered", "NumberOfSharesEncumbered"):
        if k in prom_ctx:
            pledged_shares = _int_val(prom_ctx[k])
            break

    if pledged_shares is not None and prom_shares and prom_shares > 0:
        prom_pledged_pct = round((pledged_shares / prom_shares) * 100.0, 4)
    elif prom_ctx.get("PercentageOfSharesPledgedOrOtherwiseEncumberedAsAPercentageOfTotalShareholdingOfPromoterAndPromoterGroup"):
        raw_p = _num(prom_ctx["PercentageOfSharesPledgedOrOtherwiseEncumberedAsAPercentageOfTotalShareholdingOfPromoterAndPromoterGroup"])
        prom_pledged_pct = round(raw_p * 100.0 if raw_p is not None and raw_p <= 1.0 else (raw_p or 0.0), 4)
    else:
        prom_pledged_pct = 0.0

    if pledged_shares is not None and tot_shares and tot_shares > 0:
        prom_pledged_total_pct = round((pledged_shares / tot_shares) * 100.0, 4)
    elif promoter_pct is not None:
        prom_pledged_total_pct = round((prom_pledged_pct / 100.0) * promoter_pct, 4)
    else:
        prom_pledged_total_pct = 0.0

    # Shareholders count
    no_sh = None
    for cn in ("ShareholdingPattern_ContextI", "MainI", "PublicShareholding_ContextI"):
        d = by_ctx.get(cn, {})
        if "NumberOfShareholders" in d:
            no_sh = _int_val(d["NumberOfShareholders"])
            if no_sh is not None:
                break
    if no_sh is None:
        # Sum promoter + public shareholders if pattern total omitted
        s1 = _int_val(by_ctx.get("ShareholdingOfPromoterAndPromoterGroup_ContextI", {}).get("NumberOfShareholders")) or 0
        s2 = _int_val(by_ctx.get("PublicShareholding_ContextI", {}).get("NumberOfShareholders")) or 0
        no_sh = (s1 + s2) if (s1 + s2) > 0 else None

    return {
        "symbol": sym or "",
        "isin": isin_val,
        "quarter_end": q_dt,
        "promoter_pct": promoter_pct,
        "promoter_pledged_pct": prom_pledged_pct,
        "promoter_pledged_total_pct": prom_pledged_total_pct,
        "mf_pct": mf_pct,
        "dii_pct": dii_pct,
        "fii_pct": fii_pct,
        "retail_pct": retail_pct,
        "insurance_pct": ins_pct,
        "no_of_shareholders": no_sh,
        "shares_outstanding": tot_shares,
        "source": "NSE SHP XBRL",
    }


def sync_shareholding_xbrl_from_bytes(con, payload: bytes, *, symbol: Optional[str] = None, isin: Optional[str] = None) -> dict:
    row = parse_shp_xbrl(payload, symbol=symbol, isin=isin)
    if not row["symbol"]:
        return {"status": "fail", "message": "symbol missing from SHP XBRL"}
    sh_out = row.pop("shares_outstanding", None)
    n = db.upsert_rows(con, "ownership_quarterly", [row], keys=["symbol", "quarter_end"])
    if sh_out and sh_out > 0:
        con.execute(
            """
            UPDATE ref_security
            SET shares_outstanding = COALESCE(?, shares_outstanding),
                shares_source = COALESCE(shares_source, 'NSE SHP XBRL'),
                shares_as_of = COALESCE(shares_as_of, ?),
                updated_at = current_timestamp
            WHERE nse_symbol = ?
            """,
            [sh_out, row["quarter_end"], row["symbol"]],
        )
    db.upsert_rows(con, "raw_files", [{
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "NSE-SHP",
        "url": f"(SHP XBRL {row['symbol']} {row['quarter_end']})",
        "saved_path": "n/a",
        "bytes": len(payload),
        "rows": n,
    }], keys=["sha256"])
    return {
        "status": "ok",
        "rows": n,
        "symbol": row["symbol"],
        "quarter_end": str(row["quarter_end"]),
        "shares_outstanding": sh_out,
    }


def ordered_universe_symbols(con, universe: str = "nifty100") -> List[str]:
    """Returns NSE symbols prioritized as: NIFTY100 -> rest of NIFTY500 -> remaining listed."""
    def _latest_idx_syms(idx_name: str) -> List[str]:
        return [
            r[0] for r in con.execute(
                """
                SELECT r.symbol
                FROM ref_index_constituent r
                JOIN (SELECT MAX(as_of) AS max_dt FROM ref_index_constituent WHERE index_name = ?) m
                  ON r.as_of = m.max_dt
                LEFT JOIN ref_security s ON s.nse_symbol = r.symbol
                LEFT JOIN (
                    SELECT symbol, close
                    FROM px_daily
                    WHERE source = 'NSE'
                    QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) = 1
                ) px ON px.symbol = r.symbol
                WHERE r.index_name = ? AND r.symbol IS NOT NULL
                ORDER BY (COALESCE(px.close, 0) * COALESCE(s.shares_outstanding, 0)) DESC, r.symbol ASC
                """,
                [idx_name, idx_name],
            ).fetchall()
        ]

    n100 = _latest_idx_syms("NIFTY100")
    n500 = _latest_idx_syms("NIFTY500")
    all_syms = [
        r[0] for r in con.execute(
            "SELECT DISTINCT nse_symbol FROM ref_security WHERE nse_symbol IS NOT NULL AND COALESCE(listing_status, 'listed') <> 'delisted' ORDER BY nse_symbol"
        ).fetchall()
    ]

    seen: set[str] = set()
    ordered: List[str] = []

    def _add(items: List[str]):
        for s in items:
            if s and s not in seen:
                seen.add(s)
                ordered.append(s)

    uni = (universe or "nifty100").lower().strip()
    if uni == "nifty100":
        _add(n100)
        return ordered if ordered else all_syms[:100]
    if uni == "nifty500":
        _add(n100)
        _add(n500)
        return ordered if ordered else all_syms[:500]
    _add(n100)
    _add(n500)
    _add(all_syms)
    return ordered


def sync_shareholding_for_symbol(
    con,
    symbol: str,
    *,
    max_quarters: int = 3,
    session=None,
) -> dict:
    """Fetches NSE shareholding master list & up to `max_quarters` official SHP XBRL files."""
    s = session or bootstrap_nse_session()
    url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol}"
    r_meta = http.fetch(url, source="nse-api", session=s)
    if r_meta.blocked():
        return {"status": "blocked", "symbol": symbol, "message": r_meta.error or "http:403"}
    if not r_meta.ok():
        return {"status": "skip", "symbol": symbol, "message": f"no shareholding master data ({r_meta.error})"}
    try:
        data = json.loads(r_meta.bytes)
    except Exception:
        return {"status": "skip", "symbol": symbol, "message": "non-JSON shareholding master"}
    if not isinstance(data, list) or not data:
        return {"status": "skip", "symbol": symbol, "message": "no shareholding master data"}
    saved = 0
    shares_updated = False
    for entry in data[:max_quarters]:
        x_url = entry.get("xbrl")
        if not x_url:
            continue
        r = http.fetch(x_url, source="nse-shp", session=s, save_name=f"SHP_{symbol}_{entry.get('date','')}.xml")
        if r.blocked():
            return {"status": "blocked", "symbol": symbol, "quarters": saved, "message": r.error or "http:403"}
        if r.ok():
            x_res = sync_shareholding_xbrl_from_bytes(con, r.bytes, symbol=symbol, isin=entry.get("isin"))
            saved += 1
            if x_res.get("shares_outstanding"):
                shares_updated = True
    return {"status": "ok", "symbol": symbol, "quarters": saved, "shares_updated": shares_updated}


def sync_shp_batch(
    con,
    universe: str = "nifty100",
    *,
    resume: bool = True,
    max_quarters: int = 1,
    max_symbols: int | None = None,
) -> dict:
    """Resumable sequential SHP sync ordered NIFTY100 -> NIFTY500 -> rest; stops on 403/429."""
    t0 = datetime.now()
    symbols = ordered_universe_symbols(con, universe)
    if max_symbols is not None:
        symbols = symbols[:max_symbols]

    done = db.get_progress_keys(con, "sync_shp", statuses=("ok",)) if resume else set()
    s = bootstrap_nse_session()
    processed = 0
    skipped = 0
    failed = 0
    blocked = False

    for sym in symbols:
        if sym in done:
            skipped += 1
            continue
        res = sync_shareholding_for_symbol(con, sym, max_quarters=max_quarters, session=s)
        if res.get("status") == "blocked":
            db.mark_progress(con, "sync_shp", sym, "fail", res.get("message", "403/429"))
            log.error(
                "NSE returned 403/429 at %s. Respecting publisher limits — stopping immediately.\n"
                "Manual fallback: download SHP XBRL files in your browser as data/inbox/SHP_<symbol>.xml "
                "or daily PR archive as data/inbox/PRddmmyy.zip and run `make synkinbox`.",
                sym,
            )
            blocked = True
            failed += 1
            break
        if res.get("status") == "ok" and res.get("quarters", 0) > 0:
            db.mark_progress(con, "sync_shp", sym, "ok", f"q={res['quarters']}")
            processed += 1
        else:
            db.mark_progress(con, "sync_shp", sym, "skip", res.get("message", "no data"))
            failed += 1

    try:
        from app.query.snapshot import build_screener_snapshot
        build_screener_snapshot(con)
    except Exception as exc:
        log.warning("Post-SHP snapshot rebuild failed: %s", exc)

    db.upsert_rows(con, "ingest_status", [{
        "id": f"sync_shp::{universe}::{date.today()}",
        "job": "sync_shp",
        "run_date": date.today(),
        "status": "partial" if blocked else "ok",
        "rows": processed,
        "message": f"universe={universe} ok={processed} resumed_skip={skipped} miss_or_fail={failed} blocked={blocked}",
        "started_at": t0,
        "finished_at": datetime.now(),
    }], keys=["id"])
    return {
        "status": "partial" if blocked else "ok",
        "universe": universe,
        "processed": processed,
        "skipped_resume": skipped,
        "failed_or_missing": failed,
        "blocked": blocked,
    }


# ------------------------------------------------------------------ Bulk & Block Deals Parser

def parse_largedeals_json(blob: Dict[str, Any], *, exchange: str = "NSE") -> List[Dict[str, Any]]:
    """Parses NSE /api/snapshot-capital-market-largedeal JSON payload cleanly."""
    out: List[Dict[str, Any]] = []
    fallback_dt = _parse_date_any(blob.get("as_on_date")) or date.today()
    for key, deal_type in (("BULK_DEALS_DATA", "BULK"), ("BLOCK_DEALS_DATA", "BLOCK")):
        for item in blob.get(key) or []:
            sym = (item.get("symbol") or "").strip().upper()
            client = (item.get("clientName") or "").strip()
            bs = (item.get("buySell") or "").strip().upper()
            qty = _int_val(item.get("qty"))
            if not sym or not client or bs not in ("BUY", "SELL") or qty is None:
                continue
            dt = _parse_date_any(item.get("date")) or fallback_dt
            out.append({
                "deal_date": dt,
                "exchange": exchange,
                "deal_type": deal_type,
                "symbol": sym,
                "isin": item.get("isin") or None,
                "client_name": client,
                "buy_sell": bs,
                "quantity": qty,
                "price": _num(item.get("watp")),
                "remarks": (item.get("remarks") or "").strip() or None,
                "source": f"{exchange} largedeal API",
            })
    return out


def parse_deals_csv_bytes(payload: bytes, *, deal_type: str = "BULK", exchange: str = "NSE") -> List[Dict[str, Any]]:
    """Parses CSV bulk/block deal dumps dropped in data/inbox/."""
    rows = list(csv.reader(io.StringIO(payload.decode("utf-8-sig", "replace"))))
    if len(rows) < 2:
        return []
    hdr = [h.strip().lower() for h in rows[0]]

    def _find(*names):
        for nm in names:
            for j, h in enumerate(hdr):
                if nm in h:
                    return j
        return None

    i_dt = _find("date")
    i_sym = _find("symbol", "security")
    i_cli = _find("client")
    i_bs = _find("buy / sell", "buy/sell", "buysell", "transaction")
    i_qty = _find("quantity", "qty")
    i_px = _find("price", "watp")

    if i_sym is None or i_cli is None or i_qty is None:
        return []

    out = []
    for r in rows[1:]:
        if len(r) <= max(i_sym, i_cli, i_qty):
            continue
        sym = r[i_sym].strip().upper()
        cli = r[i_cli].strip()
        qty = _int_val(r[i_qty])
        if not sym or not cli or qty is None:
            continue
        bs = r[i_bs].strip().upper() if i_bs is not None and i_bs < len(r) else "BUY"
        if bs.startswith("B"):
            bs = "BUY"
        elif bs.startswith("S"):
            bs = "SELL"
        dt = _parse_date_any(r[i_dt]) if i_dt is not None and i_dt < len(r) else date.today()
        px = _num(r[i_px]) if i_px is not None and i_px < len(r) else None
        out.append({
            "deal_date": dt or date.today(),
            "exchange": exchange,
            "deal_type": deal_type,
            "symbol": sym,
            "client_name": cli,
            "buy_sell": bs,
            "quantity": qty,
            "price": px,
            "source": f"{exchange} CSV",
        })
    return out


def sync_bulk_block_deals(con, *, session=None) -> dict:
    s = session or bootstrap_nse_session()
    url = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"
    r = http.fetch(url, source="nse-api", session=s)
    if r.blocked():
        return {"status": "blocked", "message": r.error or "http:403"}
    if not r.ok():
        return {"status": "fail", "message": f"largedeal API unavailable ({r.error})"}
    try:
        data = json.loads(r.bytes)
    except Exception:
        return {"status": "fail", "message": "largedeal non-JSON payload"}
    if not isinstance(data, dict):
        return {"status": "fail", "message": "largedeal API unexpected structure"}
    rows = parse_largedeals_json(data, exchange="NSE")
    n = db.upsert_rows(
        con, "bulk_block_deals", rows,
        keys=["deal_date", "exchange", "deal_type", "symbol", "client_name", "buy_sell", "quantity"],
    )
    return {"status": "ok", "rows": n}


# ------------------------------------------------------------------ SEBI PIT Insider Trades

def parse_pit_json_or_csv(payload: bytes) -> List[Dict[str, Any]]:
    """Parses NSE SEBI PIT insider trading disclosures (API JSON or CF-Insider-Trading-*.csv)."""
    text = payload.decode("utf-8-sig", "replace").strip()
    out: List[Dict[str, Any]] = []

    if text.startswith("{") or text.startswith("["):
        blob = json.loads(text)
        items = blob.get("data", []) if isinstance(blob, dict) else blob
        for it in items:
            sym = (it.get("symbol") or "").strip().upper()
            acq = (it.get("acqName") or "").strip()
            shares = _int_val(it.get("secAcq"))
            dt = _parse_date_any(it.get("date") or it.get("intimDt") or it.get("acqfromDt"))
            if not sym or not acq or shares is None or not dt:
                continue
            mode = (it.get("tdpTransactionType") or "Buy").strip().upper()
            tx = "SELL" if "SELL" in mode or "DISPOS" in mode or "SALE" in mode else "BUY"
            out.append({
                "broadcast_date": dt,
                "symbol": sym,
                "acquirer_name": acq,
                "person_category": (it.get("personCategory") or "").strip() or None,
                "transaction_type": tx,
                "shares": abs(shares),
                "trade_value": _num(it.get("secVal")),
                "after_holding_shares": _int_val(it.get("afterAcqSharesNo")),
                "after_holding_pct": _num(it.get("afterAcqSharesPer")),
                "source": "NSE PIT API",
            })
        return out

    # CSV path (CF-Insider-Trading-*.csv)
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        return []
    hdr = [h.strip().lower() for h in rows[0]]

    def _find(*names):
        for nm in names:
            for j, h in enumerate(hdr):
                if nm in h:
                    return j
        return None

    i_sym = _find("symbol")
    i_acq = _find("name of the acquirer", "acquirer", "person")
    i_cat = _find("category")
    i_tx = _find("transaction type", "mode of acquisition")
    i_sh = _find("no. of securities", "acquired/disposed", "shares")
    i_val = _find("value of security", "value")
    i_dt = _find("broadCast", "broadcast", "intimation", "date")

    if i_sym is None or i_acq is None or i_sh is None:
        return []

    for r in rows[1:]:
        if len(r) <= max(i_sym, i_acq, i_sh):
            continue
        sym = r[i_sym].strip().upper()
        acq = r[i_acq].strip()
        sh = _int_val(r[i_sh])
        if not sym or not acq or sh is None:
            continue
        tx_raw = r[i_tx].strip().upper() if i_tx is not None and i_tx < len(r) else "BUY"
        tx = "SELL" if "SELL" in tx_raw or "DISPOS" in tx_raw or "SALE" in tx_raw else "BUY"
        dt = _parse_date_any(r[i_dt]) if i_dt is not None and i_dt < len(r) else date.today()
        out.append({
            "broadcast_date": dt or date.today(),
            "symbol": sym,
            "acquirer_name": acq,
            "person_category": r[i_cat].strip() if i_cat is not None and i_cat < len(r) else None,
            "transaction_type": tx,
            "shares": abs(sh),
            "trade_value": _num(r[i_val]) if i_val is not None and i_val < len(r) else None,
            "source": "NSE PIT CSV",
        })
    return out


def sync_insider_trades(con, days_back: int = 183, *, session=None) -> dict:
    s = session or bootstrap_nse_session()
    frm = (date.today() - timedelta(days=days_back)).strftime("%d-%m-%Y")
    to_ = date.today().strftime("%d-%m-%Y")
    url = f"https://www.nseindia.com/api/corporates-pit?index=equities&from_date={frm}&to_date={to_}"
    r = http.fetch(url, source="nse-pit", session=s, save_name=f"pit_{date.today().strftime('%y%m%d')}_{days_back}d.json")
    if r.blocked():
        return {"status": "blocked", "message": r.error or "http:403"}
    if not r.ok():
        return {"status": "fail", "message": f"PIT fetch failed ({r.error})"}
    rows = parse_pit_json_or_csv(r.bytes)
    n = db.upsert_rows(
        con, "insider_trades", rows,
        keys=["broadcast_date", "symbol", "acquirer_name", "transaction_type", "shares"],
    )
    return {"status": "ok", "rows": n, "days_back": days_back}


def sync_deals_and_pit(con, *, days_back: int = 183) -> dict:
    """Fetches bulk/block deals + 6 months (default 183 days) of SEBI PIT insider trades cleanly."""
    t0 = datetime.now()
    s = bootstrap_nse_session()
    res_deals = sync_bulk_block_deals(con, session=s)
    if res_deals.get("status") == "blocked":
        log.error("NSE 403/429 on deals API. Manual drop: data/inbox/bulk_deals_*.csv & block_deals_*.csv -> make synkinbox.")
        return {"status": "partial", "blocked": True, "bulk_block": res_deals, "insider_pit": {"status": "skipped"}}
    res_pit = sync_insider_trades(con, days_back=days_back, session=s)
    if res_pit.get("status") == "blocked":
        log.error("NSE 403/429 on PIT API. Manual drop: data/inbox/CF-Insider-Trading-*.csv -> make synkinbox.")
    total_rows = int(res_deals.get("rows", 0)) + int(res_pit.get("rows", 0))
    blocked = res_pit.get("status") == "blocked"
    try:
        from app.query.snapshot import build_screener_snapshot
        build_screener_snapshot(con)
    except Exception as exc:
        log.warning("Post-deals snapshot rebuild failed: %s", exc)
    db.upsert_rows(con, "ingest_status", [{
        "id": f"sync_deals::{date.today()}",
        "job": "sync_deals",
        "run_date": date.today(),
        "status": "partial" if blocked else "ok",
        "rows": total_rows,
        "message": f"bulk_block={res_deals.get('rows', 0)} pit_{days_back}d={res_pit.get('rows', 0)}",
        "started_at": t0,
        "finished_at": datetime.now(),
    }], keys=["id"])
    return {"status": "partial" if blocked else "ok", "blocked": blocked, "bulk_block": res_deals, "insider_pit": res_pit}


# ------------------------------------------------------------------ Ownership Metrics Aggregator

def _default_ownership_snapshot() -> Dict[str, Optional[float]]:
    return {
        "mutual_fund_holding": None,
        "domestic_institutional_holding": None,
        "foreign_institutional_holding": None,
        "promoter_holding": None,
        "pledged_promoter_holdings": None,
        "retail_investor_holding": None,
        "insurance_firms_holding": None,
        "no_of_shareholders": None,
        "mf_holding_change_3m": None,
        "mf_holding_change_6m": None,
        "dii_holding_change_3m": None,
        "dii_holding_change_6m": None,
        "fii_holding_change_3m": None,
        "fii_holding_change_6m": None,
        "promoter_holding_change_3m": None,
        "promoter_holding_change_6m": None,
        "bulk_deals_1m_cumulative": None,
        "bulk_deals_3m_cumulative": None,
        "bulk_deals_6m_cumulative": None,
        "insider_trades_1m_cumulative": None,
        "insider_trades_3m_cumulative": None,
        "insider_trades_6m_cumulative": None,
    }


def _ownership_snapshot_from_inputs(
    q_rows: list[tuple],
    shares_out: Optional[float],
    bd_sums: tuple[float, float, float] | None = None,
    pit_sums: tuple[float, float, float] | None = None,
) -> Dict[str, Optional[float]]:
    """Computes ownership + deals/PIT metrics cleanly from pre-fetched rows."""
    out = _default_ownership_snapshot()

    if q_rows:
        q0 = q_rows[0]
        out["promoter_holding"] = q0[1]
        out["pledged_promoter_holdings"] = q0[2]
        out["mutual_fund_holding"] = q0[4]
        out["domestic_institutional_holding"] = q0[5]
        out["foreign_institutional_holding"] = q0[6]
        out["retail_investor_holding"] = q0[7]
        out["insurance_firms_holding"] = q0[8]
        out["no_of_shareholders"] = float(q0[9]) if q0[9] is not None else None

        if len(q_rows) >= 2:
            q1 = q_rows[1]
            if q0[4] is not None and q1[4] is not None:
                out["mf_holding_change_3m"] = round(q0[4] - q1[4], 4)
            if q0[5] is not None and q1[5] is not None:
                out["dii_holding_change_3m"] = round(q0[5] - q1[5], 4)
            if q0[6] is not None and q1[6] is not None:
                out["fii_holding_change_3m"] = round(q0[6] - q1[6], 4)
            if q0[1] is not None and q1[1] is not None:
                out["promoter_holding_change_3m"] = round(q0[1] - q1[1], 4)

        if len(q_rows) >= 3:
            q2 = q_rows[2]
            if q0[4] is not None and q2[4] is not None:
                out["mf_holding_change_6m"] = round(q0[4] - q2[4], 4)
            if q0[5] is not None and q2[5] is not None:
                out["dii_holding_change_6m"] = round(q0[5] - q2[5], 4)
            if q0[6] is not None and q2[6] is not None:
                out["fii_holding_change_6m"] = round(q0[6] - q2[6], 4)
            if q0[1] is not None and q2[1] is not None:
                out["promoter_holding_change_6m"] = round(q0[1] - q2[1], 4)

    if shares_out and shares_out > 0:
        b1, b3, b6 = bd_sums or (0.0, 0.0, 0.0)
        p1, p3, p6 = pit_sums or (0.0, 0.0, 0.0)
        denom = float(shares_out)
        out["bulk_deals_1m_cumulative"] = round((float(b1) / denom) * 100.0, 4)
        out["bulk_deals_3m_cumulative"] = round((float(b3) / denom) * 100.0, 4)
        out["bulk_deals_6m_cumulative"] = round((float(b6) / denom) * 100.0, 4)
        out["insider_trades_1m_cumulative"] = round((float(p1) / denom) * 100.0, 4)
        out["insider_trades_3m_cumulative"] = round((float(p3) / denom) * 100.0, 4)
        out["insider_trades_6m_cumulative"] = round((float(p6) / denom) * 100.0, 4)

    return out


def compute_ownership_snapshot(con, symbol: str, as_of: date | None = None) -> Dict[str, Optional[float]]:
    """Computes all 22 Ownership metrics for `symbol` per Section 10.5."""
    ref_dt = as_of or date.today()
    q_rows = con.execute(
        """
        SELECT quarter_end, promoter_pct, promoter_pledged_pct, promoter_pledged_total_pct,
               mf_pct, dii_pct, fii_pct, retail_pct, insurance_pct, no_of_shareholders
        FROM ownership_quarterly
        WHERE symbol = ? AND quarter_end <= ?
        ORDER BY quarter_end DESC
        LIMIT 3
        """,
        [symbol, ref_dt],
    ).fetchall()

    sh_row = con.execute(
        "SELECT shares_outstanding FROM ref_security WHERE nse_symbol = ? LIMIT 1", [symbol]
    ).fetchone()
    shares_out = sh_row[0] if sh_row and sh_row[0] and sh_row[0] > 0 else None

    bd_sums = (0.0, 0.0, 0.0)
    pit_sums = (0.0, 0.0, 0.0)
    if shares_out:
        d30 = ref_dt - timedelta(days=30)
        d91 = ref_dt - timedelta(days=91)
        d182 = ref_dt - timedelta(days=182)
        bd = con.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN deal_date > ? THEN CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN deal_date > ? THEN CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END), 0)
            FROM bulk_block_deals
            WHERE symbol = ? AND deal_date > ? AND deal_date <= ?
            """,
            [d30, d91, symbol, d182, ref_dt],
        ).fetchone()
        if bd:
            bd_sums = (float(bd[0]), float(bd[1]), float(bd[2]))

        pit = con.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN broadcast_date > ? THEN CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN broadcast_date > ? THEN CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END), 0)
            FROM insider_trades
            WHERE symbol = ? AND broadcast_date > ? AND broadcast_date <= ?
            """,
            [d30, d91, symbol, d182, ref_dt],
        ).fetchone()
        if pit:
            pit_sums = (float(pit[0]), float(pit[1]), float(pit[2]))

    return _ownership_snapshot_from_inputs(q_rows, shares_out, bd_sums, pit_sums)


def compute_all_ownership_snapshots_bulk(con, as_of: date | None = None) -> Dict[str, Dict[str, Optional[float]]]:
    """Set-based bulk computation of all 22 Ownership metrics across every NSE symbol (replaces N+1 queries)."""
    ref_dt = as_of or date.today()
    d30 = ref_dt - timedelta(days=30)
    d91 = ref_dt - timedelta(days=91)
    d182 = ref_dt - timedelta(days=182)

    q_by_sym: Dict[str, list[tuple]] = {}
    q_rows = con.execute(
        """
        SELECT symbol, quarter_end, promoter_pct, promoter_pledged_pct, promoter_pledged_total_pct,
               mf_pct, dii_pct, fii_pct, retail_pct, insurance_pct, no_of_shareholders
        FROM ownership_quarterly
        WHERE quarter_end <= ?
        QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY quarter_end DESC) <= 3
        ORDER BY symbol, quarter_end DESC
        """,
        [ref_dt],
    ).fetchall()
    for row in q_rows:
        sym = row[0]
        if sym:
            q_by_sym.setdefault(sym, []).append(row[1:])

    shares_by_sym: Dict[str, float] = {}
    for sym, sh in con.execute(
        "SELECT nse_symbol, shares_outstanding FROM ref_security WHERE nse_symbol IS NOT NULL AND shares_outstanding > 0"
    ).fetchall():
        shares_by_sym[sym] = float(sh)

    bd_by_sym: Dict[str, tuple[float, float, float]] = {}
    for sym, b1, b3, b6 in con.execute(
        """
        SELECT symbol,
            COALESCE(SUM(CASE WHEN deal_date > ? THEN CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN deal_date > ? THEN CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN buy_sell = 'BUY' THEN quantity ELSE -quantity END), 0)
        FROM bulk_block_deals
        WHERE deal_date > ? AND deal_date <= ?
        GROUP BY symbol
        """,
        [d30, d91, d182, ref_dt],
    ).fetchall():
        if sym:
            bd_by_sym[sym] = (float(b1), float(b3), float(b6))

    pit_by_sym: Dict[str, tuple[float, float, float]] = {}
    for sym, p1, p3, p6 in con.execute(
        """
        SELECT symbol,
            COALESCE(SUM(CASE WHEN broadcast_date > ? THEN CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN broadcast_date > ? THEN CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN transaction_type = 'BUY' THEN shares ELSE -shares END), 0)
        FROM insider_trades
        WHERE broadcast_date > ? AND broadcast_date <= ?
        GROUP BY symbol
        """,
        [d30, d91, d182, ref_dt],
    ).fetchall():
        if sym:
            pit_by_sym[sym] = (float(p1), float(p3), float(p6))

    all_syms = set(shares_by_sym) | set(q_by_sym) | set(bd_by_sym) | set(pit_by_sym)
    return {
        sym: _ownership_snapshot_from_inputs(
            q_by_sym.get(sym, []),
            shares_by_sym.get(sym),
            bd_by_sym.get(sym),
            pit_by_sym.get(sym),
        )
        for sym in all_syms
    }

