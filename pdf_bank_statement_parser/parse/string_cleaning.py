"""Utilities for cleaning dirty strings"""

from decimal import Decimal
from typing import Optional


def clean_fnb_currency_string(raw_str: Optional[str]) -> Decimal:
    """Converts a raw currency amount string extracted from a FNB
    bank statement into a clean Decimal representation

    Examples:
        >>> clean_fnb_currency_string(" 80,085.69Cr ")
        Decimal('80085.69')
        >>> clean_fnb_currency_string("420.69")
        Decimal('-420.69')
    """
    if raw_str is None:
        return Decimal("0.00")
    clean_str = raw_str.replace(",", "").replace(" ", "")
    if "Cr" in clean_str:
        clean_str = clean_str.replace("Cr", "")
    else:
        clean_str = f"-{clean_str}"
    return Decimal(clean_str)
