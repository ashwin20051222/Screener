#!/usr/bin/env python3
"""Materialize precomputed full-market screener snapshot inside DuckDB (`screener_snapshot`)."""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.query.snapshot import build_screener_snapshot  # noqa: E402


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    t0 = time.time()
    res = build_screener_snapshot()
    res["elapsed_seconds"] = round(time.time() - t0, 3)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
