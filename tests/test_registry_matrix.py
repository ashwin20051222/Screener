"""tests/test_registry_matrix.py
Verifies single-source-of-truth parity across registry/filters.yaml,
apps/web/src/data/filters.json, DATA_PROVIDER_MATRIX.md, and docs/DATA_PROVIDER_MATRIX.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.registry.capabilities import FILTER_META_FIELDS, load_registry_filters

ROOT = Path(__file__).resolve().parents[1]


def test_all_255_filters_have_complete_capabilities():
    load_registry_filters.cache_clear()
    reg = yaml.safe_load((ROOT / "registry" / "filters.yaml").read_text(encoding="utf-8"))
    filters = reg["filters"]
    assert len(filters) == 255

    for fid, meta in filters.items():
        for field in FILTER_META_FIELDS:
            assert field in meta, f"{fid} missing capability field {field}"
        assert isinstance(meta["instrument_types"], list) and len(meta["instrument_types"]) >= 1
        assert meta["applicable_sectors"] in {"all", "financial_only", "non_financial_only"}
        assert isinstance(meta["required_tables"], list)
        assert isinstance(meta["min_history_days"], int) and meta["min_history_days"] >= 0
        assert meta["primary_source"]
        assert meta["freshness_sla"]


def test_registry_json_and_matrix_in_sync():
    reg = yaml.safe_load((ROOT / "registry" / "filters.yaml").read_text(encoding="utf-8"))
    web_doc = json.loads((ROOT / "apps" / "web" / "src" / "data" / "filters.json").read_text(encoding="utf-8"))
    assert reg["filters"].keys() == web_doc["filters"].keys()

    for fid, meta in reg["filters"].items():
        w = web_doc["filters"][fid]
        for field in FILTER_META_FIELDS:
            assert w.get(field) == meta.get(field), f"{fid}.{field} differs in filters.json"

    root_matrix = (ROOT / "DATA_PROVIDER_MATRIX.md").read_text(encoding="utf-8")
    docs_matrix = (ROOT / "docs" / "DATA_PROVIDER_MATRIX.md").read_text(encoding="utf-8")
    assert root_matrix == docs_matrix
    for fid in reg["filters"]:
        assert f"| `{fid}` |" in root_matrix


def test_specific_instrument_and_sector_capabilities():
    load_registry_filters.cache_clear()
    reg = load_registry_filters()
    assert reg["put_call_ratio"]["instrument_types"] == ["fno_equity"]
    assert reg["lot_size"]["instrument_types"] == ["fno_equity"]
    assert reg["expense_ratio"]["instrument_types"] == ["etf"]
    assert reg["tracking_error"]["min_history_days"] == 30
    assert reg["net_loans"]["applicable_sectors"] == "financial_only"
    assert reg["debt_to_equity"]["applicable_sectors"] == "non_financial_only"
    assert reg["percentage_upside"]["sync_job"] == "unavailable"
    assert reg["market_cap"]["feeds"] == "daily"
    assert reg["sma_200d"]["min_history_days"] == 200
    assert reg["5y_cagr"]["min_history_days"] == 1261

