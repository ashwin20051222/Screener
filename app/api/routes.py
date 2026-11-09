"""app/api/routes.py
API endpoints for:
- /api/filters: filter registry metadata
- /api/query: execute multi-filter screening query
- /api/custom-filter/validate: validate custom filter expression
- /api/benchmarks: sector/subsector benchmarks
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import yaml

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.metrics.parser import compile_safe_expression, validate_and_test_expression
from app.query.engine import FilterCondition, QueryEngine
from app.config import settings

router = APIRouter(prefix="/api", tags=["screener"])

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "filters.yaml"


def load_registry_filters() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            return data.get("filters", {})
    return {}


class FilterRuleModel(BaseModel):
    filter_id: str
    filter_type: str = "range"  # range | enum | boolean | custom
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    bool_target: Optional[bool] = None
    custom_expression: Optional[str] = None


class ScreenerQueryRequest(BaseModel):
    active_universe: Optional[List[Dict[str, Any]]] = None
    filters: Optional[List[FilterRuleModel]] = None
    sort_by: str = "market_cap"
    sort_asc: bool = False
    page: int = 1
    page_size: int = 20
    benchmark_scope: Optional[str] = None


class CustomFilterValidateRequest(BaseModel):
    expression: str
    sample_rows: Optional[List[Dict[str, Any]]] = None


@router.get("/filters")
def get_filters():
    """Returns complete metadata for all 255 filters from the single source of truth."""
    return {"filters": load_registry_filters()}


@router.post("/query")
def query_screener(req: ScreenerQueryRequest):
    """Executes multi-filter query with sorting, pagination, and benchmark calculation."""
    reg = load_registry_filters()
    app_settings = settings()
    default_scope = app_settings.get("benchmark_scope", "market")
    scope = req.benchmark_scope or default_scope

    # Convert filter models to FilterConditions
    conditions: List[FilterCondition] = []
    if req.filters:
        for f in req.filters:
            allowed_set = set(f.allowed_values) if f.allowed_values is not None else None
            try:
                cond = FilterCondition(
                    filter_id=f.filter_id,
                    filter_type=f.filter_type,
                    min_val=f.min_val,
                    max_val=f.max_val,
                    allowed_values=allowed_set,
                    bool_target=f.bool_target,
                    custom_expression=f.custom_expression,
                )
                conditions.append(cond)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    # Base market universe: use provided active_universe or seed fallback
    base_data = req.active_universe or []
    engine = QueryEngine(benchmark_scope=scope)

    result = engine.execute_query(
        market_universe=base_data,
        active_universe=req.active_universe,
        filters=conditions,
        sort_by=req.sort_by,
        sort_asc=req.sort_asc,
        page=req.page,
        page_size=req.page_size,
        benchmark_scope_override=scope,
    )
    return result


@router.post("/custom-filter/validate")
def validate_custom_filter(req: CustomFilterValidateRequest):
    """Validates custom filter expression syntax against whitelisted AST and sample data."""
    reg = load_registry_filters()
    allowed_ids = set(reg.keys())
    sample_rows = req.sample_rows or []

    valid, msg, sample_evals = validate_and_test_expression(
        req.expression,
        sample_rows=sample_rows,
        allowed_identifiers=allowed_ids,
    )

    if not valid:
        return {"valid": False, "error": msg, "sample_evaluations": []}

    return {"valid": True, "message": msg, "sample_evaluations": sample_evals}
