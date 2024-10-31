"""Utilities for exporting data to different formats"""

import csv

from pdf_bank_statement_parser.exceptions import OutputInvalidException
from pdf_bank_statement_parser.objects import Transaction


def write_transactions_to_csv(
    transactions: list[Transaction],
    output_filepath: str,
    csv_sep_char: str = ",",
    verbose: bool = True,
) -> None:
    """Writes parsed transactions into a single CSV file"""
    with open(output_filepath, "w", encoding="utf-8") as file:
        csv_writer = csv.DictWriter(
            file,
            fieldnames=["date", "description", "amount", "balance", "bank_fee"],
            delimiter=csv_sep_char,
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer.writeheader()
        for transaction in transactions:
            transaction_dict: dict = transaction._asdict()
            for field_name, field_value in transaction_dict.items():
                if csv_sep_char in str(field_value):
                    raise OutputInvalidException(
                        f"Cannot produce valid output because found CSV-separator character '{csv_sep_char}' in field '{field_name}' of transaction {transaction_dict}"
                    )
            csv_writer.writerow(transaction_dict)
    if verbose:
        print(f"Wrote {len(transactions):,} transactions to '{output_filepath}'")
