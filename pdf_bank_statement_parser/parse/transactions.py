import re
from typing import Any, Optional

import pdfplumber

from pdf_bank_statement_parser.constants import (
    MONTH_NAMES,
    IDENTIFY_TRANSACTION_ROW_REGEX,
    REGEX_SHORT_DATE,
    REGEX_MONEY_NUM,
)
from pdf_bank_statement_parser.exceptions import PdfParsingException
from pdf_bank_statement_parser.parse.string_cleaning import clean_fnb_currency_string
from pdf_bank_statement_parser.objects import Transaction


def extract_transactions_from_pdf_statement(
    path_to_pdf_file: str, verbose: bool = True
) -> list[Transaction]:
    """docstring TODO"""
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
    with pdfplumber.open(path_to_pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text: str = page.extract_text()
            if page_num == 1:
                # extract starting year and month from first page of statement #
                current_month, current_year_raw = re.search(
                    r"Statement Period\s+:\s+\d{2}\s+([a-zA-Z]{3})[a-zA-Z]*\s+(\d{4})",
                    page_text,
                ).groups()
                current_year = int(current_year_raw)

            for balance_info in balances_found.values():
                found_balances: list[str] = re.findall(balance_info["regex"], row)
                if found_balances:
                    for balance_raw in found_balances:
                        balance_info["values_found"] = clean_fnb_currency_string(
                            balance_raw
                        )
