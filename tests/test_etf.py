"""tests/test_etf.py
Offline tests for Step 4.7: AMFI 8-column NAVAll.txt parser, TER CSV parser, and 1Y annualized Tracking Error.
"""
from __future__ import annotations

import duckdb
import pytest

from app import db
from ingest.etf import compute_tracking_error, parse_nav_all_txt, parse_ter_csv_bytes, sync_amfi_nav_from_bytes

LIVE_NAV_SAMPLE = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date
Open Ended Schemes(Other Schemes - ETFs)
Nippon India Mutual Fund
135762;INF846K01WO1;-;Axis Children's Fund;Direct Plan;Growth Option;30.9434;09-Nov-2026
148912;INF204KB14I2;-;Nippon India ETF Nifty 50 BeES;Direct Plan;Growth Option;254.1230;09-Nov-2026
148913;INF204KB17I5;-;Nippon India ETF Gold BeES;Direct Plan;Growth Option;62.4510;09-Nov-2026
""".encode()

TER_CSV_SAMPLE = """Symbol,ISIN,Scheme Code,Scheme Name,Total Expense Ratio (%),As On Date
NIFTYBEES,INF204KB14I2,148912,Nippon India ETF Nifty 50 BeES,0.04,2026-11-01
GOLDBEES,INF204KB17I5,148913,Nippon India ETF Gold BeES,0.79,2026-11-01
""".encode()


def test_parse_nav_all_8_col_etf_filter(tmp_path):
    c = duckdb.connect(str(tmp_path / "etf.duckdb"))
    db.init_schema(c)
    res = sync_amfi_nav_from_bytes(c, LIVE_NAV_SAMPLE, etf_only=True)
    assert res["rows"] == 2
    rows = c.execute("SELECT scheme_code, isin, nav FROM etf_nav_daily ORDER BY scheme_code").fetchall()
    assert rows[0][0] == "148912" and rows[0][1] == "INF204KB14I2" and rows[0][2] == pytest.approx(254.1230)
    assert rows[1][0] == "148913"
    c.close()


def test_ter_and_tracking_error():
    ters = parse_ter_csv_bytes(TER_CSV_SAMPLE)
    assert len(ters) == 2
    assert ters[0]["symbol"] == "NIFTYBEES" and ters[0]["expense_ratio"] == pytest.approx(0.04)

    # Identical daily returns -> tracking error ~ 0.0
    idx = [100.0 * (1.001 ** i) for i in range(60)]
    etf_perf = [100.0 * (1.001 ** i) for i in range(60)]
    assert compute_tracking_error(etf_perf, idx) == pytest.approx(0.0, abs=1e-6)

    # Slight daily noise -> small positive annualized tracking error
    etf_noisy = [100.0 * (1.001 ** i) * (1.0005 if i % 2 == 0 else 0.9995) for i in range(60)]
    te = compute_tracking_error(etf_noisy, idx)
    assert te is not None and te > 0.0
