# backend/app/services/concession_extractor.py
"""
Optimized extractor for concession situation PDF files.
Concession data is in PDF format and needs table extraction.
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def extract_year_from_filename(fname: str):
    """Extract year from filename."""
    m = re.search(r"(2020|2021|2022|2023|2024|2025|2026)", fname)
    return int(m.group(1)) if m else None


def extract_concession_fact(file_path: str) -> pd.DataFrame:
    """
    Extract and transform concession PDF file directly to fact format.
    This bypasses the generic bronze/silver layers for better performance.
    
    Returns: DataFrame in fact table format (ready for warehouse)
    """
    if not PDF_AVAILABLE:
        raise Exception("pdfplumber is required for PDF extraction. Install with: pip install pdfplumber")
    
    try:
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract tables from page
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # Convert to DataFrame
                        # First row is usually header
                        df = pd.DataFrame(table[1:], columns=table[0] if table else None)
                        
                        # Clean column names
                        df.columns = [str(col).strip() if col else f"col_{i}" for i, col in enumerate(df.columns)]
                        
                        # Add page number for tracking
                        df["_page_num"] = page_num
                        
                        all_tables.append(df)
                        
                except Exception as e:
                    # Continue with next page if one fails
                    continue
        
        if not all_tables:
            return pd.DataFrame()
        
        # Combine all tables
        combined = pd.concat(all_tables, ignore_index=True)
        
        # Extract year from filename
        file_year = extract_year_from_filename(Path(file_path).name) or 2024
        
        # Add metadata
        combined["Year"] = file_year
        combined["SourceFile"] = Path(file_path).name
        
        # Try to identify key columns (may vary by PDF structure)
        # Common columns: Operator, Block, Field, Status, etc.
        key_columns = {}
        for col in combined.columns:
            col_upper = str(col).upper()
            if "OPERATOR" in col_upper:
                key_columns["operator"] = col
            elif "BLOCK" in col_upper:
                key_columns["block"] = col
            elif "FIELD" in col_upper:
                key_columns["field"] = col
            elif "STATUS" in col_upper or "CONCESSION" in col_upper:
                key_columns["status"] = col
            elif "TYPE" in col_upper:
                key_columns["type"] = col
        
        # Map to standard names
        if "operator" in key_columns:
            combined["operating_company"] = combined[key_columns["operator"]].astype(str).str.strip()
        else:
            combined["operating_company"] = ""
        
        if "block" in key_columns:
            combined["block_name"] = combined[key_columns["block"]].astype(str).str.strip()
        else:
            combined["block_name"] = ""
        
        if "field" in key_columns:
            combined["field_name"] = combined[key_columns["field"]].astype(str).str.strip()
        else:
            combined["field_name"] = ""
        
        if "status" in key_columns:
            combined["concession_status"] = combined[key_columns["status"]].astype(str).str.strip()
        else:
            combined["concession_status"] = ""
        
        if "type" in key_columns:
            combined["concession_type"] = combined[key_columns["type"]].astype(str).str.strip()
        else:
            combined["concession_type"] = ""
        
        # Create asset name from block/field
        combined["asset_name"] = combined.apply(
            lambda row: f"{row.get('block_name', '')} - {row.get('field_name', '')}".strip(" -") or row.get("block_name", "") or row.get("field_name", ""),
            axis=1
        )
        
        # Create date_key (use year, default to first of year)
        combined["date_key"] = int(f"{file_year}0101")
        combined["MonthNum"] = 1
        combined["Month"] = "Jan"
        
        # Remove helper columns
        if "_page_num" in combined.columns:
            combined = combined.drop(columns=["_page_num"])
        
        return combined
        
    except Exception as e:
        raise Exception(f"Failed to extract concession from {file_path}: {str(e)}")
