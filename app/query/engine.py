"""app/query/engine.py
Multi-filter query engine supporting:
- Multi-filter AND combination (numeric range, enum, boolean, custom formula)
- Nulls-last sorting (ascending/descending with deterministic secondary tie-breaker)
- Pagination (default page size 20)
- Benchmark scope toggling (market vs universe)
- Dynamic sector & sub-sector counts and tertile presets
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from app.metrics.benchmarks import BenchmarkEngine
from app.metrics.parser import compile_safe_expression
from app.query.presets import (
    calculate_amfi_market_cap_categories,
    calculate_tertiles,
    compute_sector_counts,
)


class FilterCondition:
    """Represents a single filter rule applied in the query engine."""

    def __init__(
        self,
        filter_id: str,
        filter_type: str = "range",  # range | enum | boolean | custom
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allowed_values: Optional[Set[Any]] = None,
        bool_target: Optional[bool] = None,
        custom_expression: Optional[str] = None,
    ):
        self.filter_id = filter_id
        self.filter_type = filter_type
        self.min_val = min_val
        self.max_val = max_val
        self.allowed_values = allowed_values
        self.bool_target = bool_target
        self.custom_expression = custom_expression
        self._custom_evaluator: Optional[Callable[[Dict[str, Any]], Optional[float]]] = None

        if self.filter_type == "custom" and self.custom_expression:
            fn, err, _ = compile_safe_expression(self.custom_expression)
            if err:
                raise ValueError(f"Custom filter compilation error: {err}")
            self._custom_evaluator = fn

    def matches(self, row: Dict[str, Any]) -> bool:
        """Evaluates whether the row satisfies this filter condition."""
        if self.filter_type == "range":
            val = row.get(self.filter_id)
            if val is None or not isinstance(val, (int, float)) or math.isnan(val):
                return False
            f_val = float(val)
            if self.min_val is not None and f_val < self.min_val:
                return False
            if self.max_val is not None and f_val > self.max_val:
                return False
            return True

        elif self.filter_type == "enum":
            val = row.get(self.filter_id)
            if self.allowed_values is None or len(self.allowed_values) == 0:
                return True
            return val in self.allowed_values

        elif self.filter_type == "boolean":
            val = row.get(self.filter_id)
            return bool(val) == bool(self.bool_target)

        elif self.filter_type == "custom":
            if not self._custom_evaluator:
                return False
            eval_val = self._custom_evaluator(row)
            if eval_val is None:
                return False
            if self.min_val is not None and eval_val < self.min_val:
                return False
            if self.max_val is not None and eval_val > self.max_val:
                return False
            return True

        return True


class QueryEngine:
    """Core screening engine for filtering, benchmark enrichment, sorting, and pagination."""

    def __init__(self, benchmark_scope: str = "market"):
        self.benchmark_scope = benchmark_scope
        self.benchmark_engine = BenchmarkEngine(default_scope=benchmark_scope)

    def execute_query(
        self,
        market_universe: Sequence[Dict[str, Any]],
        active_universe: Optional[Sequence[Dict[str, Any]]] = None,
        filters: Optional[Sequence[FilterCondition]] = None,
        sort_by: str = "market_cap",
        sort_asc: bool = False,
        page: int = 1,
        page_size: int = 20,
        benchmark_scope_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes full screener query pipeline."""
        scope = benchmark_scope_override or self.benchmark_scope
        base_rows = active_universe if active_universe is not None else market_universe

        # 1. Compute benchmarks according to configured scope
        benchmark_source = market_universe if scope == "market" else base_rows
        sector_benchmarks = self.benchmark_engine.compute_benchmarks(benchmark_source, group_key="sector")
        subsector_benchmarks = self.benchmark_engine.compute_benchmarks(benchmark_source, group_key="sub_sector")

        # 2. Enrich base rows with sector and sub-sector benchmark derived metrics
        enriched_rows = [
            self.benchmark_engine.enrich_stock_with_benchmarks(r, sector_benchmarks, subsector_benchmarks)
            for r in base_rows
        ]

        # 3. Apply Multi-Filter AND combination
        filter_rules = filters or []
        filtered_rows = []
        for row in enriched_rows:
            satisfies_all = True
            for rule in filter_rules:
                if not rule.matches(row):
                    satisfies_all = False
                    break
            if satisfies_all:
                filtered_rows.append(row)

        # 4. Compute dynamic sector counts and active universe presets
        sector_counts = compute_sector_counts(filtered_rows)
        mc_categories = calculate_amfi_market_cap_categories(filtered_rows)

        # 5. Sort with NULLS LAST guarantee
        def sort_key(item: Dict[str, Any]) -> Tuple[int, Any, float]:
            val = item.get(sort_by)
            is_null = 1 if (val is None or (isinstance(val, float) and math.isnan(val))) else 0
            # Tie breaker: market_cap descending, or name ascending
            mc = float(item.get("market_cap") or 0.0)
            if is_null:
                return (1, 0, -mc)
            val_comp = -val if (sort_asc and isinstance(val, (int, float))) else val
            return (0, val_comp, -mc)

        # In Python sort:
        # For sort_asc: non-null sorted low to high, nulls at end
        # For sort_desc: non-null sorted high to low, nulls at end
        def nulls_last_comparator(item: Dict[str, Any]):
            val = item.get(sort_by)
            is_null = val is None or (isinstance(val, float) and math.isnan(val))
            mc = float(item.get("market_cap") or 0.0)
            if is_null:
                return (1, 0, -mc)
            # Nulls come last (flag 0)
            if not sort_asc:
                # Descending order: invert numeric value
                num_comp = -float(val) if isinstance(val, (int, float)) else str(val)
                return (0, num_comp, -mc)
            else:
                num_comp = float(val) if isinstance(val, (int, float)) else str(val)
                return (0, num_comp, -mc)

        sorted_rows = sorted(filtered_rows, key=nulls_last_comparator)

        # 6. Pagination
        total_count = len(sorted_rows)
        effective_page_size = max(1, page_size)
        total_pages = max(1, math.ceil(total_count / float(effective_page_size)))
        current_page = max(1, min(page, total_pages))

        start_idx = (current_page - 1) * effective_page_size
        end_idx = start_idx + effective_page_size
        page_items = sorted_rows[start_idx:end_idx]

        return {
            "total_count": total_count,
            "total_pages": total_pages,
            "page": current_page,
            "page_size": effective_page_size,
            "items": page_items,
            "sector_counts": sector_counts,
            "market_cap_categories": mc_categories,
            "benchmark_scope": scope,
        }
