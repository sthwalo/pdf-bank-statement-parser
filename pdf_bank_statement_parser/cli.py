import argparse

from pdf_bank_statement_parser.parse import extract_transactions_from_pdf_statement

if __name__ == "__main__":
    transactions = extract_transactions_from_statement()
