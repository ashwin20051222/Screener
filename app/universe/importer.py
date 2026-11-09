"""app/universe/importer.py
Spreadsheet importer supporting .xlsx, .xls, and .csv formats:
- Multi-sheet workbook detection and sheet extraction
- Auto-detection of identifier columns (ISIN, Symbol, Code, Company Name)
- Extraction of user custom columns (Quantity, Buy Price, Notes, etc.)
- Template headers generator for prefilling user spreadsheets
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple
import openpyxl


IDENTIFIER_CANDIDATE_PATTERNS = [
    (r"\bisin\b", "isin"),
    (r"\b(nse[_\s]?)?symbol\b", "symbol"),
    (r"\bticker\b", "symbol"),
    (r"\bbse[_\s]?code\b", "bse_code"),
    (r"\bscrip[_\s]?code\b", "bse_code"),
    (r"\bcompany([_\s]?name)?\b", "company_name"),
    (r"\bsecurity([_\s]?name)?\b", "company_name"),
    (r"\bscheme([_\s]?name)?\b", "company_name"),
    (r"\bstock([_\s]?name)?\b", "company_name"),
    (r"\bname\b", "company_name"),
]

CUSTOM_COLUMN_KEYWORDS = {
    "quantity": ["quantity", "qty", "shares", "units", "holding_qty"],
    "buy_price": ["buy_price", "purchase_price", "cost_price", "avg_price", "avg_cost", "entry_price"],
    "notes": ["notes", "remarks", "comment", "tags"],
    "date": ["buy_date", "purchase_date", "trade_date", "date"],
}


def get_workbook_sheet_names(file_bytes: bytes, filename: str) -> List[str]:
    """Returns sheet names for .xlsx workbooks; returns ['Sheet1'] for CSV files."""
    if filename.lower().endswith(".csv"):
        return ["Sheet1"]

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        return wb.sheetnames
    except Exception:
        return ["Sheet1"]


def auto_detect_identifier_column(headers: List[str]) -> Optional[str]:
    """Auto-detects the most probable identifier column from headers."""
    for pattern, _ in IDENTIFIER_CANDIDATE_PATTERNS:
        for h in headers:
            clean_h = str(h).strip().lower()
            if re.search(pattern, clean_h):
                return h
    return headers[0] if headers else None


def identify_custom_columns(headers: List[str]) -> Dict[str, Optional[str]]:
    """Identifies portfolio custom columns (quantity, buy_price, notes, date) from headers."""
    detected: Dict[str, Optional[str]] = {
        "quantity": None,
        "buy_price": None,
        "notes": None,
        "date": None,
    }
    for col_type, kw_list in CUSTOM_COLUMN_KEYWORDS.items():
        for h in headers:
            clean_h = str(h).strip().lower()
            if any(kw == clean_h or kw in clean_h for kw in kw_list):
                detected[col_type] = h
                break
    return detected


def parse_spreadsheet_data(
    file_bytes: bytes,
    filename: str,
    sheet_name: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[str], Optional[str], Dict[str, Optional[str]]]:
    """Parses a spreadsheet (.xlsx, .csv) into structured records.
    Returns (rows, headers, auto_detected_id_col, detected_custom_cols).
    """
    headers: List[str] = []
    rows: List[Dict[str, Any]] = []

    if filename.lower().endswith(".csv"):
        text = file_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.reader(io.StringIO(text))
        all_lines = list(reader)
        if all_lines:
            headers = [h.strip() for h in all_lines[0] if h.strip()]
            for line in all_lines[1:]:
                if not any(line):
                    continue
                row_dict = {
                    headers[i]: (line[i].strip() if i < len(line) else "")
                    for i in range(len(headers))
                }
                rows.append(row_dict)
    else:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        active_sheet = sheet_name if (sheet_name and sheet_name in wb.sheetnames) else wb.sheetnames[0]
        ws = wb[active_sheet]

        data = list(ws.iter_rows(values_only=True))
        if data:
            raw_headers = data[0]
            headers = [str(h).strip() for h in raw_headers if h is not None and str(h).strip()]
            for raw_row in data[1:]:
                if not any(raw_row):
                    continue
                row_dict = {
                    headers[i]: (raw_row[i] if i < len(raw_row) and raw_row[i] is not None else "")
                    for i in range(len(headers))
                }
                rows.append(row_dict)

    id_col = auto_detect_identifier_column(headers)
    custom_cols = identify_custom_columns(headers)

    return rows, headers, id_col, custom_cols


def generate_template_headers(extra_fields: Optional[List[str]] = None) -> List[str]:
    """Produces canonical header template list for user downloads."""
    base = [
        "Company Name",
        "NSE Symbol",
        "ISIN",
        "BSE Code",
        "Quantity",
        "Buy Price",
        "Notes",
    ]
    if extra_fields:
        base.extend(extra_fields)
    return base
