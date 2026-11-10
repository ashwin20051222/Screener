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

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.metrics.parser import compile_safe_expression, validate_and_test_expression
from app.query.engine import FilterCondition, QueryEngine
from app.config import settings
from app.universe.importer import (
    auto_detect_identifier_column,
    generate_template_headers,
    get_workbook_sheet_names,
    identify_custom_columns,
    parse_spreadsheet_data,
)
from app.universe.master import SecurityMasterIndex
from app.universe.matcher import UniverseMatcher
from app.universe.pnl import compute_row_pnl

router = APIRouter(prefix="/api", tags=["screener"])

_GLOBAL_MASTER = SecurityMasterIndex()
_GLOBAL_MATCHER = UniverseMatcher(_GLOBAL_MASTER)

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


class MatchUniverseRequest(BaseModel):
    rows: List[Dict[str, Any]]
    id_column: Optional[str] = None
    compute_pnl: bool = True


@router.post("/universe/upload-file")
async def upload_universe_file(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
):
    """Parses uploaded .xlsx/.xls/.csv file, returns sheet names, headers, auto-detected ID column, and parsed rows."""
    contents = await file.read()
    filename = file.filename or "upload.xlsx"

    sheet_names = get_workbook_sheet_names(contents, filename)
    selected_sheet = sheet_name if sheet_name in sheet_names else sheet_names[0]

    rows, headers, id_col, custom_cols = parse_spreadsheet_data(
        contents,
        filename=filename,
        sheet_name=selected_sheet,
    )

    return {
        "filename": filename,
        "sheet_names": sheet_names,
        "selected_sheet": selected_sheet,
        "headers": headers,
        "auto_detected_id_column": id_col,
        "detected_custom_columns": custom_cols,
        "total_rows": len(rows),
        "rows": rows,
    }


@router.post("/universe/match")
def match_universe(req: MatchUniverseRequest):
    """Executes 5-tier matching cascade on provided rows and optionally computes portfolio P&L."""
    report = _GLOBAL_MATCHER.match_all(req.rows, id_col=req.id_column)

    if req.compute_pnl:
        # Enrich matched rows with P&L if quantity & buy_price exist
        for m in report["matched"]:
            sec = m.get("matched_security") or {}
            raw = m.get("raw_input") or {}
            close_px = sec.get("close_price")
            pnl_info = compute_row_pnl(raw, close_price=close_px)
            m["pnl"] = pnl_info

    return report


@router.get("/universe/template")
def get_universe_template():
    """Returns standard header template for user spreadsheets."""
    return {"template_headers": generate_template_headers()}


@router.get("/scores/weights")
def get_scores_weights():
    """Returns open-approximation quant score weights & formulas from config/scores.yaml."""
    from app.metrics.scores import scores_config
    return scores_config()


@router.get("/universes")
def get_universes():
    """Returns canonical index universe metadata from latest ref_index_constituent snapshot + All listed."""
    from app.query.db_store import get_universes_summary
    return get_universes_summary()


from fastapi import Request, Response


@router.get("/screener/dataset")
def get_screener_dataset(
    universe: Optional[str] = None,
    fields: Optional[str] = None,
    request: Request = None,
    response: Response = None,
):
    """Serves precomputed DuckDB screener snapshot with ETag/304, ?universe=, and ?fields=."""
    from app.query.snapshot import load_snapshot_from_db

    data = load_snapshot_from_db(universe=universe, fields=fields)
    etag = data.get("etag")
    if etag and request is not None:
        inm = request.headers.get("if-none-match")
        if inm and ("*" in inm or etag in {t.strip() for t in inm.split(",")}):
            return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "public, max-age=5"})
    if etag and response is not None:
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=5, stale-while-revalidate=60"
    return data


class ScoresComputeRequest(BaseModel):
    stocks: List[Dict[str, Any]]


@router.post("/scores/compute")
def compute_scores_endpoint(req: ScoresComputeRequest):
    """Computes open-approximation quant scores for supplied market rows."""
    from app.metrics.scores import compute_all_quant_scores, scores_config
    return {
        "badge": scores_config().get("badge", "Approximate - computed locally"),
        "scores": compute_all_quant_scores(req.stocks),
    }


class EnsureFiltersRequest(BaseModel):
    filter_ids: List[str] = Field(default_factory=list)
    universe: Optional[str] = None


@router.post("/data/ensure")
def post_ensure_data(req: EnsureFiltersRequest):
    """Checks capability/coverage for checked filters, computes derived metrics or queues background sync."""
    from app.jobs.ensure_manager import ensure_filters
    return ensure_filters(req.filter_ids, universe=req.universe)


@router.get("/data/jobs")
def get_data_jobs(limit: int = 20):
    """Lists recent and active background data synchronization jobs."""
    from app.jobs.ensure_manager import list_jobs
    return {"jobs": list_jobs(limit=limit)}


@router.get("/data/jobs/{job_id}")
def get_data_job_status(job_id: str):
    """Returns persistent status/progress of a background filter sync job."""
    from app.jobs.ensure_manager import get_job
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.get("/coverage")
def get_coverage(universe: Optional[str] = None, response: Response = None):
    """Returns eligibility-aware non-null coverage, status pills, and provider SLA across all 255 filters."""
    from scripts.coverage import compute_coverage_report
    rep = compute_coverage_report(universe=universe)
    if response is not None:
        response.headers["Cache-Control"] = "no-store"
    return rep


@router.post("/data/rebuild")
def post_data_rebuild():
    """Recomputes technicals, F&O metrics, cached XBRLs, ETF tracking errors, and rebuilds snapshot atomically."""
    from app.jobs.ensure_manager import rebuild_all
    return rebuild_all()


@router.get("/providers")
def get_providers():
    """Returns honest runtime health, cadence, and configuration state for all market-data providers."""
    from app.providers.registry import get_provider_status_summary
    return get_provider_status_summary()

