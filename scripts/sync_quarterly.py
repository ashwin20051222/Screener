#!/usr/bin/env python3
"""Targeted, resumable quarterly sync (3 SHP quarters + 6 annual / 4 quarterly XBRL filings)."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from ingest import sources  # noqa: E402
from scripts.coverage import compute_coverage_report, render_markdown  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Targeted resumable SHP + Ind-AS XBRL quarterly sync.")
    parser.add_argument("--universe", default="nifty100", choices=["nifty100", "nifty500", "all"])
    parser.add_argument("--max", type=int, default=None, help="Optional cap on symbols processed")
    parser.add_argument("--no-resume", action="store_true", help="Ignore prior ingest_progress checkpoints")
    parser.add_argument("--no-coverage", action="store_true", help="Skip regenerating docs/DATA_COVERAGE.md")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    con = db.connect()
    db.init_schema(con)
    try:
        res = sources.run_quarterly(
            con,
            universe=args.universe,
            max_symbols=args.max,
            resume=not args.no_resume,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user; quarterly checkpoints saved in ingest_progress. Re-run to resume.", file=sys.stderr)
        return 130
    finally:
        con.close()

    if not args.no_coverage:
        rep = compute_coverage_report()
        (ROOT / "docs" / "DATA_COVERAGE.md").write_text(render_markdown(rep), encoding="utf-8")

    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
