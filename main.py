import datetime
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


class PdfParsingException(Exception):
    pass


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


def clean_fnb_currency_string(raw_str: Optional[str]) -> Decimal:
    """Converts a raw currency amount string to a Decimal
    representation

    Examples:
        >>> clean_fnb_currency_string(" 80,085.69Cr ")
        Decimal('80085.69')
        >>> clean_fnb_currency_string("420.69")
        Decimal('-420.69')
    """
    if raw_str is None:
        return Decimal("0.00")
    clean_str = raw_str.replace(",", "").replace(" ", "")
    if clean_str[-2:] == "Cr":
        clean_str = clean_str.replace("Cr", "")
    else:
        clean_str = f"-{clean_str}"
    return Decimal(clean_str)


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
            # extract starting year and month from first page of statement #
            current_month, current_year_raw = re.search(
                r"Statement Period\s+:\s+\d{2}\s+([a-zA-Z]{3})[a-zA-Z]*\s+(\d{4})",
                page_text,
            ).groups()
            current_year = int(current_year_raw)

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
                month: str = raw_month.strip()
                if MONTH_NAMES.index(month) < MONTH_NAMES.index(current_month):
                    # if month goes backward, we have crossed into a new year
                    current_year += 1
                current_month = month
                transaction_desc: str = (
                    "!ERROR: unparsable description text!"
                    if raw_desc.strip() == ""
                    else raw_desc.strip()
                )
                transactions_found.append(
                    Transaction(
                        date=datetime.date(
                            current_year, MONTH_NAMES.index(month) + 1, int(raw_day)
                        ),
                        description=transaction_desc,
                        amount=clean_fnb_currency_string(raw_amt),
                        balance=clean_fnb_currency_string(raw_balance),
                        bank_fee=clean_fnb_currency_string(raw_fee),
                    )
                )

    # validate balances found #
    for balance_name, balance_info in balances_found.items():
        if not all(
            [
                bal == balance_info["values_found"][0]
                for bal in balance_info["values_found"]
            ]
        ):
            raise PdfParsingException(
                f"Found conflicting values for {balance_name} balance: found values {';'.join([str(x) for x in balance_info['values_found']])}"
            )

    # validate each transaction found (amount to balance relationship) #
    opening_balance: Decimal = balances_found["opening"]["values_found"][0]
    closing_balance: Decimal = balances_found["closing"]["values_found"][0]

    prev_balance: Decimal = opening_balance
    for transaction in transactions_found:
        if prev_balance + transaction.amount != transaction.balance:
            raise PdfParsingException(
                f"Parsing error: pre-transaction balance ({prev_balance}) + transaction amount ({transaction.amount}) != post-transaction balance for transaction \n{transaction.balance}"
            )
        prev_balance = transaction.balance

    sum_transactions: Decimal = sum([tcn.amount for tcn in transactions_found])
    expected_closing_balance: Decimal = opening_balance + sum_transactions
    if expected_closing_balance != closing_balance:
        raise PdfParsingException(
            f"Closing balance on statement ({closing_balance}) "
            f"!= opening balance on statement ({opening_balance}) "
            f"+ sum of parsed transactions ({sum_transactions}) "
            f"= {expected_closing_balance}"
        )
