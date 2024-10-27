import re
from typing import Final

import pdfplumber

IDENTIFY_TRANSACTION_ROW_REGEX: Final[str] = (
    r"(?P<date>\d{2} [A-Za-z]{3})"  # e.g. '21 Oct'
    r"\s+"
    r"(?P<text>.+?)"
    r"\s+"
    r"(?P<number1>\d{1,3}(?:,\d{3})*\.\d{2}(?:\s?Cr)?)"
    r"\s+"
    r"(?P<number2>\d{1,3}(?:,\d{3})*\.\d{2}(?:\s?Cr)?)"
    r"\s+"
    r"(?P<number3>\d{1,3}(?:,\d{3})*\.\d{2}(?:\s?Cr)?)?"
)

with pdfplumber.open("bank_statements/FNB_ASPIRE_CURRENT_ACCOUNT_100.pdf") as pdf:
    for page in pdf.pages:
        page_text: str = page.extract_text()
        # break
        for row in page_text.split("\n"):
            row_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX, row.strip())
            if row_match:
                print(row_match.groups())
        break
