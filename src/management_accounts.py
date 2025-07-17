import pandas as pd
import calendar
from datetime import datetime

class ManagementAccounts:
    def __init__(self, transactions_df):
        """Initialize with a DataFrame containing transactions."""
        self.transactions = transactions_df
        self.categories = {
            'Income': ['Payment From', 'Deposit', 'Credit', 'Interest Received'],
            'Expenses': {
                'Fuel': ['Fuel', 'ENGEN', 'SHELL', 'BP', 'TOTAL'],
                'Utilities': ['Electricity', 'Water', 'ESKOM'],
                'Telecommunications': ['Airtime', 'Data', 'Phone'],
                'Bank Charges': ['Fee', 'Charge', 'Admin']
            }
        }

    def categorize_transaction(self, description):
        """Categorize a transaction based on its description."""
        description = str(description).upper()
        
        # Check income categories
        for keyword in self.categories['Income']:
            if keyword.upper() in description:
                return 'Income'
        
        # Check expense categories
        for category, keywords in self.categories['Expenses'].items():
            for keyword in keywords:
                if keyword.upper() in description:
                    return category
        
        return 'Uncategorized'

    def generate_monthly_summary(self, month=None, year=None):
        """Generate monthly summary of transactions."""
        # Use current month and year if not specified
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
            
        # Convert date column if it's not already datetime
        if not pd.api.types.is_datetime64_any_dtype(self.transactions['Date']):
            self.transactions['Date'] = pd.to_datetime(self.transactions['Date'], format='%d %b')
            
        # Filter for specific month
        monthly_data = self.transactions[
            (self.transactions['Date'].dt.month == month) &
            (self.transactions['Date'].dt.year == year)
        ]
        
        # Add category column
        monthly_data['Category'] = monthly_data['Description'].apply(self.categorize_transaction)
        
        # Calculate summaries
        summary = {
            'Total Income': monthly_data[monthly_data['Amount'] > 0]['Amount'].sum(),
            'Total Expenses': abs(monthly_data[monthly_data['Amount'] < 0]['Amount'].sum()),
            'Net Position': monthly_data['Amount'].sum(),
            'Category Breakdown': monthly_data.groupby('Category')['Amount'].sum().to_dict(),
            'Transaction Count': len(monthly_data),
            'Average Transaction': monthly_data['Amount'].mean()
        }
        
        return summary

    def print_monthly_report(self, month=None, year=None):
        """Print formatted monthly management report."""
        summary = self.generate_monthly_summary(month, year)
        
        month_name = calendar.month_name[month] if month else calendar.month_name[datetime.now().month]
        year_str = str(year) if year else str(datetime.now().year)
        
        print(f"\n{'='*50}")
        print(f"Management Accounts Summary - {month_name} {year_str}")
        print(f"{'='*50}")
        print(f"\nFinancial Overview:")
        print(f"Total Income:    R {summary['Total Income']:,.2f}")
        print(f"Total Expenses:  R {summary['Total Expenses']:,.2f}")
        print(f"Net Position:    R {summary['Net Position']:,.2f}")
        
        print(f"\nCategory Breakdown:")
        for category, amount in summary['Category Breakdown'].items():
            print(f"{category:15} R {amount:,.2f}")
        
        print(f"\nTransaction Analysis:")
        print(f"Number of Transactions: {summary['Transaction Count']}")
        print(f"Average Transaction:    R {summary['Average Transaction']:,.2f}")
        print(f"\n{'='*50}")

def test_management_accounts():
    """Test the ManagementAccounts class with sample data."""
    # Create sample transaction data
    sample_data = {
        'Date': ['01 Jun', '02 Jun', '03 Jun', '04 Jun'],
        'Description': [
            'Payment From John',
            'Fuel Purchase ENGEN',
            'Airtime Purchase',
            'Bank Charges'
        ],
        'Amount': [1000.00, -500.00, -100.00, -50.00],
        'Balance': [1000.00, 500.00, 400.00, 350.00]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create management accounts instance
    ma = ManagementAccounts(df)
    
    # Generate and print report
    ma.print_monthly_report()

if __name__ == "__main__":
    test_management_accounts()