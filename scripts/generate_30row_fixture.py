#!/usr/bin/env python3
"""Generates the 30-row golden end-to-end test sheet:
- 25 matched rows (mix of ISIN, symbol, BSE code, name)
- 2 ambiguous rows (Tata Motors, Larsen & Toubro)
- 3 unmatched rows (fictional/invalid ISIN)
Includes Quantity, Buy Price, and Notes columns for P&L calculation tests.
Saves to tests/fixtures/universe_30rows.xlsx and .csv.
"""
from __future__ import annotations

import csv
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

ROWS = [
    # 25 Matched Rows
    {"Identifier": "INE002A01018", "Type": "ISIN", "Quantity": 50, "Buy_Price": 2200.0, "Notes": "Core energy holding"},
    {"Identifier": "TCS", "Type": "Symbol", "Quantity": 30, "Buy_Price": 3200.0, "Notes": "IT bellwether"},
    {"Identifier": "INE040A01034", "Type": "ISIN", "Quantity": 100, "Buy_Price": 1500.0, "Notes": "Banking leader"},
    {"Identifier": "ICICIBANK", "Type": "Symbol", "Quantity": 120, "Buy_Price": 850.0, "Notes": "Private bank"},
    {"Identifier": "INE009A01021", "Type": "ISIN", "Quantity": 80, "Buy_Price": 1350.0, "Notes": "IT export"},
    {"Identifier": "HINDUNILVR", "Type": "Symbol", "Quantity": 40, "Buy_Price": 2400.0, "Notes": "FMCG staple"},
    {"Identifier": "500875", "Type": "BSE Code", "Quantity": 200, "Buy_Price": 380.0, "Notes": "High dividend"},
    {"Identifier": "SBIN", "Type": "Symbol", "Quantity": 150, "Buy_Price": 520.0, "Notes": "PSU bank"},
    {"Identifier": "BHARTIARTL", "Type": "Symbol", "Quantity": 90, "Buy_Price": 780.0, "Notes": "Telecom"},
    {"Identifier": "BAJFINANCE", "Type": "Symbol", "Quantity": 15, "Buy_Price": 6200.0, "Notes": "NBFC lending"},
    {"Identifier": "500820", "Type": "BSE Code", "Quantity": 25, "Buy_Price": 2900.0, "Notes": "Decorative paints"},
    {"Identifier": "MARUTI", "Type": "Symbol", "Quantity": 10, "Buy_Price": 8800.0, "Notes": "Auto 4-wheeler"},
    {"Identifier": "INE280A01028", "Type": "ISIN", "Quantity": 35, "Buy_Price": 2700.0, "Notes": "Jewellery retail"},
    {"Identifier": "SUNPHARMA", "Type": "Symbol", "Quantity": 60, "Buy_Price": 980.0, "Notes": "Pharma generic"},
    {"Identifier": "Tata Steel Limited", "Type": "Name", "Quantity": 300, "Buy_Price": 115.0, "Notes": "Metals & mining"},
    {"Identifier": "AXISBANK", "Type": "Symbol", "Quantity": 70, "Buy_Price": 910.0, "Notes": "Private bank"},
    {"Identifier": "Wipro Limited", "Type": "Name", "Quantity": 110, "Buy_Price": 390.0, "Notes": "IT services"},
    {"Identifier": "HCL Technologies Limited", "Type": "Name", "Quantity": 45, "Buy_Price": 1100.0, "Notes": "IT dividend"},
    {"Identifier": "500103", "Type": "BSE Code", "Quantity": 250, "Buy_Price": 85.0, "Notes": "Capital goods"},
    {"Identifier": "POWERGRID", "Type": "Symbol", "Quantity": 180, "Buy_Price": 190.0, "Notes": "Power transmission"},
    {"Identifier": "NTPC Limited", "Type": "Name", "Quantity": 220, "Buy_Price": 180.0, "Notes": "Power generation"},
    {"Identifier": "INF204KB14I2", "Type": "ISIN", "Quantity": 500, "Buy_Price": 220.0, "Notes": "Nifty 50 ETF"},
    {"Identifier": "GOLDBEES", "Type": "Symbol", "Quantity": 800, "Buy_Price": 50.0, "Notes": "Gold ETF"},
    {"Identifier": "540115", "Type": "BSE Code", "Quantity": 12, "Buy_Price": 4500.0, "Notes": "ER&D IT"},
    {"Identifier": "INF204KB17I5", "Type": "ISIN", "Quantity": 400, "Buy_Price": 52.0, "Notes": "Commodity gold"},

    # 2 Ambiguous Rows
    {"Identifier": "Tata Motors", "Type": "Name", "Quantity": 100, "Buy_Price": 550.0, "Notes": "Ambiguous: matches Tata Motors & Tata Motors DVR"},
    {"Identifier": "L&T", "Type": "Name", "Quantity": 20, "Buy_Price": 2800.0, "Notes": "Ambiguous: matches Larsen & Toubro & L&T Tech Services"},

    # 3 Unmatched Rows
    {"Identifier": "Acme Quantum Robotics Ltd", "Type": "Name", "Quantity": 100, "Buy_Price": 100.0, "Notes": "Unmatched: fictional entity"},
    {"Identifier": "INE999Z99999", "Type": "ISIN", "Quantity": 50, "Buy_Price": 250.0, "Notes": "Unmatched: invalid ISIN"},
    {"Identifier": "Atlantis Global Trading", "Type": "Name", "Quantity": 75, "Buy_Price": 50.0, "Notes": "Unmatched: non-existent firm"},
]


def main():
    headers = ["Identifier", "Type", "Quantity", "Buy_Price", "Notes"]

    # 1. Write CSV
    csv_path = FIXTURES_DIR / "universe_30rows.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows to {csv_path}")

    # 2. Write XLSX
    xlsx_path = FIXTURES_DIR / "universe_30rows.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Portfolio"
    ws.append(headers)
    for r in ROWS:
        ws.append([r[h] for h in headers])

    # Add second sheet for multi-sheet test
    ws2 = wb.create_sheet(title="Watchlist")
    ws2.append(["Symbol", "Target_Price"])
    ws2.append(["RELIANCE", 2800])
    ws2.append(["TCS", 3500])

    wb.save(xlsx_path)
    print(f"Wrote {len(ROWS)} rows to {xlsx_path} (with 2 sheets: Portfolio, Watchlist)")


if __name__ == "__main__":
    main()
