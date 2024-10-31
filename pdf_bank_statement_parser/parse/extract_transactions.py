import datetime
import re
from decimal import Decimal
from pathlib import Path

import pypdfium2 as pdfium

from pdf_bank_statement_parser.constants import (
    IDENTIFY_TRANSACTION_ROW_REGEX,
    MONTH_NAMES,
)
from pdf_bank_statement_parser.parse.string_cleaning import clean_fnb_currency_string
from pdf_bank_statement_parser.objects import Transaction
from pdf_bank_statement_parser.parse.output_validation import (
    validate_global_balances_found,
    validate_transactions_agree_with_balance_column,
    validate_transactions_sum_to_closing_balance,
)


def extract_transactions_from_fnb_pdf_statement(
    path_to_pdf_file: str | Path,
    verbose: bool,
) -> list[Transaction]:
    """Reads in PDF bank statement and extracts all transactions from it"""
    if verbose:
        print("Started parsing file", path_to_pdf_file)
    transactions_found: list[Transaction] = []
    global_balances_found: dict[str, dict] = {
        "opening": {
            "regex": r"Opening Balance\s+([\d,]+\.\d{2}\s{0,2}(?:Cr)?)\b",
            "values_found": [],
        },
        "closing": {
            "regex": r"Closing Balance\s+([\d,]+\.\d{2}\s{0,2}(?:Cr)?)\b",
            "values_found": [],
        },
    }
    try:
        pdf = pdfium.PdfDocument(path_to_pdf_file)
        if verbose:
            print(f"found {len(pdf):,} pages")
        for page_num, page in enumerate(pdf, start=1):
            if verbose:
                print(f"started page {page_num:,}")
            page_text: str = page.get_textpage().get_text_bounded()
            page.close()
            if page_num == 1:
                # extract statement start year and month from first page of statement #
                current_month, current_year_raw = re.search(
                    r"Statement Period\s+:\s+\d{2}\s+([a-zA-Z]{3})[a-zA-Z]*\s+(\d{4})",
                    page_text,
                ).groups()
                current_year = int(current_year_raw)
                if verbose:
                    print(f"starting year is {current_year}")

            for balance_name, balance_info in global_balances_found.items():
                found_balances: list[str] = re.findall(balance_info["regex"], page_text)
                if found_balances:
                    for balance_raw in found_balances:
                        balance_info["values_found"].append(
                            clean_fnb_currency_string(balance_raw)
                        )
                    if verbose:
                        print(
                            f"found balances for {balance_name}: {balance_info['values_found']}"
                        )
            for row in page_text.split("\n"):
                row_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX, row.strip())
                if row_match:
                    raw_day, raw_month, raw_desc, raw_amt, raw_balance, raw_fee = (
                        row_match.groups()
                    )
                    month: str = raw_month.strip()
                    if MONTH_NAMES.index(month) < MONTH_NAMES.index(current_month):
                        # if we go to a previous month, then we assume that we have crossed into a new year #
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
    finally:
        pdf.close()
        if verbose:
            print("closed PDF")

    opening_balance: Decimal = global_balances_found["opening"]["values_found"][0]
    closing_balance: Decimal = global_balances_found["closing"]["values_found"][0]

    for validation_test, test_input_args in (
        (validate_global_balances_found, (global_balances_found,)),
        (
            validate_transactions_agree_with_balance_column,
            (transactions_found, opening_balance),
        ),
        (
            validate_transactions_sum_to_closing_balance,
            (transactions_found, opening_balance, closing_balance),
        ),
    ):
        if verbose:
            print("started test", validation_test.__name__)
        validation_test(*test_input_args)
        if verbose:
            print("test passed: ", validation_test.__name__)

    return transactions_found
