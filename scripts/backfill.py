#!/usr/bin/env python3
"""Backfill historical NSE CM + F&O bhavcopies, corporate actions, and vectorised technicals."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from ingest.backfill import backfill_prices  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Resumable EOD bhavcopy historical backfill.")
    parser.add_argument("--days", type=int, default=400, help="Target CM trading days (default 400; 1300 for 5Y CAGR)")
    parser.add_argument("--fo-days", type=int, default=10, help="Target recent F&O trading days (default 10)")
    parser.add_argument("--no-resume", action="store_true", help="Ignore prior ingest_progress checkpoints")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    con = db.connect()
    db.init_schema(con)
    try:
        res = backfill_prices(con, trading_days=args.days, fo_days=args.fo_days, resume=not args.no_resume)
    except KeyboardInterrupt:
        print("\nInterrupted by user; backfill progress saved in ingest_progress. Re-run to resume.", file=sys.stderr)
        return 130
    finally:
        con.close()

    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
