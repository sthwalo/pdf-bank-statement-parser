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
    transactions: list[Transaction], opening_balance: Decimal, lenient_validation: bool = False
) -> None:
    """For each transaction in `transactions`, checks
    that the value in the balance column is equal to the sum of the transaction
    amount and the previous balance value.
    If a single mismatch is found, an exception is raised.
    
    Args:
        transactions: List of transactions to validate
        opening_balance: Opening balance from the statement
        lenient_validation: If True, allows small discrepancies (up to 30 units) in balance calculations
    """
    prev_balance: Decimal = opening_balance
    for transaction in transactions:
        expected_balance = prev_balance + transaction.amount + transaction.bank_fee
        
        # Check if balances match, with lenient option for small discrepancies
        if expected_balance != transaction.balance:
            discrepancy = abs(expected_balance - transaction.balance)
            
            if lenient_validation and discrepancy <= Decimal('30.00'):
                # In lenient mode, log the discrepancy but continue
                print(f"WARNING: Balance discrepancy of {discrepancy} detected but ignored in lenient mode.")
                print(f"  Transaction: {transaction}")
                print(f"  Expected balance: {expected_balance}, Actual balance: {transaction.balance}")
            else:
                raise ValidationTestFailedException(
                    f"Parsing error: pre-transaction balance ({prev_balance}) + "
                    f"transaction amount ({transaction.amount}) + "
                    f"bank fee ({transaction.bank_fee}) != "
                    f"post-transaction balance ({transaction.balance}) for transaction\n"
                    f"Date: {transaction.date}, Description: {transaction.description}\n"
                    f"Discrepancy: {discrepancy}"
                )
        prev_balance = transaction.balance


def validate_transactions_sum_to_closing_balance(
    transactions: list[Transaction],
    opening_balance: Decimal,
    closing_balance: Decimal,
    lenient_validation: bool = False,
) -> None:
    """Checks that statement opening balance plus sum of transaction amounts is equal to
    statement closing balance, otherwise raising an exception
    
    Args:
        transactions: List of transactions to validate
        opening_balance: Opening balance from the statement
        closing_balance: Closing balance from the statement
        lenient_validation: If True, allows small discrepancies (up to 30 units) in balance calculations
    """
    sum_transactions: Decimal = sum([tcn.amount for tcn in transactions])
    sum_fees: Decimal = sum([tcn.bank_fee for tcn in transactions])
    expected_closing_balance: Decimal = opening_balance + sum_transactions + sum_fees
    
    if expected_closing_balance != closing_balance:
        discrepancy = abs(expected_closing_balance - closing_balance)
        
        if lenient_validation and discrepancy <= Decimal('30.00'):
            # In lenient mode, log the discrepancy but continue
            print(f"WARNING: Closing balance discrepancy of {discrepancy} detected but ignored in lenient mode.")
            print(f"  Expected closing balance: {expected_closing_balance}, Actual closing balance: {closing_balance}")
        else:
            raise ValidationTestFailedException(
                f"Closing balance on statement ({closing_balance}) "
                f"!= opening balance on statement ({opening_balance}) "
                f"+ sum of parsed transactions ({sum_transactions}) "
                f"+ sum of bank fees ({sum_fees}) "
                f"= {expected_closing_balance}\n"
                f"Discrepancy: {discrepancy}"
            )
