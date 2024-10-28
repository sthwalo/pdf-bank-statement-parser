import re
from typing import Final

import pdfplumber

REGEX_SHORT_DATE = r"^\s*(\d{2}\s+[A-Z][a-z]{2})"  # matches e.g. '24 Dec'
REGEX_MONEY_NUM = r"\b[\d,]+\.\d{2}(?:Cr)?\b"  # matches e.g. "420.69" or "80,085.69Cr"
IDENTIFY_TRANSACTION_ROW_REGEX = (
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
