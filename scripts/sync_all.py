#!/usr/bin/env python3
"""Full resumable official-data pipeline runner (`make sync-all`).

Order:
  1. weekly masters, index lists, AMFI/FBIL, total-market sector map
  2. daily latest bhavcopies + corp actions + PR shares
  3. historical bhavcopy backfill + adjusted technicals (`--days`, `--fo-days`)
  4. targeted Market Cap / SHP shares sync (`--universe`)
  5. targeted 3Q SHP + 6Y/4Q Ind-AS XBRL sync (`--universe`, `--max`)
  6. 6-month bulk/block deals + SEBI PIT insider trades (`--deal-days`)
  7. precomputed `screener_snapshot` + live coverage report (`docs/DATA_COVERAGE.md`)

Stops polite NSE fetching immediately on HTTP 403/429 while still rebuilding the
snapshot & coverage report for all data collected so far. Safe to Ctrl+C resume.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from app.query.snapshot import build_screener_snapshot  # noqa: E402
from ingest import backfill, ownership, sources  # noqa: E402
from scripts.coverage import compute_coverage_report, render_markdown  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="End-to-end resumable ScreenerDesk data sync pipeline.")
    parser.add_argument("--universe", default="nifty100", choices=["nifty100", "nifty500", "all"])
    parser.add_argument("--days", type=int, default=400, help="Historical CM trading days to backfill")
    parser.add_argument("--fo-days", type=int, default=10, help="Recent F&O days to backfill")
    parser.add_argument("--deal-days", type=int, default=183, help="SEBI PIT lookback days")
    parser.add_argument("--max", type=int, default=None, help="Optional max symbols for quarterly XBRL pass")
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing ingest_progress checkpoints")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    t0 = time.time()
    resume = not args.no_resume
    summary: Dict[str, Any] = {"universe": args.universe, "blocked": False, "steps": {}}

    con = db.connect()
    db.init_schema(con)
    try:
        steps = [
            ("weekly", lambda: sources.run_weekly(con)),
            ("daily", lambda: sources.run_daily(con)),
            ("backfill", lambda: backfill.backfill_prices(
                con, trading_days=args.days, fo_days=args.fo_days, resume=resume
            )),
            ("shp", lambda: ownership.sync_shp_batch(con, universe=args.universe, resume=resume)),
            ("quarterly", lambda: sources.run_quarterly(
                con, universe=args.universe, max_symbols=args.max, resume=resume
            )),
            ("deals", lambda: ownership.sync_deals_and_pit(con, days_back=args.deal_days)),
        ]
        for step_name, fn in steps:
            st0 = time.time()
            res = fn()
            elapsed = round(time.time() - st0, 2)
            summary["steps"][step_name] = res
            blocked = bool(isinstance(res, dict) and res.get("blocked"))
            print(
                f"[sync-all] {step_name}: status={res.get('status', 'ok') if isinstance(res, dict) else 'ok'} "
                f"blocked={blocked} ({elapsed}s)",
                flush=True,
            )
            if blocked:
                summary["blocked"] = True
                print(
                    f"[sync-all] stopped network steps at `{step_name}` due to 403/429/network control; "
                    f"re-run `make sync-all` later to resume or use data/inbox/.",
                    flush=True,
                )
                break

        snap = build_screener_snapshot(con)
        summary["steps"]["snapshot"] = snap
        print(
            f"[sync-all] snapshot: rows={snap.get('row_count')} synced={snap.get('synced')} etag={snap.get('etag')}",
            flush=True,
        )
    except KeyboardInterrupt:
        print("\n[sync-all] Interrupted by user; rebuilding snapshot for progress saved so far...", file=sys.stderr)
        build_screener_snapshot(con)
        return 130
    finally:
        con.close()

    rep = compute_coverage_report()
    (ROOT / "docs" / "DATA_COVERAGE.md").write_text(render_markdown(rep), encoding="utf-8")
    summary["elapsed_seconds"] = round(time.time() - t0, 2)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
