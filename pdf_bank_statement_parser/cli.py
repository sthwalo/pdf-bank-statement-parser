import argparse
import json
import sys
from pathlib import Path

from pdf_bank_statement_parser.exceptions import OutputInvalidException
from pdf_bank_statement_parser.export import write_transactions_to_csv
from pdf_bank_statement_parser.objects import Transaction
from pdf_bank_statement_parser.parse.extract_transactions import (
    extract_transactions_from_fnb_pdf_statement,
)
from pdf_bank_statement_parser.utils.pdf_analyzer import analyze_pdf_format


def parse_transactions():
    """The entrypoint of the CLI tool 'pdf-bank-statement-parser'"""
    arg_parser = argparse.ArgumentParser()
    
    # Create subparsers for different commands
    subparsers = arg_parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parser for the default 'parse' command
    parse_parser = subparsers.add_parser("parse", help="Parse PDF bank statements")
    parse_parser.add_argument(
        "-f",
        "--input_filepath",
        help="Path to a single input PDF file. You must specify exactly one of -f/--input_filepath or -d/--input_dir",
    )
    parse_parser.add_argument(
        "-d",
        "--input_dir",
        help="Path to a directory containing 1 or more PDF files. You must specify exactly one of -f/--input_filepath or -d/--input_dir",
    )
    parse_parser.add_argument(
        "-o",
        "--output_path",
        help=(
            "Path to which results will be written."
            " If -f/--input_filepath was provided, --output_path is interpreted as a path to a file, otherwise --output_path is interpreted as a directory."
            " If this argument is omitted, it will default to same filename as input file (changing .pdf to .csv) or same output directory as input directory."
        ),
    )
    parse_parser.add_argument(
        "-s",
        "--csv_sep_char",
        help="Character used to separate fields in the CSV output. If this character appears within the output cells themselves, an error is raised",
        default=",",
    )
    parse_parser.add_argument(
        "-q",
        "--quiet",
        help="Add this flag to disable verbose standard output",
        action="store_true",
    )
    parse_parser.add_argument(
        "--debug",
        help="Enable debug mode with detailed output for troubleshooting parsing issues",
        action="store_true",
    )
    parse_parser.add_argument(
        "--lenient",
        help="Enable lenient validation mode that allows small discrepancies in balance calculations",
        action="store_true",
    )
    parse_parser.add_argument(
        "--skip-validation",
        help="Skip validation checks entirely (use with caution)",
        action="store_true",
    )
    
    # Parser for the 'analyze' command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze PDF format for troubleshooting")
    analyze_parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to analyze",
    )
    analyze_parser.add_argument(
        "-q",
        "--quiet",
        help="Add this flag to disable verbose output",
        action="store_true",
    )
    
    # For backward compatibility, make 'parse' the default command if none is specified
    args = arg_parser.parse_args()
    if args.command is None:
        args.command = "parse"
        
        # Check if any arguments were provided
        if len(sys.argv) == 1:
            arg_parser.print_help()
            sys.exit(1)
    
    # Handle the analyze command
    if args.command == "analyze":
        analyze_pdf_format(args.pdf_path, verbose=not args.quiet)
        return
    
    # Handle the parse command (default)
    if args.input_filepath is None and args.input_dir is None:
        raise ValueError(
            "You must specify exactly one of -f/--input_filepath or -d/--input_dir"
        )
    
    if args.input_filepath is not None and args.input_dir is not None:
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
        try:
            transactions: list[Transaction] = extract_transactions_from_fnb_pdf_statement(
                path_to_pdf_file=args.input_filepath,
                verbose=(not args.quiet),
                debug=args.debug,
                lenient_validation=args.lenient,
            )
            write_transactions_to_csv(
                transactions=transactions,
                output_filepath=args.output_path,
                csv_sep_char=args.csv_sep_char,
                verbose=(not args.quiet),
            )
        except Exception as e:
            if args.debug:
                import traceback
                print(f"ERROR processing {args.input_filepath}:")
                traceback.print_exc()
            else:
                print(f"ERROR processing {args.input_filepath}: {str(e)}")
                print("Run with --debug for more information")

    if args.input_dir is not None:
        success_count = 0
        failure_count = 0
        for input_filepath in Path(args.input_dir).glob("*.pdf"):
            try:
                if not args.quiet:
                    print(f"\n{'='*50}\nProcessing {input_filepath}\n{'='*50}")
                
                transactions: list[Transaction] = (
                    extract_transactions_from_fnb_pdf_statement(
                        path_to_pdf_file=input_filepath,
                        verbose=(not args.quiet),
                        debug=args.debug,
                        lenient_validation=args.lenient,
                    )
                )
                output_filepath = Path(args.output_path) / input_filepath.with_suffix(".csv").name
                write_transactions_to_csv(
                    transactions=transactions,
                    output_filepath=output_filepath,
                    csv_sep_char=args.csv_sep_char,
                    verbose=(not args.quiet),
                )
                success_count += 1
            except Exception as e:
                failure_count += 1
                if args.debug:
                    import traceback
                    print(f"ERROR processing {input_filepath}:")
                    traceback.print_exc()
                else:
                    print(f"ERROR processing {input_filepath}: {str(e)}")
                    print("Run with --debug for more information")
                
                # Continue with next file even if this one failed
                continue
        
        print(f"\nProcessing complete: {success_count} files succeeded, {failure_count} files failed")


if __name__ == "__main__":
    parse_transactions()
