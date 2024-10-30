from typing import Final

REGEX_SHORT_DATE: Final[str] = r"(\d{2})\s+([A-Z][a-z]{2})"  # matches e.g. '24 Dec'
REGEX_MONEY_NUM: Final[str] = (
    r"\b[\d,]+\.\d{2}(?:Cr)?\b"  # matches e.g. "420.69" or "80,085.69Cr"
)
IDENTIFY_TRANSACTION_ROW_REGEX: Final[str] = (
    r"^\s*"
    + REGEX_SHORT_DATE
    + r"(.*?(?!\.\d{2}(?:Cr)?\b))"  # anything not followed by cents amount e.g. '.42 ' or '.42Cr '
    + rf"({REGEX_MONEY_NUM})"
    + r"\s+"
    + rf"({REGEX_MONEY_NUM})"
    + rf"(?:\s+({REGEX_MONEY_NUM}))?\s*?$"  # optional 3rd money amount
)

MONTH_NAMES: Final[tuple[str, ...]] = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
