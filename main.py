import re
from decimal import Decimal
from typing import Final

import pdfplumber

REGEX_SHORT_DATE: Final[str] = r"^\s*(\d{2}\s+[A-Z][a-z]{2})"  # matches e.g. '24 Dec'
REGEX_MONEY_NUM: Final[str] = (
    r"\b[\d,]+\.\d{2}(?:Cr)?\b"  # matches e.g. "420.69" or "80,085.69Cr"
)
IDENTIFY_TRANSACTION_ROW_REGEX: Final[str] = (
    REGEX_SHORT_DATE
    + r"(.*?(?!\.\d{2}(?:Cr)?\b))"  # anything not followed by cents amount
    + rf"({REGEX_MONEY_NUM})"
    + r"\s+"
    + rf"({REGEX_MONEY_NUM})"
    + rf"(?:\s+({REGEX_MONEY_NUM}))?\s*?$"  # optional 3rd amount
)

with pdfplumber.open("bank_statements/FNB_ASPIRE_CURRENT_ACCOUNT_100.pdf") as pdf:
    for page in pdf.pages:
        page_text: str = page.extract_text()
        found_opening_balance = re.search(
            r"Opening Balance\s+([\d,]+\.\d{2}(?:Cr)?)\b", page_text
        )
        if found_opening_balance:
            print("hello")
            break
            opening_balance: Decimal = Decimal(found_opening_balance.groups()[0])
            print("found opening balance:", opening_balance)
        # break
        for row in page_text.split("\n"):
            print(row)
            row_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX, row.strip())
            if row_match:
                raw_date, raw_desc, raw_amt, raw_balance, raw_fee = row_match.groups()
                print(
                    " -- MATCH -- ",
                    raw_date,
                    raw_desc,
                    raw_amt,
                    raw_balance,
                    raw_fee,
                    sep=" :: ",
                )
