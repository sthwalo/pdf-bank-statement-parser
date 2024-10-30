# pdf-bank-statement-parser

I built this command-line tool because First National Bank (FNB) South Africa only gives the option of exporting historic statements to PDF, which is a terrible format to use for any downstream task other than reading.

This tool uses [pdfplumber](https://github.com/jsvine/pdfplumber)) for text extraction from the PDF, but has no other package dependencies.

This tool exports all transactions from a PDF bank statement and exports them into a CSV file. It does this by exporting the PDF contents to text and then extracting the transactions and balances using REGEX.

The parsed results are verified as follows:

1. It is checked (for every transaction extracted) that the balance amount is the sum of the previous balance and the transaction amount.

2. It is checked that the opening balance reported on the statement plus the sum of extracted transaction amounts is equal to the closing balance reported on the statement.

This tool currently only works on First National Bank (FNB) current account statements, but I'm happy to extend it to other bank statement formats if there is a need.
