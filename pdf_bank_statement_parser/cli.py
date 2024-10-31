import argparse
import json
from pathlib import Path

from pdf_bank_statement_parser.exceptions import OutputInvalidException
from pdf_bank_statement_parser.export import write_transactions_to_csv
from pdf_bank_statement_parser.objects import Transaction
from pdf_bank_statement_parser.parse.extract_transactions import (
    extract_transactions_from_fnb_pdf_statement,
)


def parse_transactions():
    """The entrypoint of the CLI tool 'pdf-bank-statement-parser'"""
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
        help=(
            "Path to which results will be written."
            " If -f/--input_filepath was provided, --output_path is interpreted as a path to a file, otherwise --output_path is interpreted as a directory."
            " If this argument is omitted, it will default to same filename as input file (changing .pdf to .csv) or same output directory as input directory."
        ),
    )
    arg_parser.add_argument(
        "-s",
        "--csv_sep_char",
        help="Character used to separate fields in the CSV output. If this character appears within the output cells themselves, an error is raised",
        default=",",
    )
    arg_parser.add_argument(
        "-q",
        "--quiet",
        help="Add this flag to disable verbose standard output",
        action="store_true",
    )
    args = arg_parser.parse_args()

    if (args.input_filepath is None and args.input_dir is None) or (
        args.input_filepath is not None and args.input_dir is not None
    ):
        raise ValueError(
            "You must specify exactly one of -f/--input_filepath or -d/--input_dir"
        )

    if args.output_path is None:
        if args.input_filepath is not None:
            args.output_path = args.input_filepath.replace(".pdf", ".csv")
        else:
            args.output_path = args.input_dir

    if not args.quiet:
        print("VERBOSE mode is enabled (disable by adding the --quiet flag)")
        print(
            "input_arguments are:\n",
            json.dumps(vars(args), indent=4),
        )

    if args.input_filepath is not None:
        transactions: list[Transaction] = extract_transactions_from_fnb_pdf_statement(
            path_to_pdf_file=args.input_filepath,
            verbose=(not args.quiet),
        )
        write_transactions_to_csv(
            transactions=transactions,
            output_filepath=args.output_path,
            csv_sep_char=args.csv_sep_char,
            verbose=(not args.quiet),
        )

    if args.input_dir is not None:
        for input_filepath in Path(args.input_dir).glob("*.pdf"):
            transactions: list[Transaction] = (
                extract_transactions_from_fnb_pdf_statement(
                    path_to_pdf_file=input_filepath,
                    verbose=(not args.quiet),
                )
            )
            write_transactions_to_csv(
                transactions=transactions,
                output_filepath=Path(args.output_path)
                / input_filepath.with_suffix(".csv").name,
                csv_sep_char=args.csv_sep_char,
                verbose=(not args.quiet),
            )


if __name__ == "__main__":
    parse_transactions()
