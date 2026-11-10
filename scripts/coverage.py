#!/usr/bin/env python3
"""Measure non-null data coverage across all 255 filters in registry/filters.yaml.

Outputs a readable report to stdout and saves it to docs/DATA_COVERAGE.md.
Reports coverage over (a) all listed rows in DuckDB and (b) NIFTY100 rows, plus feeding job (`feeds`).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.query.snapshot import load_snapshot_from_db  # noqa: E402


def _pct(count: int, total: int) -> float:
    return round((count / total) * 100.0, 1) if total > 0 else 0.0


def compute_coverage_report(dataset: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Computes per-filter non-null coverage against a market dataset dict."""
    with open(ROOT / "registry" / "filters.yaml", "r", encoding="utf-8") as fh:
        reg = yaml.safe_load(fh) or {}
    filters: Dict[str, Dict[str, Any]] = reg.get("filters", {})

    if dataset is None:
        dataset = load_snapshot_from_db()

    all_rows: List[Dict[str, Any]] = dataset.get("rows") or []
    universes: Dict[str, List[str]] = dataset.get("universes") or {}
    nifty100_syms = set(universes.get("NIFTY100") or [])
    nifty100_rows = [r for r in all_rows if (r.get("nse_symbol") or "") in nifty100_syms]

    n_all = len(all_rows)
    n_100 = len(nifty100_rows)

    entries: List[Dict[str, Any]] = []
    by_feed: Dict[str, Dict[str, int]] = {}
    for fid, fdef in filters.items():
        cnt_all = sum(1 for r in all_rows if r.get(fid) is not None)
        cnt_100 = sum(1 for r in nifty100_rows if r.get(fid) is not None)
        feed = str(fdef.get("feeds") or "unknown")
        by_feed.setdefault(feed, {"filters": 0, "populated_any": 0})
        by_feed[feed]["filters"] += 1
        if cnt_all > 0:
            by_feed[feed]["populated_any"] += 1

        entries.append({
            "id": fid,
            "name": str(fdef.get("name") or fid),
            "category": str(fdef.get("category") or ""),
            "availability": str(fdef.get("availability") or ""),
            "feeds": feed,
            "all_non_null": cnt_all,
            "all_pct": _pct(cnt_all, n_all),
            "nifty100_non_null": cnt_100,
            "nifty100_pct": _pct(cnt_100, n_100),
        })

    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "synced": bool(dataset.get("synced")),
        "total_rows": n_all,
        "nifty100_rows": n_100,
        "universes": {k: len(v) for k, v in sorted(universes.items())},
        "by_feed": dict(sorted(by_feed.items())),
        "filters": entries,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    """Formats the coverage report as Markdown for docs/DATA_COVERAGE.md."""
    lines: List[str] = [
        "# DATA_COVERAGE.md — Live Database Filter Coverage",
        "",
        f"> **Generated:** `{report['generated_at']}`",
        f"> **Database Synced:** `{report['synced']}` | **All Listed Rows:** `{report['total_rows']}` | **NIFTY100 Rows:** `{report['nifty100_rows']}`",
        f"> **Registry Filters Checked:** `{len(report['filters'])}`",
        "",
        "## 1. Index Universes Loaded",
        "",
    ]
    if report["universes"]:
        lines.append("| Index Slug | Member Count |")
        lines.append("|---|---|")
        for idx_name, cnt in report["universes"].items():
            lines.append(f"| `{idx_name}` | {cnt} |")
    else:
        lines.append("_No index universes loaded yet (`ref_index_constituent` is empty). Run `make sync-weekly`._")

    lines.extend([
        "",
        "## 2. Coverage Summary by Feeding Job (`feeds`)",
        "",
        "| Feeds Job | Filter Count | Filters With >= 1 Value |",
        "|---|---|---|",
    ])
    for feed, stats in report["by_feed"].items():
        lines.append(f"| `{feed}` | {stats['filters']} | {stats['populated_any']} |")

    lines.extend([
        "",
        "## 3. Per-Filter Non-Null Coverage",
        "",
        "| Filter ID | Name | Category | Availability | Feeds | All Non-Null | All % | NIFTY100 Non-Null | NIFTY100 % |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for e in report["filters"]:
        lines.append(
            f"| `{e['id']}` | {e['name']} | {e['category']} | {e['availability']} | `{e['feeds']}` | "
            f"{e['all_non_null']} | {e['all_pct']:.1f}% | {e['nifty100_non_null']} | {e['nifty100_pct']:.1f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Measure per-filter data coverage in DuckDB.")
    parser.add_argument("--out", default=str(ROOT / "docs" / "DATA_COVERAGE.md"), help="Markdown output path")
    parser.add_argument("--no-write", action="store_true", help="Print summary only without writing Markdown file")
    args = parser.parse_args(argv)

    rep = compute_coverage_report()
    md = render_markdown(rep)
    if not args.no_write:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md, encoding="utf-8")

    try:
        print(f"Synced: {rep['synced']} | All rows: {rep['total_rows']} | NIFTY100 rows: {rep['nifty100_rows']}")
        print(f"{'Filter ID':38s} {'Feeds':11s} {'All':>12s} {'NIFTY100':>12s}")
        print("-" * 77)
        for e in rep["filters"]:
            all_col = f"{e['all_non_null']} ({e['all_pct']:.1f}%)"
            n100_col = f"{e['nifty100_non_null']} ({e['nifty100_pct']:.1f}%)"
            print(f"{e['id']:38s} {e['feeds']:11s} {all_col:>12s} {n100_col:>12s}")
        if not args.no_write:
            print(f"\nSaved coverage report to {args.out}")
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
