"""app/universe/master.py
Security Master repository and lookup index.
Provides indexed mappings for ISIN, NSE Symbol, BSE Code, and Normalized Name.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def normalize_company_name(name: str) -> str:
    """Normalizes company name for exact and fuzzy matching.
    Strips legal suffixes (Ltd, Limited, Pvt, Private, Inc, Corp), punctuation, and whitespace.
    """
    if not name:
        return ""
    s = name.lower()
    # Remove common parentheticals like (India), (EQ)
    s = re.sub(r"\(.*?\)", "", s)
    # Strip common corporate legal words
    suffixes = [
        r"\bltd\b", r"\blimited\b", r"\bpvt\b", r"\bprivate\b",
        r"\binc\b", r"\bincorporated\b", r"\bcorp\b", r"\bcorporation\b",
        r"\bco\b", r"\bcompany\b", r"\bllp\b", r"\bindustries\b",
        r"\bholdings\b", r"\benterprise\b", r"\benterprises\b",
    ]
    for suf in suffixes:
        s = re.sub(suf, "", s)
    # Remove punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse whitespace
    s = " ".join(s.split())
    return s.strip()


# Canonical reference securities (Equities & ETFs)
DEFAULT_SECURITIES_MASTER: List[Dict[str, Any]] = [
    {
        "isin": "INE002A01018",
        "nse_symbol": "RELIANCE",
        "bse_code": "500325",
        "name": "Reliance Industries Limited",
        "sector": "Energy",
        "sub_sector": "Oil & Gas - Refining & Marketing",
        "security_type": "Equity",
        "market_cap": 1639061.09,
        "close_price": 2420.50,
        "pe_ratio": 24.50,
        "return_on_equity": 8.95,
    },
    {
        "isin": "INE467B01029",
        "nse_symbol": "TCS",
        "bse_code": "532540",
        "name": "Tata Consultancy Services Limited",
        "sector": "Information Technology",
        "sub_sector": "IT Services & Consulting",
        "security_type": "Equity",
        "market_cap": 1150000.00,
        "close_price": 3150.00,
        "pe_ratio": 27.80,
        "return_on_equity": 43.50,
    },
    {
        "isin": "INE040A01034",
        "nse_symbol": "HDFCBANK",
        "bse_code": "500180",
        "name": "HDFC Bank Limited",
        "sector": "Financials",
        "sub_sector": "Private Banks",
        "security_type": "Equity",
        "market_cap": 900000.00,
        "close_price": 1450.00,
        "pe_ratio": 18.20,
        "return_on_equity": 16.20,
    },
    {
        "isin": "INE090A01021",
        "nse_symbol": "ICICIBANK",
        "bse_code": "532174",
        "name": "ICICI Bank Limited",
        "sector": "Financials",
        "sub_sector": "Private Banks",
        "security_type": "Equity",
        "market_cap": 650000.00,
        "close_price": 930.00,
        "pe_ratio": 16.90,
        "return_on_equity": 15.80,
    },
    {
        "isin": "INE009A01021",
        "nse_symbol": "INFY",
        "bse_code": "500209",
        "name": "Infosys Limited",
        "sector": "Information Technology",
        "sub_sector": "IT Services & Consulting",
        "security_type": "Equity",
        "market_cap": 580000.00,
        "close_price": 1400.00,
        "pe_ratio": 23.40,
        "return_on_equity": 29.10,
    },
    {
        "isin": "INE030A01027",
        "nse_symbol": "HINDUNILVR",
        "bse_code": "500696",
        "name": "Hindustan Unilever Limited",
        "sector": "Consumer Staples",
        "sub_sector": "FMCG - Household Products",
        "security_type": "Equity",
        "market_cap": 550000.00,
        "close_price": 2350.00,
        "pe_ratio": 54.20,
        "return_on_equity": 20.40,
    },
    {
        "isin": "INE154A01025",
        "nse_symbol": "ITC",
        "bse_code": "500875",
        "name": "ITC Limited",
        "sector": "Consumer Staples",
        "sub_sector": "FMCG - Tobacco",
        "security_type": "Equity",
        "market_cap": 520000.00,
        "close_price": 415.00,
        "pe_ratio": 26.50,
        "return_on_equity": 27.80,
    },
    {
        "isin": "INE062A01020",
        "nse_symbol": "SBIN",
        "bse_code": "500112",
        "name": "State Bank of India",
        "sector": "Financials",
        "sub_sector": "Public Banks",
        "security_type": "Equity",
        "market_cap": 500000.00,
        "close_price": 560.00,
        "pe_ratio": 9.80,
        "return_on_equity": 16.50,
    },
    {
        "isin": "INE397D01024",
        "nse_symbol": "BHARTIARTL",
        "bse_code": "532454",
        "name": "Bharti Airtel Limited",
        "sector": "Communication Services",
        "sub_sector": "Telecom Services",
        "security_type": "Equity",
        "market_cap": 480000.00,
        "close_price": 820.00,
        "pe_ratio": 72.10,
        "return_on_equity": 12.30,
    },
    {
        "isin": "INE018A01030",
        "nse_symbol": "LT",
        "bse_code": "500510",
        "name": "Larsen & Toubro Limited",
        "sector": "Industrials",
        "sub_sector": "Construction & Engineering",
        "security_type": "Equity",
        "market_cap": 420000.00,
        "close_price": 2950.00,
        "pe_ratio": 38.20,
        "return_on_equity": 14.70,
    },
    {
        "isin": "INE214T01019",
        "nse_symbol": "LTTS",
        "bse_code": "540115",
        "name": "L&T Technology Services Limited",
        "sector": "Information Technology",
        "sub_sector": "IT Services & Consulting",
        "security_type": "Equity",
        "market_cap": 52000.00,
        "close_price": 4850.00,
        "pe_ratio": 36.50,
        "return_on_equity": 22.00,
    },
    {
        "isin": "INE296A01024",
        "nse_symbol": "BAJFINANCE",
        "bse_code": "500034",
        "name": "Bajaj Finance Limited",
        "sector": "Financials",
        "sub_sector": "NBFC",
        "security_type": "Equity",
        "market_cap": 410000.00,
        "close_price": 6800.00,
        "pe_ratio": 31.40,
        "return_on_equity": 23.50,
    },
    {
        "isin": "INE021A01026",
        "nse_symbol": "ASIANPAINT",
        "bse_code": "500820",
        "name": "Asian Paints Limited",
        "sector": "Materials",
        "sub_sector": "Paints",
        "security_type": "Equity",
        "market_cap": 290000.00,
        "close_price": 3050.00,
        "pe_ratio": 52.00,
        "return_on_equity": 26.00,
    },
    {
        "isin": "INE585B01010",
        "nse_symbol": "MARUTI",
        "bse_code": "532500",
        "name": "Maruti Suzuki India Limited",
        "sector": "Consumer Discretionary",
        "sub_sector": "Auto - 4 Wheelers",
        "security_type": "Equity",
        "market_cap": 280000.00,
        "close_price": 9250.00,
        "pe_ratio": 29.50,
        "return_on_equity": 13.90,
    },
    {
        "isin": "INE280A01028",
        "nse_symbol": "TITAN",
        "bse_code": "500114",
        "name": "Titan Company Limited",
        "sector": "Consumer Discretionary",
        "sub_sector": "Gems, Jewellery & Watches",
        "security_type": "Equity",
        "market_cap": 260000.00,
        "close_price": 2980.00,
        "pe_ratio": 78.40,
        "return_on_equity": 30.20,
    },
    {
        "isin": "INE044A01036",
        "nse_symbol": "SUNPHARMA",
        "bse_code": "524715",
        "name": "Sun Pharmaceutical Industries Limited",
        "sector": "Health Care",
        "sub_sector": "Pharmaceuticals",
        "security_type": "Equity",
        "market_cap": 250000.00,
        "close_price": 1050.00,
        "pe_ratio": 32.10,
        "return_on_equity": 15.00,
    },
    # Ambiguous Pair 1: Tata Motors Ordinary vs Tata Motors DVR (Both share company name)
    {
        "isin": "INE155A01022",
        "nse_symbol": "TATAMOTORS",
        "bse_code": "500570",
        "name": "Tata Motors Limited",
        "sector": "Consumer Discretionary",
        "sub_sector": "Auto - 4 Wheelers",
        "security_type": "Equity",
        "market_cap": 240000.00,
        "close_price": 650.00,
        "pe_ratio": 14.20,
        "return_on_equity": 18.00,
    },
    {
        "isin": "IN9155A01020",
        "nse_symbol": "TATAMTRDVR",
        "bse_code": "570001",
        "name": "Tata Motors Limited",
        "sector": "Consumer Discretionary",
        "sub_sector": "Auto - 4 Wheelers",
        "security_type": "Equity",
        "market_cap": 18000.00,
        "close_price": 450.00,
        "pe_ratio": 12.10,
        "return_on_equity": 18.00,
    },
    # Ambiguous Pair 2: L&T Group Companies
    {
        "isin": "INE498L01015",
        "nse_symbol": "LTF",
        "bse_code": "533519",
        "name": "L&T Finance Limited",
        "sector": "Financials",
        "sub_sector": "NBFC",
        "security_type": "Equity",
        "market_cap": 42000.00,
        "close_price": 170.00,
        "pe_ratio": 17.50,
        "return_on_equity": 11.20,
    },
    # Additional benchmark securities
    {
        "isin": "INE081A01012",
        "nse_symbol": "TATASTEEL",
        "bse_code": "500470",
        "name": "Tata Steel Limited",
        "sector": "Materials",
        "sub_sector": "Steel & Iron Products",
        "security_type": "Equity",
        "market_cap": 150000.00,
        "close_price": 125.00,
        "pe_ratio": 11.20,
        "return_on_equity": 10.50,
    },
    {
        "isin": "INE238A01034",
        "nse_symbol": "AXISBANK",
        "bse_code": "532215",
        "name": "Axis Bank Limited",
        "sector": "Financials",
        "sub_sector": "Private Banks",
        "security_type": "Equity",
        "market_cap": 290000.00,
        "close_price": 970.00,
        "pe_ratio": 13.50,
        "return_on_equity": 16.80,
    },
    {
        "isin": "INE075A01022",
        "nse_symbol": "WIPRO",
        "bse_code": "507685",
        "name": "Wipro Limited",
        "sector": "Information Technology",
        "sub_sector": "IT Services & Consulting",
        "security_type": "Equity",
        "market_cap": 210000.00,
        "close_price": 410.00,
        "pe_ratio": 19.50,
        "return_on_equity": 14.20,
    },
    {
        "isin": "INE121A01024",
        "nse_symbol": "HCLTECH",
        "bse_code": "532281",
        "name": "HCL Technologies Limited",
        "sector": "Information Technology",
        "sub_sector": "IT Services & Consulting",
        "security_type": "Equity",
        "market_cap": 310000.00,
        "close_price": 1180.00,
        "pe_ratio": 21.00,
        "return_on_equity": 22.50,
    },
    {
        "isin": "INE257A01026",
        "nse_symbol": "BHEL",
        "bse_code": "500103",
        "name": "Bharat Heavy Electricals Limited",
        "sector": "Industrials",
        "sub_sector": "Heavy Electrical Equipment",
        "security_type": "Equity",
        "market_cap": 35000.00,
        "close_price": 102.00,
        "pe_ratio": 45.00,
        "return_on_equity": 2.50,
    },
    {
        "isin": "INE111A01025",
        "nse_symbol": "POWERGRID",
        "bse_code": "532898",
        "name": "Power Grid Corporation of India Limited",
        "sector": "Utilities",
        "sub_sector": "Electric Utilities",
        "security_type": "Equity",
        "market_cap": 180000.00,
        "close_price": 200.00,
        "pe_ratio": 12.00,
        "return_on_equity": 18.20,
    },
    {
        "isin": "INE733E01010",
        "nse_symbol": "NTPC",
        "bse_code": "532555",
        "name": "NTPC Limited",
        "sector": "Utilities",
        "sub_sector": "Electric Utilities",
        "security_type": "Equity",
        "market_cap": 190000.00,
        "close_price": 210.00,
        "pe_ratio": 11.50,
        "return_on_equity": 13.00,
    },
    # ETFs
    {
        "isin": "INF204KB14I2",
        "nse_symbol": "NIFTYBEES",
        "bse_code": "590101",
        "name": "Nippon India ETF Nifty BeES",
        "sector": "ETF",
        "sub_sector": "Index ETF",
        "security_type": "ETF",
        "market_cap": 25000.00,
        "close_price": 240.50,
        "pe_ratio": None,
        "return_on_equity": None,
    },
    {
        "isin": "INF204KB17I5",
        "nse_symbol": "GOLDBEES",
        "bse_code": "590095",
        "name": "Nippon India ETF Gold BeES",
        "sector": "ETF",
        "sub_sector": "Commodity ETF",
        "security_type": "ETF",
        "market_cap": 12000.00,
        "close_price": 55.20,
        "pe_ratio": None,
        "return_on_equity": None,
    },
]


class SecurityMasterIndex:
    """In-memory security master lookup index."""

    def __init__(self, securities: Optional[List[Dict[str, Any]]] = None):
        self.securities: List[Dict[str, Any]] = list(securities or DEFAULT_SECURITIES_MASTER)
        self.by_isin: Dict[str, Dict[str, Any]] = {}
        self.by_symbol: Dict[str, Dict[str, Any]] = {}
        self.by_bse_code: Dict[str, Dict[str, Any]] = {}
        self.by_norm_name: Dict[str, List[Dict[str, Any]]] = {}
        self._build_indexes()

    def _build_indexes(self):
        self.by_isin.clear()
        self.by_symbol.clear()
        self.by_bse_code.clear()
        self.by_norm_name.clear()

        for s in self.securities:
            isin = (s.get("isin") or "").strip().upper()
            if isin:
                self.by_isin[isin] = s

            sym = (s.get("nse_symbol") or "").strip().upper()
            if sym:
                self.by_symbol[sym] = s

            bse = str(s.get("bse_code") or "").strip()
            if bse:
                self.by_bse_code[bse] = s

            name = s.get("name") or ""
            norm = normalize_company_name(name)
            if norm:
                self.by_norm_name.setdefault(norm, []).append(s)

    def add_security(self, sec: Dict[str, Any]):
        self.securities.append(sec)
        self._build_indexes()
