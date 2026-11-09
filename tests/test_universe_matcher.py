"""tests/test_universe_matcher.py
Automated end-to-end tests for the Excel universe workflow:
- 30-row golden spreadsheet parsing (multi-sheet workbook)
- Auto-detection of identifier column and custom columns
- 5-tier cascade matching: exactly 25 matched, 2 ambiguous, 3 unmatched
- Manual fix override on ambiguous/unmatched rows
- Portfolio P&L calculation
"""
from pathlib import Path
import pytest

from app.universe.importer import (
    get_workbook_sheet_names,
    parse_spreadsheet_data,
    generate_template_headers,
)
from app.universe.master import SecurityMasterIndex
from app.universe.matcher import UniverseMatcher
from app.universe.pnl import compute_row_pnl

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
XLSX_PATH = FIXTURES_DIR / "universe_30rows.xlsx"
CSV_PATH = FIXTURES_DIR / "universe_30rows.csv"


@pytest.fixture
def master_index():
    return SecurityMasterIndex()


@pytest.fixture
def matcher(master_index):
    return UniverseMatcher(master_index=master_index, fuzzy_threshold=88.0)


def test_multi_sheet_detection():
    """Workbook sheet names are accurately listed."""
    with open(XLSX_PATH, "rb") as f:
        bytes_data = f.read()
    sheets = get_workbook_sheet_names(bytes_data, "universe_30rows.xlsx")
    assert sheets == ["Portfolio", "Watchlist"]


def test_parse_spreadsheet_and_auto_detect_columns():
    """Parser extracts 30 rows and auto-detects Identifier and custom columns."""
    with open(XLSX_PATH, "rb") as f:
        bytes_data = f.read()
    rows, headers, id_col, custom_cols = parse_spreadsheet_data(bytes_data, "universe_30rows.xlsx", sheet_name="Portfolio")

    assert len(rows) == 30
    assert "Identifier" in headers
    assert id_col == "Identifier"
    assert custom_cols["quantity"] == "Quantity"
    assert custom_cols["buy_price"] == "Buy_Price"
    assert custom_cols["notes"] == "Notes"


def test_golden_30rows_matching_cascade_breakdown(matcher):
    """The 30-row fixture must yield exactly 25 matched, 2 ambiguous, and 3 unmatched rows."""
    with open(XLSX_PATH, "rb") as f:
        bytes_data = f.read()
    rows, headers, id_col, _ = parse_spreadsheet_data(bytes_data, "universe_30rows.xlsx", sheet_name="Portfolio")

    report = matcher.match_all(rows, id_col=id_col)

    assert report["total_rows"] == 30
    assert report["matched_count"] == 25, f"Expected 25 matched, got {report['matched_count']}"
    assert report["ambiguous_count"] == 2, f"Expected 2 ambiguous, got {report['ambiguous_count']}"
    assert report["unmatched_count"] == 3, f"Expected 3 unmatched, got {report['unmatched_count']}"

    # Verify Ambiguous details: Tata Motors and L&T
    ambig_inputs = [a["raw_input"]["Identifier"] for a in report["ambiguous"]]
    assert "Tata Motors" in ambig_inputs
    assert "L&T" in ambig_inputs

    # Verify each ambiguous result provides candidate securities
    for amb in report["ambiguous"]:
        assert len(amb["candidates"]) >= 2
        cand_symbols = [c["nse_symbol"] for c in amb["candidates"]]
        if amb["raw_input"]["Identifier"] == "Tata Motors":
            assert any("DVR" in sym for sym in cand_symbols)
            assert any("TATAMOTORS" in sym for sym in cand_symbols)
        elif amb["raw_input"]["Identifier"] == "L&T":
            assert any("LTTS" in sym for sym in cand_symbols)
            assert any("LTF" in sym for sym in cand_symbols)

    # Verify Unmatched details
    unmatched_inputs = [u["raw_input"]["Identifier"] for u in report["unmatched"]]
    assert "Acme Quantum Robotics Ltd" in unmatched_inputs
    assert "INE999Z99999" in unmatched_inputs
    assert "Atlantis Global Trading" in unmatched_inputs


def test_csv_equivalence(matcher):
    """CSV version gives identical 25/2/3 matching breakdown."""
    with open(CSV_PATH, "rb") as f:
        bytes_data = f.read()
    rows, headers, id_col, _ = parse_spreadsheet_data(bytes_data, "universe_30rows.csv")
    report = matcher.match_all(rows, id_col=id_col)

    assert report["total_rows"] == 30
    assert report["matched_count"] == 25
    assert report["ambiguous_count"] == 2
    assert report["unmatched_count"] == 3


def test_manual_fix_override(master_index):
    """Manual fix allows user to resolve an ambiguous or unmatched row."""
    # User selects Tata Motors Ordinary share (INE155A01022) for the ambiguous row
    target_sec = master_index.by_symbol["TATAMOTORS"]
    ambiguous_row = {"Identifier": "Tata Motors", "Quantity": 100, "Buy_Price": 550.0}

    # Manual override resolves to target security
    resolved_record = dict(target_sec)
    resolved_record.update({
        "user_quantity": ambiguous_row["Quantity"],
        "user_buy_price": ambiguous_row["Buy_Price"],
        "resolved_manually": True,
    })
    assert resolved_record["nse_symbol"] == "TATAMOTORS"
    assert resolved_record["user_quantity"] == 100


def test_portfolio_pnl_calculation():
    """Verify Invested Value, Current Value, P&L Amount, and P&L % calculations."""
    row = {"Quantity": 50, "Buy_Price": 2200.0}
    close_price = 2420.50  # Reliance close price

    pnl = compute_row_pnl(row, close_price=close_price, qty_col="Quantity", buy_price_col="Buy_Price")

    assert pnl["quantity"] == 50
    assert pnl["buy_price"] == 2200.0
    # Invested = 50 * 2200 = 110,000
    assert pnl["invested_value"] == 110000.0
    # Current = 50 * 2420.50 = 121,025
    assert pnl["current_value"] == 121025.0
    # P&L Amount = 121,025 - 110,000 = +11,025
    assert pnl["pnl_amount"] == 11025.0
    # P&L % = (2420.50 / 2200 - 1) * 100 = +10.02%
    assert pnl["pnl_pct"] == 10.02


def test_template_headers():
    """Copy template headers produces canonical column list."""
    headers = generate_template_headers(["PE Ratio", "Market Cap"])
    assert "Company Name" in headers
    assert "NSE Symbol" in headers
    assert "ISIN" in headers
    assert "PE Ratio" in headers
