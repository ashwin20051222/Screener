#!/usr/bin/env python3
"""Print a data-status report and quick table stats (used by humans + tests + UI later)."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root on path for direct runs


from app import db
from ingest import sources


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.WARNING)
    con = db.connect()
    try:
        rep = sources.status_report(con)
        print(json.dumps(rep, indent=2))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
