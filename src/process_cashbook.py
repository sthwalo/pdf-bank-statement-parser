import pandas as pd
import os
import re
import openpyxl
from openpyxl.utils import get_column_letter

from datetime import datetime

def combine_csv_files(input_dir, start_date, end_date):
    """
    Combine multiple CSV files within the specified date range.
    """
    print(f"Reading CSV files from {input_dir} for period {start_date} to {end_date}")
    
    # Convert dates to datetime objects
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # List to store individual dataframes
    dfs = []
    
    # Read each CSV file
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_dir, filename)
            print(f"Processing {filename}")
            
            try:
                # Read CSV with semicolon separator and skip the header row
                df = pd.read_csv(file_path, sep=';', skiprows=1,
                               names=['date', 'description', 'amount', 'balance', 'bank_fee'])
                
                # Convert date column to datetime using the YYYY-MM-DD format
                df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                
                # Filter data within the date range
                mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
                df = df[mask]
                
                if not df.empty:
                    dfs.append(df)
                    print(f"Added {len(df)} rows from {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    # Combine all dataframes
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df = combined_df.sort_values('date')
        print(f"Combined {len(dfs)} CSV files, total rows: {len(combined_df)}")
        return combined_df
    else:
        raise ValueError("No data found for the specified date range")

def clean_and_process_csv(df):
    """
    Clean and process the DataFrame to create a proper cashbook.
    """
    print("Processing combined data")
    
    # Clean up the DataFrame
    # Remove rows where amount is empty
    df = df.dropna(subset=['amount'])
    
    # Convert amount to numeric
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    # Determine transaction type
    df['Type'] = df['amount'].apply(lambda x: 'Credit' if x > 0 else 'Debit')
    
    # Create separate Debit and Credit columns
    df['Debit'] = df['amount'].apply(lambda x: abs(x) if x < 0 else 0)
    df['Credit'] = df['amount'].apply(lambda x: x if x > 0 else 0)
    
    # Clean up the Balance column
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce')
    
    # Clean up the bank_fee column
    df['bank_fee'] = pd.to_numeric(df['bank_fee'], errors='coerce')
    
    # Categorize transactions
    df = categorize_transactions(df)
    
    return df

def categorize_transactions(df):
    """
    Categorize transactions based on description keywords.
    """
    # Define account mappings in a more structured way
    account_mappings = {
        # INCOME CATEGORIES
        'Income from Services': [
            'Service Income', 'Consulting Income', 'Freelance Income', 'FNB OB Pmt Nutri Feeds'
        ],
        'Investment Income': [
            'Interest Earned', 'Dividend'
        ],
        
        # EXPENSE CATEGORIES
        # Bank Related
        'Bank Charges': [
            'Penalty Interest', 'Service Fee', 'Bank Charges', 
            'Non FNB Withdrawal Fees', 'Monthly Fees', 'Service Fees',
            'Bank Charge', 'Account Fee', 'Item Fee', 'Fee', 'Fees',
            'Manual Reversal Fee', 'Unsuccessful F Declined', 'Unpaid No Funds',
            'Fee Tcib', 'Swift Commission', 'Replacement Fee', 'Card Fee',
            'Commission', 'Schd Trxn', 'Unpaid No Funds 01', 'Dr.Int.Rate',
            '!ERROR: unparsable description text!', 'Card POS Unsuccessful F Declined',
            'Bank Charges'
        ],
        
        # Transportation
        'Fuel Expense': [
            'Fuel', 'Engen', 'Total', 'Sasol', 'Trac Diamond Plaza', 'Doornpoort', 
            'Astron Energy', 'Petrol', 'BP', 'Caltex', 'Vw Parts', 'Engine Parts Luc','Fuel Purchase','Fuel Purchase Total','Fuel Purchase Engen','Fuel Purchase Sasol','Fuel Purchase Trac Diamond Plaza','Fuel Purchase','Fuel Purchase Astron Energy','Fuel Purchase BP','Fuel Purchase Caltex','Fuel Purchase Engen Linksfield Mo 428104*2012','Fuel Purchase Sasol Houghton 428104*2012 ','POS Purchase Total Boksburg Moto 428104*2012', 'Fuel Purchase Sasol Houghton 428104*2012','POS Purchase Astron Energy Cyril 428104*2012','POS Purchase Engen Bramley 428104*2012','POS Purchase Baobab Plaza 428104*2012','POS Purchase Doornpoort 428104*2012','POS Purchase Trac Diamond Plaza 428104*2012','POS Purchase Engen Linksfield Mo 428104*2012','POS Purchase Sasol Houghton 428104*2012 ','POS Purchase Total Boksburg Moto 428104*2012', 'Fuel Purchase Engen Linksfield Mo 428104*2012','Fuel Purchase Sasol Cosmo City 428104*2012'
        ],
        'Toll Fees': [
            'Plaza', 'Toll', 'Baobab Plaza', 'Capricorn Plaza', 'Kranskop Plaza',
            'Nyl Plaza', 'Carousel', 'Pumulani', 'Middleburg Tap','POS Purchase Middleburg Tap N Go', 'Doornkop Plaza', 'Toll Fees', 'Toll Fees Plaza', 'Toll Fees Trac Diamond Plaza','POS Purchase Kranskop Plaza 428104*2012','POS Purchase Capricorn Plaza 428104*2012','POS Purchase Nyl Plaza 428104*2012 ','POS Purchase Doornkop Plaza 428104*2012 '
        ],
        'Vehicle Maintenance': [
            'Parts', 'Engine Parts', 'Truck Spares', 'Vw Parts', 'Engine Parts Luc','FNB App Payment To Engine Parts Engine Parts Luc','FNB App Payment To Masikize Truck Spares'
        ],
        'Vehicle Hire': [
            'Car Hire', 'Car Rental', 'Truck Hire', 'Quantum Hire', 'Rentals', 
            'Outward Swift R024', 'Ez Truck Hire', 'Car Rental'
        ],
        'Travelling Expense': [
            'Uber', 'Taxi', 'Flight'
        ],
        
        # Office Expenses
        'Stationery and Printing': [
            'Game', 'Cenecon', 'Stationery', 'Office', 'Printing', 'Paper', 'POS Purchase Game',
            'Stationery', 'Printer Cartridges', 'Ink for Printers'
        ],
        'Telephone Expense': [
            'Airtime', 'Topup', 'Telkom', 'Vodacom', 'MTN', 'Cell C',
            'Telephone & Utilities'
        ],
        'Internet Expense': [
            'Wifi', 'Internet', 'Home Wifi', 'Fibre',
            'Internet ADSL & Hosting'
        ],
        'Business Equipment': [
            'Verimark', 'African Electro', 'Incredible', 'Hpy*', 
            'Electronic', 'POS Consultin', 'Ikh*E POS', 'Yoco', 'CSB Cosmo City','POS Purchase Bwh Northgate 428104*2012'
        ],
        
        # Personnel Expenses
        'Salaries and Wages': [
            'Driver', 'Salary', 'Tendai', 'Bonakele', 'Ncube', 'Ze', 'Send Money',
            'Salaries', 'Wages', 'Payroll', 'Staff Payment', 'Employee Payment','Settlement',
            'Salaries & Wages'
        ],
        'Director Remunerations': [
             'FNB App Payment To Lk', 'FNB App Payment To Lucky', 'FNB App Payment To Gu', 'FNB App Payment To Gr', 'FNB App Payment To G', 'FNB App Rtc Pmt To Lucky','FNB App Rtc Pmt To Lucky Nhlanhla','FNB App Rtc Pmt To Aunty Lucky','FNB App Rtc Pmt To Qiniso Nsele Lucky','FNB App Rtc Pmt To Lucky Mav Logistics','FNB App Payment To Luc Lucky','FNB App Rtc Pmt To Lucky Lucky Allowance'
        ],
        
        # Business Operations
        'Business Meetings': [
            'Nandos', 'Mcd', 'KFC', 'Chicken Licken', 'Tres Jolie', 'MCP', 'Lunch',
            'Steers', 'Galitos', 'Nizams', 'Newscafe', 'Tonys Ca', 'Snack Shop',
            'Rocky Liquor', 'Avianto',
            'Refreshments / Entertainment expences'
        ],
        'Outsourced Services': [
            'Transport', 'Masik', 'Luc Trs', 'Mas', 'Samantha Mas Logistics', 'Lucky Nikelo Logistics','FNB App Payment To Lucky Nikelo Logistics',
            'Outsourced Services'
        ],
        'Supplier Payments': [
            'Makhosin', 'Masikize', 'Supplier', 'Vendor'
        ],
        
        # Household Expenses
        'Household Expense': [
            'Grocery', 'Shoprite', 'Food', 'Ndoziz Buy', 'Beder Cash And Chic',
            'Diamond Hill', 'Checkers', 'Woolworths', 'PNP', 'Spar', 'Grocc',
            'Gro ', 'Makro', 'Edgars', 'Markham', 'Clicks', 'Dischem', 'Pharmacy',
            'BBW', 'Cotton Lounge', 'Crazy Store', 'Jet', 'MRP', 'Mrprice',
            'Euro Rivonia', 'Ok Minimark', 'Valueco', 'Csb Cosmo City',
            'Braamfontein Superm', 'Mall', 'British A', 'Cellini', 'Ladies Fash',
            'Cash Build', 'Butchery', 'Valley View', 'Eden Perfumes', 'Bramfontein Sup','POS Purchase S2S*Salamudestasupe 428104*2012 '
        ],
        
        # Personal Expenses
        'Drawings': [
            'ATM', 'Cash Advanc', 'Withdrawal', 'Cashback', 'Family Support'
        ],
        'Entertainment': [
            'DSTV', 'Ticketpros', 'Movies', 'Cinema', 'Liquorshop'
        ],
        'Cosmetics Expense': [
            'Cosmetics', 'Umumodi', 'Perfume'
        ],
        
        # Financial Expenses
        'Insurance': [
            'FNB Insure', 'Internal Debit Order', 'Insurance'
        ],
        'Interest Paid': [
            'Int On Debit Balance', 'Loan Interest'
        ],
        'Bond Payment': [
             'Mavondo', 'Rental', 'Rent', 'Mortgage', 'FNB App Transfer To','FNB App Payment To Flat'
        ],
        
        # Other Expenses
        'Educational Expenses': [
            'Sch Fees', 'School', 'Education', 'Computer Lessons', 'Extra Lessons', 'AmandaS Schoolfees',
            'Simphiwe', 'Pathfinder', 'Kids For Kids', 'School Fees', 'School Transport', 'School Uniform',
            'Educational Aids', 'Learner Support Material', 'Education and Training (Staff)'
        ],
        'Donations': [
            'Father\'S Day', 'Penlope Mail', 'Funeral', 'Donation',
            'Donations / Gifts'
        ],
        'Investment Expense': [
            'Invest', 'Investment', 'Shares'
        ],
        'Electricity': [
            'Electricity Prepaid', 'Eskom',
            'Electricity'
        ],
        
        # ASSET/LIABILITY CATEGORIES
        'Assets': [
            'Furniture', 'Equipment', 'Vehicle Purchase'
        ],
        'Liabilities': [
            'Loan', 'Debt', 'Credit Card', 'Payable'
        ],
        'Equity': [
            'Drawings', 'Retained Earnings', 'Capital'
        ],
        
        # TRANSFER CATEGORIES
        'Inter Account Transfers': [
            'Penlope Investments', 'Penelope Investments', 'Transfer Between Accounts'
        ],
        'Miscellaneous': [
            'Transfer To Trf', 'Transfer To Msu', 'Transfer To Ndu',
            'Transfer To Ukn', 'Transfer To Chantelle', 'Transfer To Sleeping Bag',
            'Transfer To Amn', 'Transfer To Mnc', 'Transfer To Sk', 'Liquorshop Cosmo',
            '4624616', 'Payment To Msu', 'Payment To Ndu',
            'S2S*Salamudestasupe', 'Steers Balfour',
            'POS Purchase S2S*Salamudestasupe 428104*2012 03 Sep','FNB App Transfer To N'
        ],
        
        # Additional new categories
        'Service Contracts': [
            'Service contract Copiers'
        ],
        'Professional Fees': [
            'Audit Fees', 'Accounting Services', 'Legal Fees'
        ],
        'Software Expenses': [
            'Computer Software and Licences'
        ],
        'Security Expenses': [
            'Security - Buildings/ Grounds'
        ],
        'Maintenance Expenses': [
            'Maintenance - Assets and Equiptment', 'Maintenance - Buildings',
            'Maintenance - Sport Facilities', 'Maintenance - Grounds'
        ],
        'Equipment': [
            'Tools / Equiptment', 'Protective Clothing'
        ],
        'Cleaning': [
            'Cleaning aids', 'Cleaning Material'
        ],
        'Affiliations': [
            'Affiliations', 'Badges'
        ],
        'Concert Expenses': [
            'Concert Facilitated', 'Concert Presented'
        ],
        'Compliance Fees': [
            'Compliance Fees (COIDA)'
        ],
        'Sporting Activities': [
            'Sporting Activities'
        ],
        'Trust Expenses': [
            'Trust Expenses'
        ],
        'Transportation Expenses': [
            'Fuel & Other Transport costs'
        ],
        'Rent': [
            'Rent'
        ],
        'Excursions': [
            'Excursions'
        ],
    }

    # Add Account column with default value
    df['Account'] = 'Uncategorized'
    
    # Case-insensitive categorization
    for account, keywords in account_mappings.items():
        for keyword in keywords:
            mask = (df['Account'] == 'Uncategorized') & df['description'].astype(str).str.lower().str.contains(keyword.lower(), na=False)
            df.loc[mask, 'Account'] = account
    
    # Additional categorization rules from audit analysis
    # Handle FNB App payments and transfers
    fnb_app_mask = df['description'].astype(str).str.contains('FNB App', case=False, na=False)
    df.loc[fnb_app_mask & df['description'].str.contains('Gro|Grocc', case=False, na=False), 'Account'] = 'Household Expense'
    df.loc[fnb_app_mask & df['description'].str.contains('Petrol', case=False, na=False), 'Account'] = 'Fuel Expense'
    df.loc[fnb_app_mask & df['description'].str.contains('Car|Rental|Hire', case=False, na=False), 'Account'] = 'Vehicle Hire'
    
    # Additional categorization rules
    credit_mask = (df['Type'] == 'Credit') & (~df['description'].astype(str).str.contains(
        'Int|Interest|Service Fee', case=False, na=False))
    df.loc[credit_mask & (df['Account'] == 'Uncategorized'), 'Account'] = 'Income from Services'
    
    # Define account types mapping
    account_types = {
        # Income
        'Income from Services': 'Income',
        'Investment Income': 'Income',
        
        # Expenses
        'Bank Charges': 'Expense',
        'Fuel Expense': 'Expense',
        'Toll Fees': 'Expense',
        'Vehicle Maintenance': 'Expense',
        'Vehicle Hire': 'Expense',
        'Travelling Expense': 'Expense',
        'Stationery and Printing': 'Expense',
        'Telephone Expense': 'Expense',
        'Internet Expense': 'Expense',
        'Business Equipment': 'Expense',
        'Salaries and Wages': 'Expense',
        'Director Remunerations': 'Expense',
        'Business Meetings': 'Expense',
        'Outsourced Services': 'Expense',
        'Supplier Payments': 'Expense',
        'Household Expense': 'Expense',
        'Drawings': 'Equity',
        'Entertainment': 'Expense',
        'Cosmetics Expense': 'Expense',
        'Insurance': 'Expense',
        'Interest Paid': 'Expense',
        'Bond Payment': 'Expense',
        'Educational Expenses': 'Expense',
        'Donations': 'Expense',
        'Investment Expense': 'Expense',
        'Electricity': 'Expense',
        'Service Contracts': 'Expense',
        'Professional Fees': 'Expense',
        'Software Expenses': 'Expense',
        'Security Expenses': 'Expense',
        'Maintenance Expenses': 'Expense',
        'Equipment': 'Expense',
        'Cleaning': 'Expense',
        'Affiliations': 'Expense',
        'Concert Expenses': 'Expense',
        'Compliance Fees': 'Expense',
        'Sporting Activities': 'Expense',
        'Trust Expenses': 'Expense',
        'Transportation Expenses': 'Expense',
        'Rent': 'Expense',
        'Excursions': 'Expense',

        # Assets/Liabilities/Equity
        'Assets': 'Asset',
        'Liabilities': 'Liability',
        'Equity': 'Equity',
        
        # Transfers
        'Inter Account Transfers': 'Transfer',
        
        # Default
        'Uncategorized': 'Unknown'
    }
    
    df['Account Type'] = df['Account'].map(account_types)
    
    return df

def generate_trial_balance(df):
    """
    Generate a trial balance from the categorized transactions.
    """
    trial_balance = df.groupby('Account').agg({
        'Debit': 'sum',
        'Credit': 'sum'
    }).reset_index()
    
    trial_balance['Net'] = trial_balance['Debit'] - trial_balance['Credit']
    trial_balance['Account Type'] = trial_balance['Account'].map(
        df.groupby('Account')['Account Type'].first())
    
    # Sort by account type and name
    trial_balance = trial_balance.sort_values(['Account Type', 'Account'])
    
    # Add totals row
    totals = pd.DataFrame({
        'Account': ['TOTAL'],
        'Debit': [trial_balance['Debit'].sum()],
        'Credit': [trial_balance['Credit'].sum()],
        'Net': [trial_balance['Net'].sum()],
        'Account Type': ['']
    })
    
    trial_balance = pd.concat([trial_balance, totals], ignore_index=True)
    
    return trial_balance

def generate_management_accounts(df):
    """
    Generate management accounts from the processed data.
    """
    # Calculate totals by account type
    account_totals = df.groupby(['Account Type', 'Account']).agg({
        'Debit': 'sum',
        'Credit': 'sum'
    }).reset_index()
    
    account_totals['Net'] = account_totals['Debit'] - account_totals['Credit']
    
    # Income Statement
    income_accounts = account_totals[account_totals['Account Type'] == 'Income']
    expense_accounts = account_totals[account_totals['Account Type'] == 'Expense']
    
    total_income = abs(income_accounts['Credit'].sum() - income_accounts['Debit'].sum())
    total_expenses = expense_accounts['Debit'].sum() - expense_accounts['Credit'].sum()
    net_profit = total_income - total_expenses
    
    income_statement = pd.DataFrame({
        'Category': ['Revenue', 'Less: Expenses', 'Net Profit/(Loss)'],
        'Amount': [total_income, total_expenses, net_profit]
    })
    
    # Balance Sheet
    assets = account_totals[account_totals['Account Type'] == 'Asset']['Net'].sum()
    liabilities = account_totals[account_totals['Account Type'] == 'Liability']['Net'].sum()
    equity = account_totals[account_totals['Account Type'] == 'Equity']['Net'].sum()
    
    balance_sheet = pd.DataFrame({
        'Category': ['Assets', 'Liabilities', 'Equity', 'Retained Earnings'],
        'Amount': [assets, liabilities, equity, net_profit]
    })
    
    return income_statement, balance_sheet

def generate_cashbook_excel(df, output_path):
    """
    Generate an Excel cashbook with management accounts.
    """
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Create monthly summary
        monthly_summary = df.groupby([pd.Grouper(key='date', freq='ME'), 'Account']).agg({
            'Debit': 'sum',
            'Credit': 'sum'
        }).reset_index()
        
        # Calculate Net after aggregation
        monthly_summary['Net'] = monthly_summary['Debit'] - monthly_summary['Credit']
        
        # Write each sheet
        # Format the date column before writing to Excel
        df_formatted = df.copy()
        df_formatted['date'] = df_formatted['date'].dt.strftime('%Y-%m-%d')
        
        monthly_summary_formatted = monthly_summary.copy()
        monthly_summary_formatted['date'] = monthly_summary_formatted['date'].dt.strftime('%Y-%m-%d')
        
        # Write to Excel
        df_formatted.to_excel(writer, sheet_name='Detailed Transactions', index=False)
        monthly_summary_formatted.to_excel(writer, sheet_name='Monthly Summary', index=False)
        
        # Generate and write trial balance
        trial_balance = generate_trial_balance(df)
        trial_balance.to_excel(writer, sheet_name='Trial Balance', index=False)
        
        # Format worksheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Adjust column widths
            for idx, col in enumerate(worksheet.columns, 1):
                worksheet.column_dimensions[get_column_letter(idx)].width = 15
                
            # Format date columns to show as dates
            if sheet_name in ['Detailed Transactions', 'Monthly Summary']:
                # Format the date column (assuming it's the first column)
                for cell in worksheet['A'][1:]:  # Skip header row
                    try:
                        cell.number_format = 'yyyy-mm-dd'
                    except:
                        pass

if __name__ == "__main__":
    # Set the fiscal year date range
    start_date = '2023-03-01'
    end_date = '2024-02-28'
    
    # Get the input and output paths
    input_dir = '/Users/sthwalonyoni/pdf-bank-statement-parser/data/input/2024'
    output_path = os.path.join(os.path.dirname(input_dir), "Annual_Cashbook_2024.xlsx")
    
    try:
        # Combine and process CSV files
        df = combine_csv_files(input_dir, start_date, end_date)
        df = clean_and_process_csv(df)
        
        # Generate the Excel cashbook
        generate_cashbook_excel(df, output_path)
        print(f"\nAnnual cashbook generated successfully: {output_path}")
        
    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        print("\nDetailed error information:")
        traceback.print_exc()