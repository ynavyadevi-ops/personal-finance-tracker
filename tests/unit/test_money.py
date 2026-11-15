"""Unit tests for Decimal monetary precision and formatting."""

from decimal import Decimal

import pytest

from src.core.money import format_currency, to_decimal


def test_to_decimal_exact_arithmetic() -> None:
    """Verify that to_decimal eliminates float precision inaccuracies."""
    # 0.1 + 0.2 in floating point produces 0.30000000000000004
    d1 = to_decimal(0.1)
    d2 = to_decimal(0.2)
    assert d1 + d2 == Decimal("0.30")


def test_to_decimal_string_conversion() -> None:
    """Verify string inputs convert cleanly to two decimal places."""
    assert to_decimal("150.75") == Decimal("150.75")
    assert to_decimal("150") == Decimal("150.00")
    assert to_decimal("0.001") == Decimal("0.00")


def test_to_decimal_invalid_input() -> None:
    """Verify ValueError is raised on non-numeric strings."""
    with pytest.raises(ValueError, match="Cannot convert"):
        to_decimal("invalid-money-string")


def test_format_currency() -> None:
    """Verify currency string formatting with commas and symbols."""
    assert format_currency(Decimal("1250.50")) == "$1,250.50"
    assert format_currency("5000000.00") == "$5,000,000.00"
    assert format_currency(Decimal("-50.25")) == "-$50.25"
