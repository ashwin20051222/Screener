"""ingest/master_enrichment.py
Enriches ref_security using official index constituents + config/sector_map.yaml + ETF flags.
Maps raw exchange industries into the 11 UI sectors (+ ETF pseudo-sector) and financial templates.
"""
from __future__ import annotations

import logging
from typing import Dict

from app.config import sector_map

log = logging.getLogger(__name__)


def map_industry_to_sector(raw_industry: str | None) -> str | None:
    if not raw_industry:
        return None
    smap = sector_map()
    mapping: Dict[str, str] = smap.get("mapping") or {}
    key = raw_industry.strip().lower()
    if key in mapping:
        return mapping[key]
    # Substring fallback matching known canonical keys cleanly
    for k, ui_sec in mapping.items():
        if k in key or key in k:
            return ui_sec
    return smap.get("default") or None


def detect_financial_template(raw_industry: str | None, sector: str | None) -> tuple[bool, str]:
    """Returns (is_financial_institution, financial_template)."""
    smap = sector_map()
    hints = smap.get("financials_subsector_hint") or {}
    low_ind = (raw_industry or "").strip().lower()
    low_sec = (sector or "").strip().lower()

    is_bank = any(tok in low_ind for tok in (hints.get("is_bank") or ["bank"]))
    is_insurer = any(tok in low_ind for tok in (hints.get("is_insurer") or ["insur"]))
    is_nbfc = any(tok in low_ind for tok in (hints.get("is_consume_finance") or ["nbfc", "finance"]))

    if is_bank:
        return True, "banks"
    if is_insurer:
        return True, "insurers"
    if is_nbfc or low_sec == "financials":
        return True, "banks" if "bank" in low_ind else "industrials"
    if low_sec == "utilities" or "power" in low_ind or "utilities" in low_ind:
        return False, "utilities"
    return False, "industrials"


def classify_security_industries(
    con,
    symbol_industry_pairs: list[tuple[str, str]],
    *,
    key_col: str = "nse_symbol",
    overwrite: bool = True,
) -> dict:
    """Applies official industry strings onto `ref_security` using `config/sector_map.yaml`.

    Unmapped raw industries are stored cleanly on `industry`/`sub_sector` while `sector` stays NULL
    (rendered honestly as `"Unclassified"`, never guessed as `"Industrials"`).
    """
    updated = 0
    unmapped_examples: list[str] = []
    unmapped_industries: set[str] = set()
    for sym_key, raw_ind in symbol_industry_pairs:
        if not sym_key or not raw_ind or not str(raw_ind).strip():
            continue
        ind_clean = str(raw_ind).strip()
        ui_sector = map_industry_to_sector(ind_clean)
        if ui_sector == "INDUSTRY_UNMAPPED":
            unmapped_industries.add(ind_clean)
            if len(unmapped_examples) < 25:
                unmapped_examples.append(f"{sym_key}:{ind_clean}")
            ui_sector = None
        is_fin, template = detect_financial_template(ind_clean, ui_sector)
        if overwrite:
            con.execute(
                f"""
                UPDATE ref_security
                SET industry = ?,
                    sub_sector = ?,
                    sector = ?,
                    is_financial_institution = ?,
                    financial_template = ?
                WHERE {key_col} = ? AND COALESCE(is_etf, FALSE) = FALSE
                """,
                [ind_clean, ind_clean, ui_sector, is_fin, template, sym_key],
            )
        else:
            con.execute(
                f"""
                UPDATE ref_security
                SET industry = COALESCE(industry, ?),
                    sub_sector = COALESCE(sub_sector, ?),
                    sector = COALESCE(sector, ?),
                    is_financial_institution = ?,
                    financial_template = ?
                WHERE {key_col} = ? AND COALESCE(is_etf, FALSE) = FALSE
                """,
                [ind_clean, ind_clean, ui_sector, is_fin, template, sym_key],
            )
        updated += 1

    if unmapped_industries:
        log.warning("Unmapped exchange industries (%d distinct): %s", len(unmapped_industries), sorted(unmapped_industries))
    return {
        "updated": updated,
        "unmapped_count": len(unmapped_industries),
        "unmapped_industries": sorted(unmapped_industries),
        "unmapped_examples": unmapped_examples,
    }


def get_unmapped_industries(con) -> list[dict]:
    """Returns distinct official industry labels in `ref_security` that lack a mapped `sector`."""
    rows = con.execute(
        """
        SELECT industry, COUNT(*) AS cnt
        FROM ref_security
        WHERE sector IS NULL AND industry IS NOT NULL AND TRIM(industry) <> ''
        GROUP BY industry
        ORDER BY cnt DESC, industry ASC
        """
    ).fetchall()
    return [{"industry": ind, "count": int(cnt)} for ind, cnt in rows]


def enrich_securities_from_constituents(con) -> dict:
    """Propagates official industry classification from ref_index_constituent & ETF flags into ref_security."""
    rows = con.execute(
        """
        SELECT DISTINCT symbol, industry
        FROM ref_index_constituent
        WHERE industry IS NOT NULL AND TRIM(industry) <> ''
        """
    ).fetchall()

    res = classify_security_industries(con, [(sym, raw_ind) for sym, raw_ind in rows], overwrite=True)

    # ETF pseudo-sector enforcement per Section 10.12
    con.execute(
        """
        UPDATE ref_security
        SET sector = 'ETF', sub_sector = COALESCE(sub_sector, 'Index / Commodity ETF')
        WHERE is_etf = TRUE
        """
    )
    return res

