#!/usr/bin/env python3
"""
Custom FNB Bank Statement Parser
Designed specifically for the FNB statement format discovered in the diagnostic.
"""

import os
import sys
import subprocess
import re
import datetime
from pathlib import Path
from decimal import Decimal
from typing import Optional, List, NamedTuple
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pypdfium2 as pdfium

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class StatementMetadata(NamedTuple):
    company_name: str
    opening_balance: Decimal
    closing_balance: Decimal
    statement_period: str

class Transaction(NamedTuple):
    date: datetime.date
    description: str
    amount: Decimal
    balance: Decimal
    bank_fee: Decimal

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

def clean_currency_string(raw_str: Optional[str]) -> Decimal:
    """Convert currency string to Decimal."""
    if not raw_str or raw_str.strip() == "":
        return Decimal("0.00")
    
    clean_str = raw_str.replace(",", "").replace(" ", "")
    
    if clean_str.endswith("Cr"):
        # Credit amount (positive)
        return Decimal(clean_str.replace("Cr", ""))
    else:
        # Debit amount (negative)
        return Decimal("-" + clean_str)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        all_text = ""
        for page_num in range(len(pdf)):
            page = pdf.get_page(page_num)
            textpage = page.get_textpage()
            page_text = textpage.get_text_range()
            all_text += page_text + "\n"
            textpage.close()
            page.close()
    finally:
        pdf.close()
    
    return all_text

def parse_fnb_statement(pdf_path: str) -> tuple[StatementMetadata, List[Transaction]]:
    """Parse FNB statement with custom logic."""
    logger.info(f"Parsing {pdf_path} with custom parser...")
    
    text = extract_text_from_pdf(pdf_path)
    lines = text.split('\n')
    
    # Extract metadata
    company_name = ""
    opening_balance = Decimal("0.00")
    closing_balance = Decimal("0.00")
    statement_period = ""
    
    # Look for company name and statement period in first few lines
    for line in lines[:20]:  # Check first 20 lines
        # Look for company name (usually appears near the top)
        if "Account Holder:" in line or "Statement for:" in line:
            company_parts = line.split(":")
            if len(company_parts) > 1:
                company_name = company_parts[1].strip()
        
        # Look for statement period
        if "Statement Period" in line:
            statement_period = line.strip()
    
    transactions = []
    current_year = None
    current_month = None
    
    # Extract opening balance from first transaction
    first_balance = None
    
    # Extract year from statement period
    for line in lines:
        if "Statement Period" in line:
            year_match = re.search(r'(\d{4})', line)
            if year_match:
                current_year = int(year_match.group(1))
                break
    
    if not current_year:
        raise ValueError("Could not extract year from statement")
    
    # Enhanced regex patterns for different transaction formats
    patterns = [
        # Standard format: DD MMM Description Amount Balance [Fee]
        r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+(.*?)\s+([\d,]+\.\d{2}(?:Cr)?)\s+([\d,]+\.\d{2}(?:Cr)?)\s*([\d,]+\.\d{2})?$',
        # Format with missing description: DD MMM Amount Balance [Fee]
        r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+([\d,]+\.\d{2}(?:Cr)?)\s+([\d,]+\.\d{2}(?:Cr)?)\s*([\d,]+\.\d{2})?$',
        # Very flexible format
        r'^(\d{1,2})\s+([A-Z][a-z]{2})\s+(.*?)$'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        transaction = None
        
        # Try each pattern
        for pattern_idx, pattern in enumerate(patterns):
            match = re.match(pattern, line)
            if match:
                try:
                    groups = match.groups()
                    day = int(groups[0])
                    month_str = groups[1]
                    
                    if month_str not in MONTH_NAMES:
                        continue
                    
                    month = MONTH_NAMES.index(month_str) + 1
                    
                    # Handle year transitions
                    if current_month and month < current_month:
                        current_year += 1
                    current_month = month
                    
                    if pattern_idx == 0:  # Standard format
                        description = groups[2].strip() if groups[2] else "Transaction"
                        amount_str = groups[3]
                        balance_str = groups[4]
                        fee_str = groups[5] if len(groups) > 5 and groups[5] else "0.00"
                        
                    elif pattern_idx == 1:  # Missing description format
                        description = "Transaction"
                        amount_str = groups[2]
                        balance_str = groups[3]
                        fee_str = groups[4] if len(groups) > 4 and groups[4] else "0.00"
                        
                    else:  # Very flexible - parse amounts from the end
                        rest = groups[2]
                        amounts = re.findall(r'[\d,]+\.\d{2}(?:Cr)?', rest)
                        
                        if len(amounts) >= 2:
                            description_parts = re.split(r'[\d,]+\.\d{2}(?:Cr)?', rest)
                            description = description_parts[0].strip() if description_parts[0] else "Transaction"
                            amount_str = amounts[-2]  # Second to last amount
                            balance_str = amounts[-1]  # Last amount
                            fee_str = amounts[-3] if len(amounts) >= 3 else "0.00"
                        else:
                            continue
                    
                    # Clean and convert amounts
                    amount = clean_currency_string(amount_str)
                    balance = clean_currency_string(balance_str)
                    bank_fee = clean_currency_string(fee_str)
                    
                    # Create transaction
                    transaction = Transaction(
                        date=datetime.date(current_year, month, day),
                        description=description,
                        amount=amount,
                        balance=balance,
                        bank_fee=bank_fee
                    )
                    
                    transactions.append(transaction)
                    
                    # Track opening and closing balances
                    if first_balance is None:
                        first_balance = balance
                        opening_balance = balance
                    closing_balance = balance
                    
                    logger.debug(f"Parsed: {transaction}")
                    break
                    
                except Exception as e:
                    logger.debug(f"Error parsing line '{line}' with pattern {pattern_idx}: {str(e)}")
                    continue
    
    # Create metadata object
    metadata = StatementMetadata(
        company_name=company_name,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        statement_period=statement_period
    )
    
    logger.info(f"Extracted {len(transactions)} transactions")
    logger.info(f"Statement for: {company_name}")
    logger.info(f"Period: {statement_period}")
    logger.info(f"Opening Balance: {opening_balance}")
    logger.info(f"Closing Balance: {closing_balance}")
    
    return metadata, transactions

def write_transactions_to_csv(metadata: StatementMetadata, transactions: List[Transaction], 
                            output_path: str, csv_sep_char: str = ';'):
    """Write transactions to CSV file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write metadata
        f.write(f"# Statement Metadata{csv_sep_char}\n")
        f.write(f"# Company Name{csv_sep_char}{metadata.company_name}\n")
        f.write(f"# Statement Period{csv_sep_char}{metadata.statement_period}\n")
        f.write(f"# Opening Balance{csv_sep_char}{metadata.opening_balance}\n")
        f.write(f"# Closing Balance{csv_sep_char}{metadata.closing_balance}\n")
        f.write(f"#\n")  # Empty line after metadata
        
        # Write header
        f.write(f"date{csv_sep_char}description{csv_sep_char}amount{csv_sep_char}balance{csv_sep_char}bank_fee\n")
        
        # Write transactions
        for transaction in transactions:
            f.write(f"{transaction.date}{csv_sep_char}")
            f.write(f"{transaction.description}{csv_sep_char}")
            f.write(f"{transaction.amount}{csv_sep_char}")
            f.write(f"{transaction.balance}{csv_sep_char}")
            f.write(f"{transaction.bank_fee}\n")

def convert_all_pdfs_custom(input_dir, output_dir=None, csv_sep_char=';'):
    """Convert all PDFs using custom parser."""
    if output_dir is None:
        output_dir = input_dir
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_path}")
        return False
    
    logger.info(f"Found {len(pdf_files)} PDF files to convert with custom parser")
    
    success_count = 0
    failure_count = 0
    total_transactions = 0
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Converting {pdf_file.name} with custom parser...")
            
            # Parse statement
            metadata, transactions = parse_fnb_statement(str(pdf_file))
            
            if transactions:
                # Write to CSV
                csv_filename = pdf_file.stem + ".csv"
                csv_output_path = output_path / csv_filename
                
                write_transactions_to_csv(metadata, transactions, str(csv_output_path), csv_sep_char)
                
                success_count += 1
                total_transactions += len(transactions)
                logger.info(f"✅ Successfully converted {pdf_file.name} to {csv_filename} "
                          f"({len(transactions)} transactions)")
            else:
                failure_count += 1
                logger.error(f"❌ No transactions found in {pdf_file.name}")
                
        except Exception as e:
            failure_count += 1
            logger.error(f"❌ Error converting {pdf_file.name}: {str(e)}")
    
    logger.info(f"\nCUSTOM PARSER RESULTS:")
    logger.info(f"Successful conversions: {success_count}/{len(pdf_files)}")
    logger.info(f"Total transactions extracted: {total_transactions}")
    
    return success_count > 0

def generate_cashbook():
    """Generate cashbook from CSV files."""
    try:
        logger.info("Generating cashbook...")
        
        # Calculate correct path to process_cashbook.py
        script_path = Path(__file__).parent / "process_cashbook.py"
        logger.info(f"Looking for process_cashbook.py at: {script_path}")
        
        if not script_path.exists():
            logger.error(f"process_cashbook.py not found at {script_path}")
            return False
            
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Cashbook generated successfully")
            print(result.stdout)
            return True
        else:
            logger.error(f"❌ Failed to generate cashbook: {result.stderr}")
            print(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"Error generating cashbook: {str(e)}")
        return False

def determine_output_dir(input_dir: Path) -> Path:
    """Determine output directory based on input directory structure."""
    # Extract company name from path (e.g., 'ghc' from 'data/input/2025/ghc')
    company_name = input_dir.name.lower()
    
    # Construct output path (data/output/company_name)
    output_dir = Path("data/output") / company_name
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir

def main():
    """Main function."""
    input_dir = Path("data/input/2025/ghc")
    output_dir = determine_output_dir(input_dir)
    
    logger.info("Starting CUSTOM FNB Parser workflow...")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Convert PDFs using custom parser
    logger.info("Step 1: Converting PDFs with custom parser...")
    if not convert_all_pdfs_custom(input_dir):
        logger.error("❌ Custom parser failed on all PDFs.")
        return False
    
    # Generate cashbook
    logger.info("Step 2: Generating cashbook...")
    if not generate_cashbook():
        logger.error("❌ Cashbook generation failed.")
        return False
    
    logger.info("🎉 Custom parser workflow completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
