# backend/app/services/gas_production_extractor.py
"""
Optimized extractor for gas production Excel files.
Gas data is already normalized (one row per month), but needs proper extraction.
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path


MONTH_NAME_MAP = {
    "JAN": (1, "Jan"), "JANUARY": (1, "Jan"),
    "FEB": (2, "Feb"), "FEBRUARY": (2, "Feb"),
    "MAR": (3, "Mar"), "MARCH": (3, "Mar"),
    "APR": (4, "Apr"), "APRIL": (4, "Apr"),
    "MAY": (5, "May"),
    "JUN": (6, "Jun"), "JUNE": (6, "Jun"),
    "JUL": (7, "Jul"), "JULY": (7, "Jul"),
    "AUG": (8, "Aug"), "AUGUST": (8, "Aug"),
    "SEP": (9, "Sep"), "SEPT": (9, "Sep"), "SEPTEMBER": (9, "Sep"),
    "OCT": (10, "Oct"), "OCTOBER": (10, "Oct"),
    "NOV": (11, "Nov"), "NOVEMBER": (11, "Nov"),
    "DEC": (12, "Dec"), "DECEMBER": (12, "Dec"),
}


def clean_col(x) -> str:
    """Clean column name: normalize whitespace."""
    return re.sub(r"\s+", " ", str(x).strip())


def extract_year_from_filename(fname: str):
    """Extract year from filename."""
    m = re.search(r"(2020|2021|2022|2023|2024|2025|2026)", fname)
    return int(m.group(1)) if m else None


def normalize_month(month_str: str, fallback_year: int):
    """
    Returns (year, month_num, month_abbrev) from month name string.
    """
    if not month_str or pd.isna(month_str):
        return (None, None, None)
    
    s = clean_col(str(month_str)).upper()
    
    if s in MONTH_NAME_MAP:
        mnum, mname = MONTH_NAME_MAP[s]
        return (fallback_year, mnum, mname)
    
    return (None, None, None)


def read_with_dynamic_header(path: str) -> pd.DataFrame:
    """
    Detect correct header row by finding keywords like MONTHS, PRODUCTION, etc.
    Gas files typically have header at row 6.
    """
    preview = pd.read_excel(path, header=None, nrows=20)
    header_row = None
    
    # Look for header row with MONTHS or PRODUCTION keywords
    for i in range(len(preview)):
        row = " ".join(str(x).upper() for x in preview.iloc[i] if pd.notna(x))
        if any(keyword in row for keyword in ["MONTHS", "PRODUCTION", "MMSCF", "GAS"]):
            # Check if next row has actual data (not another header)
            if i + 1 < len(preview):
                next_row = " ".join(str(x).upper() for x in preview.iloc[i + 1] if pd.notna(x))
                if "JANUARY" in next_row or "JAN" in next_row:
                    header_row = i
                    break
    
    if header_row is None:
        # Fallback: try row 6 (common for gas files)
        header_row = 6
    
    df = pd.read_excel(path, header=header_row)
    df.columns = [clean_col(c) for c in df.columns]
    df = df.dropna(how="all")
    
    # Remove rows that are headers or totals
    if "MONTHS" in df.columns:
        df = df[df["MONTHS"].notna()]
        df = df[~df["MONTHS"].astype(str).str.upper().str.contains("TOTAL", na=False)]
    
    return df


def transform_to_fact(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Transform gas production Excel to fact table format.
    Gas data is already normalized (one row per month), just needs cleaning.
    """
    df.columns = [clean_col(c) for c in df.columns]
    
    # Extract year from filename
    file_year = extract_year_from_filename(Path(source_file).name)
    if not file_year:
        # Try to extract from sheet name if available
        file_year = 2024  # Default fallback
    
    # Ensure MONTHS column exists
    if "MONTHS" not in df.columns:
        # Try to find month column
        for col in df.columns:
            if "MONTH" in col.upper():
                df = df.rename(columns={col: "MONTHS"})
                break
    
    if "MONTHS" not in df.columns:
        return pd.DataFrame()
    
    # Normalize month names and extract year/month
    fact = df.copy()
    
    # Parse month and create date columns
    month_info = fact["MONTHS"].apply(lambda x: normalize_month(x, file_year))
    fact["Year"] = month_info.apply(lambda x: x[0])
    fact["MonthNum"] = month_info.apply(lambda x: x[1])
    fact["Month"] = month_info.apply(lambda x: x[2])
    
    # Create date_key (YYYYMMDD format, using 1st of month)
    fact["date_key"] = fact.apply(
        lambda row: int(f"{row['Year']}{row['MonthNum']:02d}01") if pd.notna(row['Year']) and pd.notna(row['MonthNum']) else None,
        axis=1
    )
    
    fact["SourceFile"] = Path(source_file).name
    
    # Keep all production metrics
    # Standard columns: AG PRODUCTION, NAG PRODUCTION, TOTAL GAS PRODUCTION, etc.
    # These will be stored in the fact table
    
    return fact


def extract_gas_production_fact(file_path: str) -> pd.DataFrame:
    """
    Extract and transform gas production Excel file directly to fact format.
    This bypasses the generic bronze/silver layers for better performance.
    
    Returns: DataFrame in fact table format (ready for warehouse)
    """
    try:
        df = read_with_dynamic_header(file_path)
        fact = transform_to_fact(df, file_path)
        return fact
    except Exception as e:
        raise Exception(f"Failed to extract gas production from {file_path}: {str(e)}")
