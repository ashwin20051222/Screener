"""app/universe/matcher.py
5-Tier Security Master Matcher Cascade:
1. ISIN (12-char exact)
2. NSE Symbol (exact uppercase)
3. BSE Code (exact numeric code)
4. Exact Normalized Name
5. Fuzzy Name (RapidFuzz token_set_ratio with threshold from config, default 88)
Accurately distinguishes Matched, Ambiguous, and Unmatched rows without dropping any data.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import rapidfuzz.fuzz as fuzz

from app.universe.master import SecurityMasterIndex, normalize_company_name


class MatchResult:
    """Detailed result of matching a single input record."""

    def __init__(
        self,
        row_index: int,
        raw_input: Dict[str, Any],
        status: str,  # "matched" | "ambiguous" | "unmatched"
        matched_security: Optional[Dict[str, Any]] = None,
        match_tier: Optional[str] = None,  # "isin" | "nse_symbol" | "bse_code" | "normalized_name" | "fuzzy_name"
        confidence: float = 0.0,
        candidates: Optional[List[Dict[str, Any]]] = None,
        notes: str = "",
    ):
        self.row_index = row_index
        self.raw_input = raw_input
        self.status = status
        self.matched_security = matched_security
        self.match_tier = match_tier
        self.confidence = confidence
        self.candidates = candidates or []
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_index": self.row_index,
            "raw_input": self.raw_input,
            "status": self.status,
            "matched_security": self.matched_security,
            "match_tier": self.match_tier,
            "confidence": round(self.confidence, 1),
            "candidates": self.candidates,
            "notes": self.notes,
        }


class UniverseMatcher:
    """Matches uploaded spreadsheets against the security master index."""

    def __init__(self, master_index: SecurityMasterIndex, fuzzy_threshold: float = 88.0):
        self.master = master_index
        self.fuzzy_threshold = fuzzy_threshold

    def match_row(
        self,
        row: Dict[str, Any],
        row_index: int,
        id_col: Optional[str] = None,
    ) -> MatchResult:
        """Matches a single row using the 5-tier cascade."""
        # Candidate value extraction
        val = str(row.get(id_col) or "").strip() if id_col else ""
        if not val:
            # Try common identifier column names
            for col in ["isin", "symbol", "ticker", "bse_code", "name", "company", "company_name", "stock"]:
                if col in row and row[col]:
                    val = str(row[col]).strip()
                    break

        if not val:
            return MatchResult(
                row_index=row_index,
                raw_input=row,
                status="unmatched",
                notes="No identifier value found in row",
            )

        clean_val = val.strip().upper()

        # Tier 1: ISIN match (12 chars starting with country code e.g. IN...)
        if re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", clean_val):
            if clean_val in self.master.by_isin:
                return MatchResult(
                    row_index=row_index,
                    raw_input=row,
                    status="matched",
                    matched_security=self.master.by_isin[clean_val],
                    match_tier="isin",
                    confidence=100.0,
                    notes=f"Exact ISIN match: {clean_val}",
                )

        # Tier 2: NSE Symbol match
        if clean_val in self.master.by_symbol:
            return MatchResult(
                row_index=row_index,
                raw_input=row,
                status="matched",
                matched_security=self.master.by_symbol[clean_val],
                match_tier="nse_symbol",
                confidence=100.0,
                notes=f"Exact NSE symbol match: {clean_val}",
            )

        # Tier 3: BSE Code match (5 or 6 digits)
        clean_code = val.strip()
        if clean_code in self.master.by_bse_code:
            return MatchResult(
                row_index=row_index,
                raw_input=row,
                status="matched",
                matched_security=self.master.by_bse_code[clean_code],
                match_tier="bse_code",
                confidence=100.0,
                notes=f"Exact BSE code match: {clean_code}",
            )

        # Tier 4: Exact Normalized Name match
        norm = normalize_company_name(val)
        if norm and norm in self.master.by_norm_name:
            candidates = self.master.by_norm_name[norm]
            if len(candidates) == 1:
                return MatchResult(
                    row_index=row_index,
                    raw_input=row,
                    status="matched",
                    matched_security=candidates[0],
                    match_tier="normalized_name",
                    confidence=98.0,
                    notes=f"Exact normalized name match: '{norm}'",
                )
            else:
                # Multiple securities with identical normalized names (e.g. ordinary vs DVR share classes)
                return MatchResult(
                    row_index=row_index,
                    raw_input=row,
                    status="ambiguous",
                    match_tier="normalized_name",
                    confidence=95.0,
                    candidates=candidates,
                    notes=f"Multiple securities matched normalized name '{norm}' ({len(candidates)} candidates)",
                )

        # Tier 5: Fuzzy Name Match using RapidFuzz
        best_candidates: List[Tuple[float, Dict[str, Any]]] = []
        for sec in self.master.securities:
            sec_name = sec.get("name") or ""
            sec_norm = normalize_company_name(sec_name)
            # Compare both raw names and normalized names
            score_raw = fuzz.token_set_ratio(val.lower(), sec_name.lower())
            score_norm = fuzz.token_set_ratio(norm, sec_norm) if norm and sec_norm else 0.0
            score = max(score_raw, score_norm)
            if score >= self.fuzzy_threshold:
                best_candidates.append((score, sec))

        # Sort candidates descending by score
        best_candidates.sort(key=lambda x: x[0], reverse=True)

        if not best_candidates:
            return MatchResult(
                row_index=row_index,
                raw_input=row,
                status="unmatched",
                confidence=0.0,
                notes=f"No matching security found above threshold ({self.fuzzy_threshold})",
            )

        top_score = best_candidates[0][0]
        # Ambiguity check: if multiple candidates are within 3 points of top score, or top candidate is borderline
        close_candidates = [
            c[1] for c in best_candidates
            if (top_score - c[0] <= 3.0 and c[0] >= self.fuzzy_threshold)
        ]

        if len(close_candidates) > 1:
            return MatchResult(
                row_index=row_index,
                raw_input=row,
                status="ambiguous",
                match_tier="fuzzy_name",
                confidence=top_score,
                candidates=close_candidates,
                notes=f"Ambiguous match: {len(close_candidates)} candidates with score ~{top_score:.1f}%",
            )

        return MatchResult(
            row_index=row_index,
            raw_input=row,
            status="matched",
            matched_security=best_candidates[0][1],
            match_tier="fuzzy_name",
            confidence=top_score,
            notes=f"Fuzzy name match (score: {top_score:.1f}%)",
        )

    def match_all(
        self,
        rows: List[Dict[str, Any]],
        id_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Matches a collection of rows and compiles a complete Match Report."""
        results: List[MatchResult] = []
        matched: List[Dict[str, Any]] = []
        ambiguous: List[Dict[str, Any]] = []
        unmatched: List[Dict[str, Any]] = []

        for idx, row in enumerate(rows):
            res = self.match_row(row, row_index=idx, id_col=id_col)
            results.append(res)
            res_dict = res.to_dict()
            if res.status == "matched":
                matched.append(res_dict)
            elif res.status == "ambiguous":
                ambiguous.append(res_dict)
            else:
                unmatched.append(res_dict)

        total = len(rows)
        return {
            "total_rows": total,
            "matched_count": len(matched),
            "ambiguous_count": len(ambiguous),
            "unmatched_count": len(unmatched),
            "matched": matched,
            "ambiguous": ambiguous,
            "unmatched": unmatched,
            "all_results": [r.to_dict() for r in results],
        }
