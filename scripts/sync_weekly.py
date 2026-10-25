#!/usr/bin/env python3
"""Weekly ingestion: inbox manual imports first, then masters/index/AMFI/FBIL refresh."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root on path for direct runs


from app import db
from ingest import sources


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    con = db.connect()
    try:
        res = sources.run_weekly(con)
        for k, v in res.items():
            print(f"{k}: {v if not isinstance(v, (list, dict)) else (v if isinstance(v, dict) else v)}")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
