import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExcelDataExtractor:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        if not self.file_path.suffix in ['.xls', '.xlsx']:
            raise ValueError("File must be an Excel file (.xls or .xlsx)")
            
    def read_excel(self):
        """Read Excel file and return all sheets as dictionary"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(self.file_path)
            sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Reading sheet: {sheet_name}")
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets[sheet_name] = df
                
            return sheets
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            raise

    def save_to_csv(self, sheets: dict, output_dir: str = "data/output"):
        """Save each sheet as a separate CSV file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for sheet_name, df in sheets.items():
            csv_path = output_path / f"{sheet_name}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {sheet_name} to {csv_path}")

def main():
    try:
        # Initialize extractor
        excel_path = "input/Annual Financial Statements -2014.xls"
        extractor = ExcelDataExtractor(excel_path)
        
        # Read all sheets
        sheets = extractor.read_excel()
        
        # Save to CSV files
        extractor.save_to_csv(sheets)
        
        logger.info("Excel processing completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to process Excel file: {str(e)}")
        raise

if __name__ == "__main__":
    main()