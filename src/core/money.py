"""Financial precision utilities enforcing Python's Decimal for monetary handling."""

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

# Standard currency quantization to 2 decimal places
CENTS_UNIT = Decimal("0.01")


def to_decimal(value: str | int | float | Decimal) -> Decimal:
    """Safely convert numerical inputs to Decimal without floating-point drift.

    Float inputs are converted to strings first to prevent binary representation noise.
    """
    if isinstance(value, Decimal):
        return value.quantize(CENTS_UNIT, rounding=ROUND_HALF_EVEN)

    try:
        # String conversion preserves literal decimal representation
        str_val = str(value).strip()
        dec = Decimal(str_val)
        return dec.quantize(CENTS_UNIT, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, ValueError) as err:
        raise ValueError(f"Cannot convert '{value}' to valid financial Decimal") from err


def format_currency(value: Decimal | str | int | float, currency_symbol: str = "₹") -> str:
    """Format monetary decimal to formatted string (e.g. '₹1,250.50')."""
    dec = to_decimal(value)
    sign = "-" if dec < 0 else ""
    abs_dec = abs(dec)
    return f"{sign}{currency_symbol}{abs_dec:,.2f}"
