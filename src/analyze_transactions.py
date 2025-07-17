import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TransactionAnalyzer:
    def __init__(self):
        self.detailed_transactions = None
        self.monthly_summary = None
        self.trial_balance = None

    def load_data(self, file_path):
        """Load data from Excel file."""
        try:
            # Read all sheets
            xls = pd.ExcelFile(file_path)
            
            # Load detailed transactions with Debit/Credit columns
            self.detailed_transactions = pd.read_excel(xls, 'Detailed Transactions')
            
            # Load monthly summary
            self.monthly_summary = pd.read_excel(xls, 'Monthly Summary')
            
            # Load trial balance
            self.trial_balance = pd.read_excel(xls, 'Trial Balance')
            
            logger.info("Successfully loaded all sheets from cashbook")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def analyze_account(self, account_name):
        """Analyze transactions for a specific account."""
        try:
            # Skip TOTAL row
            if account_name == 'TOTAL':
                return None

            # Get trial balance amounts with net
            trial_bal = self.trial_balance[
                self.trial_balance['Account'] == account_name
            ].iloc[0]
            
            trial_bal_debit = trial_bal['Debit']
            trial_bal_credit = trial_bal['Credit']
            trial_bal_net = trial_bal['Net']

            # Get monthly totals with net
            monthly_debit = 0
            monthly_credit = 0
            monthly_net = 0
            
            if account_name in self.monthly_summary.columns:
                monthly_debit = self.monthly_summary[account_name]['Debit'].sum()
                monthly_credit = self.monthly_summary[account_name]['Credit'].sum()
                monthly_net = self.monthly_summary[account_name]['Net'].sum()

            # Get detailed transactions - only Debit and Credit
            account_transactions = self.detailed_transactions[
                self.detailed_transactions['Account'] == account_name
            ]

            # Calculate totals from detailed transactions - no net calculation
            detailed_debit = account_transactions['Debit'].fillna(0).sum()
            detailed_credit = account_transactions['Credit'].fillna(0).sum()

            result = {
                'account': account_name,
                'trial_balance': {
                    'debit': trial_bal_debit,
                    'credit': trial_bal_credit,
                    'net': trial_bal_net
                },
                'monthly_summary': {
                    'debit': monthly_debit,
                    'credit': monthly_credit,
                    'net': monthly_net
                },
                'detailed': {
                    'debit': detailed_debit,
                    'credit': detailed_credit,
                    'transactions': account_transactions  # Move transactions here
                },
                'reconciled': abs(trial_bal_net - (detailed_credit - detailed_debit)) < 0.01
            }
            return result

        except Exception as e:
            logger.warning(f"Error analyzing account {account_name}: {str(e)}")
            return None

    def generate_analysis_report(self, output_path):
        """Generate detailed analysis report."""
        try:
            results = []
            detailed_sheets = []  # Store detailed transaction data

            # First pass - collect all results and detailed sheets
            for account in self.trial_balance['Account'].unique():
                analysis = self.analyze_account(account)
                if analysis:
                    results.append({
                        'Account': analysis['account'],
                        'Trial Balance Net': analysis['trial_balance']['net'],
                        'Trial Balance Debit': analysis['trial_balance']['debit'],
                        'Trial Balance Credit': analysis['trial_balance']['credit'],
                        'Monthly Net': analysis['monthly_summary']['net'],
                        'Detailed Debit': analysis['detailed']['debit'],
                        'Detailed Credit': analysis['detailed']['credit'],
                        'Difference': analysis['trial_balance']['net'] - 
                                    (analysis['detailed']['credit'] - analysis['detailed']['debit']),
                        'Reconciled': analysis['reconciled']
                    })

                    # Store detailed transactions for later writing
                    if len(analysis['detailed']['transactions']) > 0:
                        sheet_name = f"{analysis['account'][:30]}_detail".replace('/', '_')
                        detailed_sheets.append({
                            'name': sheet_name,
                            'data': analysis['detailed']['transactions']
                        })

            if not results:
                logger.error("No results to write to Excel")
                return

            # Second pass - write everything to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write summary first
                summary_df = pd.DataFrame(results)
                summary_df.to_excel(writer, sheet_name='Analysis Summary', index=False)

                # Write all detailed sheets
                for sheet in detailed_sheets:
                    sheet['data'].to_excel(
                        writer,
                        sheet_name=sheet['name'],
                        index=False
                    )

            logger.info(f"Analysis report generated successfully: {output_path}")

        except Exception as e:
            logger.error(f"Error generating analysis report: {str(e)}")
            raise

def main():
    # Initialize analyzer
    analyzer = TransactionAnalyzer()
    
    # Set file paths
    input_path = Path('Annual_Cashbook_2024.xlsx')
    output_path = Path('transaction_analysis.xlsx')
    
    # Load and analyze data
    analyzer.load_data(input_path)
    analyzer.generate_analysis_report(output_path)
    
    logger.info(f"Analysis complete. Report saved to {output_path}")

if __name__ == '__main__':
    main()