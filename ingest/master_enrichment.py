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


def enrich_securities_from_constituents(con) -> dict:
    """Propagates official industry classification from ref_index_constituent & ETF flags into ref_security."""
    rows = con.execute(
        """
        SELECT DISTINCT symbol, industry
        FROM ref_index_constituent
        WHERE industry IS NOT NULL AND TRIM(industry) <> ''
        """
    ).fetchall()

    updated = 0
    unmapped: list[str] = []
    for sym, raw_ind in rows:
        ui_sector = map_industry_to_sector(raw_ind)
        if ui_sector == "INDUSTRY_UNMAPPED":
            unmapped.append(f"{sym}:{raw_ind}")
            ui_sector = None
        is_fin, template = detect_financial_template(raw_ind, ui_sector)
        con.execute(
            """
            UPDATE ref_security
            SET industry = COALESCE(industry, ?),
                sub_sector = COALESCE(sub_sector, ?),
                sector = COALESCE(sector, ?),
                is_financial_institution = ?,
                financial_template = ?
            WHERE nse_symbol = ? AND COALESCE(is_etf, FALSE) = FALSE
            """,
            [raw_ind, raw_ind, ui_sector, is_fin, template, sym],
        )
        updated += 1

    # ETF pseudo-sector enforcement per Section 10.12
    con.execute(
        """
        UPDATE ref_security
        SET sector = 'ETF', sub_sector = COALESCE(sub_sector, 'Index / Commodity ETF')
        WHERE is_etf = TRUE
        """
    )

    if unmapped:
        log.warning("Unmapped exchange industries (%d): %s", len(unmapped), unmapped[:10])
    return {"updated": updated, "unmapped_count": len(unmapped)}
