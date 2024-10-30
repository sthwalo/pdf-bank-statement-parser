import argparse
import csv

from pdf_bank_statement_parser.objects import Transaction
from pdf_bank_statement_parser.parse.extract_transactions import (
    extract_transactions_from_fnb_pdf_statement,
)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-f",
        "--input_filepath",
        help="Path to a single input PDF file. You must specify exactly one of -f/--input_filepath or -d/--input_dir",
    )
    arg_parser.add_argument(
        "-d",
        "--input_dir",
        help="Path to a directory containing 1 or more PDF files. You must specify exactly one of -f/--input_filepath or -d/--input_dir",
    )
    arg_parser.add_argument(
        "-o",
        "--output_path",
        help="Path to which results will be written. If -f/--input_filepath was provided, this is interpreted as a path to a file, otherwise it is interpreted as a directory.",
        required=True,
    )
    args = arg_parser.parse_args()

    if (args.input_filepath is None and args.input_dir is None) or (
        args.input_filepath is not None and args.input_dir is not None
    ):
        raise ValueError(
            "You must specify exactly one of -f/--input_filepath or -d/--input_dir"
        )

    if args.input_filepath is not None:
        transactions: list[Transaction] = extract_transactions_from_fnb_pdf_statement(
            path_to_pdf_file=args.input_filepath
        )
        with open(args.output_path, "w", encoding="utf-8") as file:
            csv_writer = csv.DictWriter(
                file,
                fieldnames=["date", "description", "amount", "balance", "bank_fee"],
                delimiter="|",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )
            csv_writer.writeheader()
            for transaction in transactions:
                csv_writer.writerow(transaction._asdict())

    if args.input_dir is not None:
        print("TODO")
