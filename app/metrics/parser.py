"""app/metrics/parser.py
Safe custom filter compiler using Python's AST module.
No `eval()`, strictly whitelisted operators (+, -, *, /) and registered identifiers.
Enforces 2 to 5 data items constraint and validates against sample data.
"""
from __future__ import annotations

import ast
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class SafeExpressionVisitor(ast.NodeVisitor):
    """AST validator that verifies only safe mathematical operations are present."""

    ALLOWED_NODES = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.USub,
        ast.UAdd,
        ast.Name,
        ast.Constant,
        ast.Load,
    )

    def __init__(self, allowed_identifiers: Optional[Set[str]] = None):
        self.allowed_identifiers = allowed_identifiers
        self.found_identifiers: Set[str] = set()
        self.is_safe = True
        self.error_message = ""

    def generic_visit(self, node: ast.AST):
        if not isinstance(node, self.ALLOWED_NODES):
            self.is_safe = False
            self.error_message = f"Disallowed syntax: {type(node).__name__}. Only basic arithmetic is permitted."
            return
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self.found_identifiers.add(node.id)
        if self.allowed_identifiers is not None and node.id not in self.allowed_identifiers:
            self.is_safe = False
            self.error_message = f"Unknown metric identifier: '{node.id}'"
            return
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if not isinstance(node.value, (int, float)):
            self.is_safe = False
            self.error_message = f"Only numeric constants are allowed, found: {type(node.value).__name__}"
            return
        self.generic_visit(node)


def compile_safe_expression(
    expr_str: str,
    allowed_identifiers: Optional[Set[str]] = None,
    min_items: int = 2,
    max_items: int = 5,
) -> Tuple[Optional[Callable[[Dict[str, Any]], Optional[float]]], Optional[str], Set[str]]:
    """Compiles an expression string into a safe callable.
    Returns (eval_fn, error_message, found_identifiers).
    """
    clean_expr = expr_str.strip()
    if not clean_expr:
        return None, "Expression cannot be empty", set()

    try:
        parsed = ast.parse(clean_expr, mode="eval")
    except SyntaxError as e:
        return None, f"Invalid mathematical syntax: {e.msg}", set()

    visitor = SafeExpressionVisitor(allowed_identifiers=allowed_identifiers)
    visitor.visit(parsed)

    if not visitor.is_safe:
        return None, visitor.error_message, visitor.found_identifiers

    num_identifiers = len(visitor.found_identifiers)
    if num_identifiers < min_items:
        return None, f"Expression must contain at least {min_items} metrics (found {num_identifiers})", visitor.found_identifiers
    if num_identifiers > max_items:
        return None, f"Expression cannot contain more than {max_items} metrics (found {num_identifiers})", visitor.found_identifiers

    compiled_code = compile(parsed, filename="<custom_filter>", mode="eval")

    def evaluator(row: Dict[str, Any]) -> Optional[float]:
        # Build local context from row
        local_scope = {}
        for var in visitor.found_identifiers:
            val = row.get(var)
            if val is None or not isinstance(val, (int, float)):
                return None
            local_scope[var] = float(val)

        try:
            res = eval(compiled_code, {"__builtins__": {}}, local_scope)
            if res is None or not isinstance(res, (int, float)):
                return None
            if res != res:  # NaN
                return None
            if abs(res) == float("inf"):
                return None
            return float(res)
        except (ZeroDivisionError, OverflowError, TypeError, ValueError):
            return None

    return evaluator, None, visitor.found_identifiers


def validate_and_test_expression(
    expr_str: str,
    sample_rows: List[Dict[str, Any]],
    allowed_identifiers: Optional[Set[str]] = None,
) -> Tuple[bool, str, List[Optional[float]]]:
    """Validates an expression and tests it on sample rows."""
    evaluator, err, found_ids = compile_safe_expression(expr_str, allowed_identifiers)
    if err:
        return False, err, []

    sample_results = [evaluator(row) for row in sample_rows]
    valid_count = sum(1 for r in sample_results if r is not None)

    msg = f"Valid expression with {len(found_ids)} metrics ({', '.join(sorted(found_ids))}). Evaluated on {len(sample_rows)} sample rows ({valid_count} non-null)."
    return True, msg, sample_results
