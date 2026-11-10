#!/usr/bin/env python3
"""Single-source-of-truth registry synchronizer and provider matrix generator.

Reads `registry/filters.yaml`, resolves canonical operational metadata for all
255 filters via `app.registry.capabilities`, writes back clean `registry/filters.yaml`,
syncs `apps/web/src/data/filters.json`, and generates `DATA_PROVIDER_MATRIX.md`
(plus `docs/DATA_PROVIDER_MATRIX.md`).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.registry.capabilities import FILTER_META_FIELDS, resolve_filter_capabilities  # noqa: E402

REGISTRY_PATH = ROOT / "registry" / "filters.yaml"
WEB_JSON_PATH = ROOT / "apps" / "web" / "src" / "data" / "filters.json"
ROOT_MATRIX_PATH = ROOT / "DATA_PROVIDER_MATRIX.md"
DOCS_MATRIX_PATH = ROOT / "docs" / "DATA_PROVIDER_MATRIX.md"

_CORE_KEY_ORDER = [
    "name",
    "category",
    "sub_category",
    "unit",
    "kind",
    "default_min",
    "default_max",
    "step",
    "availability",
    *FILTER_META_FIELDS,
    "formula",
    "inputs",
    "null_rule",
    "direction_of_goodness",
    "glossary",
]


def _order_filter_dict(fdef: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for k in _CORE_KEY_ORDER:
        if k in fdef:
            ordered[k] = fdef[k]
    for k, v in fdef.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


def sync_all(*, check_only: bool = False) -> Dict[str, Any]:
    doc = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    filters: Dict[str, Dict[str, Any]] = doc.get("filters") or {}

    enriched: Dict[str, Dict[str, Any]] = {}
    for fid, raw in filters.items():
        merged = dict(raw)
        caps = resolve_filter_capabilities(fid, merged)
        merged.update(caps)
        enriched[fid] = _order_filter_dict(merged)

    new_doc = {"version": str(doc.get("version") or "2.0"), "filters": enriched}
    yaml_text = yaml.safe_dump(new_doc, sort_keys=False, allow_unicode=True, width=140)
    json_payload = {"version": new_doc["version"], "filters": enriched}
    json_text = json.dumps(json_payload, indent=2, ensure_ascii=False) + "\n"
    matrix_md = render_provider_matrix(enriched)

    if check_only:
        cur_json = WEB_JSON_PATH.read_text(encoding="utf-8") if WEB_JSON_PATH.exists() else ""
        cur_root_matrix = ROOT_MATRIX_PATH.read_text(encoding="utf-8") if ROOT_MATRIX_PATH.exists() else ""
        return {
            "count": len(enriched),
            "yaml_in_sync": REGISTRY_PATH.read_text(encoding="utf-8") == yaml_text,
            "json_in_sync": cur_json == json_text,
            "matrix_in_sync": cur_root_matrix == matrix_md,
        }

    REGISTRY_PATH.write_text(yaml_text, encoding="utf-8")
    WEB_JSON_PATH.write_text(json_text, encoding="utf-8")
    ROOT_MATRIX_PATH.write_text(matrix_md, encoding="utf-8")
    DOCS_MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_MATRIX_PATH.write_text(matrix_md, encoding="utf-8")
    return {"count": len(enriched), "synced": True}


def render_provider_matrix(filters: Dict[str, Dict[str, Any]]) -> str:
    feed_counts = Counter(str(f.get("feeds") or "unavailable") for f in filters.values())
    job_counts = Counter(str(f.get("sync_job") or "unavailable") for f in filters.values())
    avail_counts = Counter(str(f.get("availability") or "Unknown") for f in filters.values())

    lines: List[str] = [
        "# DATA_PROVIDER_MATRIX.md — Authoritative Filter Capability & Source Matrix",
        "",
        f"> Generated automatically from `registry/filters.yaml` (`{len(filters)}` filters) via `scripts/sync_registry.py`.",
        "> Never invent data or fabricate values for unavailable fields. Delayed/EOD feeds are explicitly distinguished from real-time quotes.",
        "",
        "## 1. Summary by Feed, Availability, and Sync Job",
        "",
        "| Feed | Count | Sync Job Breakdown |",
        "|---|---:|---|",
    ]
    for feed, cnt in sorted(feed_counts.items()):
        jobs = Counter(
            str(f.get("sync_job") or "")
            for f in filters.values()
            if str(f.get("feeds") or "unavailable") == feed
        )
        job_str = ", ".join(f"`{j}` ({c})" for j, c in sorted(jobs.items()))
        lines.append(f"| `{feed}` | {cnt} | {job_str} |")

    lines.extend([
        "",
        "| Availability Classification | Count |",
        "|---|---:|",
    ])
    for av, cnt in sorted(avail_counts.items()):
        lines.append(f"| {av} | {cnt} |")

    lines.extend([
        "",
        "| Sync Job (`sync_job`) | Filter Count |",
        "|---|---:|",
    ])
    for job, cnt in sorted(job_counts.items()):
        lines.append(f"| `{job}` | {cnt} |")

    lines.extend([
        "",
        "## 2. All 255 Filters — Exact Source, Table, Calculation & Freshness Matrix",
        "",
        "| Filter ID | Name | Category | Instruments | Sector Scope | Feed | Sync Job | Primary Source | Backup Source | Required Tables | Calculation Function | Lookback | Min Days | Refresh Cadence | Freshness SLA |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|",
    ])

    def _esc(val: Any) -> str:
        return str(val or "").replace("|", "\\|").replace("\n", " ").strip()

    for fid, f in filters.items():
        inst = ", ".join(f.get("instrument_types") or [])
        tables = ", ".join(f.get("required_tables") or []) or "—"
        lines.append(
            f"| `{fid}` | {_esc(f.get('name'))} | {_esc(f.get('category'))} | `{inst}` | "
            f"`{_esc(f.get('applicable_sectors'))}` | `{_esc(f.get('feeds'))}` | `{_esc(f.get('sync_job'))}` | "
            f"{_esc(f.get('primary_source'))} | {_esc(f.get('backup_source'))} | `{tables}` | "
            f"`{_esc(f.get('calculation_function'))}` | {_esc(f.get('lookback_periods'))} | "
            f"{int(f.get('min_history_days') or 0)} | {_esc(f.get('refresh_cadence'))} | {_esc(f.get('freshness_sla'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync registry/filters.yaml, filters.json, and DATA_PROVIDER_MATRIX.md.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any generated file is out of sync.")
    args = parser.parse_args(argv)
    res = sync_all(check_only=args.check)
    print(json.dumps(res, indent=2))
    if args.check:
        ok = bool(res.get("yaml_in_sync") and res.get("json_in_sync") and res.get("matrix_in_sync"))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

