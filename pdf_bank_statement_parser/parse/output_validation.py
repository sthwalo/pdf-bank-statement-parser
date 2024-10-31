"""Utilities for validating produced data"""

from decimal import Decimal

from pdf_bank_statement_parser.exceptions import ValidationTestFailedException
from pdf_bank_statement_parser.objects import Transaction


def validate_global_balances_found(global_balances_found: dict[str, dict]) -> None:
    """Checks whether all matches found for a global balance pattern
    (e.g. opening balance) extract the same value.
    This is done for each global balance found.
    If 2 different values are found for the same global balance,
    an exception is raised."""
    for balance_name, balance_info in global_balances_found.items():
        if not all(
            [
                bal == balance_info["values_found"][0]
                for bal in balance_info["values_found"]
            ]
        ):
            raise ValidationTestFailedException(
                f"Found conflicting values for {balance_name} balance: found values {';'.join([str(x) for x in balance_info['values_found']])}"
            )


def validate_transactions_agree_with_balance_column(
    transactions: list[Transaction], opening_balance: Decimal
) -> None:
    """For each transaction in `transactions`, checks
    that the value in the balance column is equal to the sum of the transaction
    amount and the previous balance value.
    If a single mismatch is found, an exception is raised.
    """
    prev_balance: Decimal = opening_balance
    for transaction in transactions:
        if prev_balance + transaction.amount != transaction.balance:
            raise ValidationTestFailedException(
                f"Parsing error: pre-transaction balance ({prev_balance}) + transaction amount ({transaction.amount}) != post-transaction balance for transaction \n{transaction.balance}"
            )
        prev_balance = transaction.balance


def validate_transactions_sum_to_closing_balance(
    transactions: list[Transaction],
    opening_balance: Decimal,
    closing_balance: Decimal,
) -> None:
    """Checks that statement opening balance plus sum of transaction amounts is equal to
    statement closing balance, otherwise raising an exception"""
    sum_transactions: Decimal = sum([tcn.amount for tcn in transactions])
    expected_closing_balance: Decimal = opening_balance + sum_transactions
    if expected_closing_balance != closing_balance:
        raise ValidationTestFailedException(
            f"Closing balance on statement ({closing_balance}) "
            f"!= opening balance on statement ({opening_balance}) "
            f"+ sum of parsed transactions ({sum_transactions}) "
            f"= {expected_closing_balance}"
        )
