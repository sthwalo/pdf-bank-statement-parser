import re
from collections import namedtuple
from decimal import Decimal
from typing import Any, Final, Optional

import pdfplumber

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

Transaction = namedtuple(
    "transaction", ["date", "description", "amount", "balance", "bank_fee"]
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

with pdfplumber.open("bank_statements/FNB_ASPIRE_CURRENT_ACCOUNT_100.pdf") as pdf:
    transactions_found: list[Transaction] = []
    balances_found: dict[str, Any] = {
        "opening": {
            "regex": r"Opening Balance\s+([\d,]+\.\d{2}(?:Cr)?)\b",
            "values_found": [],
        },
        "closing": {
            "regex": r"Closing Balance\s+([\d,]+\.\d{2}(?:Cr)?)\b",
            "values_found": [],
        },
    }

    current_year: Optional[int] = None
    for page in pdf.pages:
        page_text: str = page.extract_text()
        if current_year is None:
            current_year = int(
                re.search(
                    r"Statement Period\s+:\s+\d{2}\s+[a-zA-Z]+\s+(\d{4})",
                    page_text,
                ).groups()[0]
            )
        for row in page_text.split("\n"):
            for balance_name, balance_info in balances_found.items():
                found_balance = re.search(balance_info["regex"], row)
                if found_balance:
                    balance_raw: str = found_balance.groups()[0].replace(" ", "")
                    if "Cr" not in balance_raw:
                        balance: Decimal = Decimal("-" + balance_raw.replace("Cr", ""))
                    else:
                        balance: Decimal = Decimal(
                            balance_raw.replace("Cr", "").replace(",", "")
                        )
                    balance_info["values_found"].append(balance)

            row_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX, row.strip())
            if row_match:
                raw_day, raw_month, raw_desc, raw_amt, raw_balance, raw_fee = (
                    row_match.groups()
                )

            # parsed data validation #
            for balance_name, balance_info in balances_found.items():
                assert all(
                    [
                        bal == balance_info["values_found"][0]
                        for bal in balance_info["values_found"]
                    ]
                ), f"Found conflicting values for {balance_name} balance: found values {';'.join([str(x) for x in balance_info['values_found']])}"

            opening_balance: Decimal = balances_found["opening"]["values_found"][0]
            closing_balance: Decimal = balances_found["closing"]["vaues_found"][0]
