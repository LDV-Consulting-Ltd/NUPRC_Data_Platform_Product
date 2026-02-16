"""
Analyze sample data files to determine transformation logic for each source.
"""
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the project root (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample data"

def analyze_oil_production():
    """Analyze oil production Excel file."""
    file_path = SAMPLE_DATA_DIR / "JAN-DEC-2024-RECONCILED-PRODUCTION (1).xlsx"
    if not file_path.exists():
        print(f"[ERROR] Oil file not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("OIL PRODUCTION ANALYSIS")
    print("="*80)
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"\nSheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=50)
            
            # Find header row (look for TERMINAL/STREAM)
            header_row = None
            for i in range(min(50, len(df))):
                row_str = " ".join(str(x).upper() for x in df.iloc[i] if pd.notna(x))
                if "TERMINAL" in row_str and "STREAM" in row_str:
                    header_row = i
                    break
            
            if header_row is not None:
                print(f"[OK] Header found at row {header_row}")
                df_header = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                print(f"Columns: {list(df_header.columns)}")
                print(f"Shape: {df_header.shape}")
                print(f"\nFirst 5 rows:")
                print(df_header.head().to_string())
                
                # Check for month columns
                month_cols = []
                for col in df_header.columns:
                    col_str = str(col).upper().strip()
                    if any(month in col_str for month in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
                                                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]):
                        month_cols.append(col)
                    elif pd.to_datetime(str(col), errors='coerce') is not pd.NaT:
                        month_cols.append(col)
                
                print(f"\nMonth columns detected: {month_cols}")
            else:
                print("[WARN] Header row not found")
                print(f"First 10 rows:")
                print(df.head(10).to_string())
                
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def analyze_gas_production():
    """Analyze gas production Excel file."""
    file_path = SAMPLE_DATA_DIR / "2024-Monthly-Gas-Data-for-Publication_December-2024-UPDATED.xlsx"
    if not file_path.exists():
        print(f"[ERROR] Gas file not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("GAS PRODUCTION ANALYSIS")
    print("="*80)
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"\nSheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=50)
            
            # Find header row
            header_row = None
            for i in range(min(50, len(df))):
                row_str = " ".join(str(x).upper() for x in df.iloc[i] if pd.notna(x))
                if any(keyword in row_str for keyword in ["TERMINAL", "STREAM", "OPERATOR", "FIELD", "ASSET"]):
                    header_row = i
                    break
            
            if header_row is not None:
                print(f"[OK] Header found at row {header_row}")
                df_header = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                print(f"Columns: {list(df_header.columns)}")
                print(f"Shape: {df_header.shape}")
                print(f"\nFirst 5 rows:")
                print(df_header.head().to_string())
            else:
                print("[WARN] Header row not found")
                print(f"First 10 rows:")
                print(df.head(10).to_string())
                
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def analyze_rig_disposition():
    """Analyze rig disposition Excel file."""
    file_path = SAMPLE_DATA_DIR / "RIG-DISPOSITION-REPORT-JAN-DEC-2025_VERSION-UPLOADED-ON-NUPRC-WEBSITE-1-1-2.xlsx"
    if not file_path.exists():
        print(f"[ERROR] Rig file not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("RIG DISPOSITION ANALYSIS")
    print("="*80)
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"\nSheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=50)
            
            # Find header row
            header_row = None
            for i in range(min(50, len(df))):
                row_str = " ".join(str(x).upper() for x in df.iloc[i] if pd.notna(x))
                if any(keyword in row_str for keyword in ["RIG", "OPERATOR", "FIELD", "STATUS", "DISPOSITION"]):
                    header_row = i
                    break
            
            if header_row is not None:
                print(f"[OK] Header found at row {header_row}")
                df_header = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                print(f"Columns: {list(df_header.columns)}")
                print(f"Shape: {df_header.shape}")
                print(f"\nFirst 5 rows:")
                print(df_header.head().to_string())
            else:
                print("[WARN] Header row not found")
                print(f"First 10 rows:")
                print(df.head(10).to_string())
                
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def analyze_concession():
    """Analyze concession PDF file."""
    file_path = SAMPLE_DATA_DIR / "NUPRC-Concession-Situation-Final-Merged-@-1st-January-2026.pdf"
    if not file_path.exists():
        print(f"[ERROR] Concession file not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("CONCESSION ANALYSIS")
    print("="*80)
    
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            print(f"\nTotal pages: {len(pdf.pages)}")
            
            # Analyze first few pages
            for page_num in range(min(3, len(pdf.pages))):
                page = pdf.pages[page_num]
                print(f"\n--- Page {page_num + 1} ---")
                
                # Extract text
                text = page.extract_text()
                if text:
                    lines = text.split('\n')[:20]
                    print("First 20 lines:")
                    for line in lines:
                        print(f"  {line}")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    print(f"\nFound {len(tables)} table(s)")
                    for i, table in enumerate(tables[:2]):  # Show first 2 tables
                        if table and len(table) > 0:
                            print(f"\nTable {i+1} (first 5 rows):")
                            for row in table[:5]:
                                print(f"  {row}")
    except ImportError:
        print("[WARN] pdfplumber not available, skipping PDF analysis")
        print("   (PDF structure already visible from file read)")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Analyzing Sample Data Files...")
    analyze_oil_production()
    analyze_gas_production()
    analyze_rig_disposition()
    analyze_concession()
    print("\nAnalysis complete!")
