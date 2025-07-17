import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypdfium2 as pdfium

from pdf_bank_statement_parser.constants import (
    IDENTIFY_TRANSACTION_ROW_REGEX,
    IDENTIFY_TRANSACTION_ROW_REGEX_ORIGINAL,
    IDENTIFY_TRANSACTION_ROW_REGEX_ENHANCED,
)


def analyze_pdf_format(pdf_path: str | Path, verbose: bool = True) -> Dict:
    """
    Analyzes a PDF file to identify potential parsing issues and format differences.
    
    Args:
        pdf_path: Path to the PDF file to analyze
        verbose: Whether to print analysis results
        
    Returns:
        Dictionary containing analysis results
    """
    if verbose:
        print(f"Analyzing PDF format: {pdf_path}")
    
    results = {
        "file": str(pdf_path),
        "pages": 0,
        "transaction_rows": {
            "original_regex": 0,
            "enhanced_regex": 0,
            "unique_to_original": 0,
            "unique_to_enhanced": 0,
        },
        "potential_issues": [],
        "sample_transactions": []
    }
    
    try:
        # Open the PDF file
        pdf = pdfium.PdfDocument(pdf_path)
        results["pages"] = len(pdf)
        
        # Extract text from each page
        all_text = ""
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            text_page = page.get_textpage()
            page_text = text_page.get_text_range()
            all_text += page_text + "\n"
        
        # Analyze transaction rows
        original_matches = []
        enhanced_matches = []
        
        for line in all_text.split("\n"):
            original_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX_ORIGINAL, line.strip())
            enhanced_match = re.match(IDENTIFY_TRANSACTION_ROW_REGEX_ENHANCED, line.strip())
            
            if original_match:
                original_matches.append((line, original_match.groups()))
            if enhanced_match:
                enhanced_matches.append((line, enhanced_match.groups()))
        
        results["transaction_rows"]["original_regex"] = len(original_matches)
        results["transaction_rows"]["enhanced_regex"] = len(enhanced_matches)
        
        # Find rows matched by only one regex
        original_lines = set(match[0] for match in original_matches)
        enhanced_lines = set(match[0] for match in enhanced_matches)
        
        unique_to_original = original_lines - enhanced_lines
        unique_to_enhanced = enhanced_lines - original_lines
        
        results["transaction_rows"]["unique_to_original"] = len(unique_to_original)
        results["transaction_rows"]["unique_to_enhanced"] = len(unique_to_enhanced)
        
        # Sample transactions for analysis
        for i, (line, groups) in enumerate(enhanced_matches):
            if i < 5:  # Limit to 5 samples
                day, month, desc, amt, balance, fee = groups
                results["sample_transactions"].append({
                    "line": line,
                    "day": day,
                    "month": month,
                    "description": desc.strip(),
                    "amount": amt,
                    "balance": balance,
                    "fee": fee if fee else "None"
                })
        
        # Check for potential issues
        if len(unique_to_original) > 0:
            results["potential_issues"].append(
                f"Found {len(unique_to_original)} rows matched by original regex but not enhanced regex"
            )
        if len(unique_to_enhanced) > 0:
            results["potential_issues"].append(
                f"Found {len(unique_to_enhanced)} rows matched by enhanced regex but not original regex"
            )
        
        # Look for inconsistent fee formats
        fee_formats = set()
        for _, groups in enhanced_matches:
            if groups[5]:  # Fee is present
                fee_formats.add(groups[5])
        
        if len(fee_formats) > 1:
            results["potential_issues"].append(
                f"Multiple fee formats detected: {', '.join(fee_formats)}"
            )
        
        if verbose:
            print(f"Analysis complete for {pdf_path}")
            print(f"Pages: {results['pages']}")
            print(f"Transaction rows (original regex): {results['transaction_rows']['original_regex']}")
            print(f"Transaction rows (enhanced regex): {results['transaction_rows']['enhanced_regex']}")
            print(f"Rows unique to original regex: {results['transaction_rows']['unique_to_original']}")
            print(f"Rows unique to enhanced regex: {results['transaction_rows']['unique_to_enhanced']}")
            
            if results["potential_issues"]:
                print("\nPotential issues:")
                for issue in results["potential_issues"]:
                    print(f"- {issue}")
            
            if results["sample_transactions"]:
                print("\nSample transactions:")
                for i, tx in enumerate(results["sample_transactions"]):
                    print(f"\nTransaction {i+1}:")
                    print(f"  Line: {tx['line']}")
                    print(f"  Date: {tx['day']} {tx['month']}")
                    print(f"  Description: {tx['description']}")
                    print(f"  Amount: {tx['amount']}")
                    print(f"  Balance: {tx['balance']}")
                    print(f"  Fee: {tx['fee']}")
    
    except Exception as e:
        results["potential_issues"].append(f"Error analyzing PDF: {str(e)}")
        if verbose:
            print(f"Error analyzing PDF: {str(e)}")
    
    return results


def main():
    """
    Command-line interface for the PDF analyzer
    """
    if len(sys.argv) < 2:
        print("Usage: python pdf_analyzer.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_pdf_format(pdf_path)


if __name__ == "__main__":
    main()
