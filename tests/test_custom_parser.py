"""tests/test_custom_parser.py
Unit tests for the safe AST custom filter expression compiler.
Ensures malicious syntax is rejected, valid math compiles, and nulls/zero divisions are handled cleanly.
"""
import pytest

from app.metrics.parser import compile_safe_expression, validate_and_test_expression


ALLOWED_METRICS = {"pe_ratio", "pb_ratio", "ps_ratio", "dividend_yield", "roe", "market_cap"}


def test_valid_custom_expression():
    """Valid arithmetic expression with 2 to 5 identifiers compiles and evaluates."""
    expr = "(pe_ratio + pb_ratio) / 2.0"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS)
    assert err is None
    assert ids == {"pe_ratio", "pb_ratio"}
    assert evaluator is not None

    sample_row = {"pe_ratio": 20.0, "pb_ratio": 4.0}
    result = evaluator(sample_row)
    assert result == 12.0


def test_custom_expression_three_metrics():
    """Test expression with 3 metrics: market_cap / (pe_ratio * pb_ratio)."""
    expr = "market_cap / (pe_ratio * pb_ratio)"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS)
    assert err is None
    assert len(ids) == 3
    assert evaluator is not None

    sample_row = {"market_cap": 1000.0, "pe_ratio": 10.0, "pb_ratio": 2.0}
    assert evaluator(sample_row) == 50.0


def test_reject_too_few_metrics():
    """Expressions with fewer than 2 metrics must be rejected."""
    expr = "pe_ratio * 1.5"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS, min_items=2)
    assert evaluator is None
    assert "at least 2 metrics" in err


def test_reject_too_many_metrics():
    """Expressions with more than 5 metrics must be rejected."""
    expr = "pe_ratio + pb_ratio + ps_ratio + dividend_yield + roe + market_cap"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS, max_items=5)
    assert evaluator is None
    assert "more than 5 metrics" in err


def test_reject_unknown_metric():
    """Identifiers not in allowed metrics must be rejected."""
    expr = "pe_ratio + unknown_metric"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS)
    assert evaluator is None
    assert "Unknown metric identifier" in err


def test_reject_malicious_code_injection():
    """Code injection attempts like function calls, imports, or dunders must be rejected."""
    dangerous = [
        "__import__('os').system('ls')",
        "pe_ratio + exec('print(1)')",
        "open('/etc/passwd').read()",
        "pe_ratio.__class__.__bases__",
        "[x for x in range(10)]",
        "pe_ratio if True else pb_ratio",
    ]
    for expr in dangerous:
        evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS)
        assert evaluator is None, f"Expected {expr} to fail AST validation"
        assert err is not None


def test_safe_division_by_zero_and_missing_values():
    """Evaluator must return None rather than throwing ZeroDivisionError or KeyError."""
    expr = "pe_ratio / pb_ratio"
    evaluator, err, ids = compile_safe_expression(expr, allowed_identifiers=ALLOWED_METRICS)
    assert evaluator is not None

    # Division by zero
    assert evaluator({"pe_ratio": 10.0, "pb_ratio": 0.0}) is None
    # Missing variable
    assert evaluator({"pe_ratio": 10.0}) is None
    # None value in row
    assert evaluator({"pe_ratio": None, "pb_ratio": 2.0}) is None


def test_validate_and_test_expression_helper():
    """Test batch validation helper function against multiple sample rows."""
    expr = "pe_ratio * 2.0 - pb_ratio"
    rows = [
        {"pe_ratio": 15.0, "pb_ratio": 3.0},
        {"pe_ratio": 25.0, "pb_ratio": 5.0},
        {"pe_ratio": None, "pb_ratio": 2.0},
    ]
    is_valid, msg, results = validate_and_test_expression(expr, rows, allowed_identifiers=ALLOWED_METRICS)
    assert is_valid is True
    assert results == [27.0, 45.0, None]
