#!/usr/bin/env python3
"""Process the manual-import drop zone (data/inbox/) only; used by `make synkinbox`."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root on path for direct runs


from app import db
from ingest.inbox import process_inbox


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    con = db.connect()
    try:
        for item in process_inbox(con):
            print(item)
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
