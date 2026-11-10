#!/usr/bin/env python3
"""Sync shares outstanding (Market Cap unblock) via bulk NSE PR MCAP + resumable SHP XBRL."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from ingest import nse as nse_mod  # noqa: E402
from ingest.ownership import sync_shp_batch  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Unblock Market Cap via bulk PR MCAP and/or SHP XBRL.")
    parser.add_argument("--universe", default="nifty100", choices=["nifty100", "nifty500", "all"])
    parser.add_argument("--per-symbol", action="store_true", help="Also fetch per-symbol SHP XBRL after bulk PR MCAP")
    parser.add_argument("--no-resume", action="store_true", help="Ignore prior ingest_progress checkpoints")
    parser.add_argument("--max-symbols", type=int, default=None)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    con = db.connect()
    db.init_schema(con)
    summary: dict = {}
    try:
        pr_res = nse_mod.sync_nse_pr_mcap(con)
        summary["bulk_pr_mcap"] = pr_res
        if args.per_symbol or pr_res.get("status") != "ok":
            summary["shp_batch"] = sync_shp_batch(
                con,
                universe=args.universe,
                resume=not args.no_resume,
                max_symbols=args.max_symbols,
            )
    except KeyboardInterrupt:
        print("\nInterrupted by user; checkpoint saved in ingest_progress. Re-run to resume.", file=sys.stderr)
        return 130
    finally:
        con.close()

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
