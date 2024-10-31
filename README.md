# PDF Bank Statement Parser

[![Downloads](https://static.pepy.tech/badge/pdf-bank-statement-parser)](https://pepy.tech/project/pdf-bank-statement-parser)

Command-line tool for robustly converting PDF bank statements into clean usable CSV. Currently only works for statements from First National Bank (FNB) South Africa (please let me know if you want me to expand the scope).

## Install

```bash
pip install pdf-bank-statement-parser
```

## Example Usage

```shell
# parse a single PDF bank statement #
parse-bank-statement-pdf \
  --input_filepath 'bank_statements/2024_03_27 - 2024_06_28.pdf' \
  --output_path 'bank_statements/csv/2024_03_27 - 2024_06_28.csv'

# parse all PDF bank statements in a given directory #
parse-bank-statement-pdf \
  --input_dir 'bank_statements/' \
  --output_path 'bank_statements/csv/' \
  --csv_sep_char ';'
```

The only format available from FNB for downloading historical bank statements is PDF, which is a useless format for any kind of downstream data task other than reading.

This tool uses [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) for text extraction from PDF and native python for everything else. Transactions are extracted using RegEx.

The parsed results are verified as follows:

1. It is checked (for every transaction extracted) that the balance amount is the sum of the previous balance and the transaction amount.

2. It is checked that the opening balance reported on the statement plus the sum of extracted transactions is equal to the closing balance reported on the statement.
