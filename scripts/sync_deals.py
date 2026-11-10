#!/usr/bin/env python3
"""Sync NSE Bulk/Block deals + 6 months (183 days) of SEBI PIT insider trades."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from ingest.ownership import sync_deals_and_pit  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Sync bulk/block institutional deals and SEBI PIT insider disclosures.")
    parser.add_argument("--days", type=int, default=183, help="Days of PIT insider history to retain (default 183 = 6M)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    con = db.connect()
    db.init_schema(con)
    try:
        res = sync_deals_and_pit(con, days_back=args.days)
    finally:
        con.close()

    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
