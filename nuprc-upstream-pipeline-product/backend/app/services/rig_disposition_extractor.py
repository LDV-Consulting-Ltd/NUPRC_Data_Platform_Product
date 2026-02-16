# backend/app/services/rig_disposition_extractor.py
"""
Optimized extractor for rig disposition Excel files.
Rig files have multiple sheets (one per month), each with rig details.
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


def parse_month_from_sheet_name(sheet_name: str) -> tuple:
    """
    Parse month and year from sheet name like "JANUARY 2024" or "JANUARY_2025".
    Returns (year, month_num, month_abbrev) or (None, None, None).
    """
    sheet_upper = str(sheet_name).upper().strip()
    
    # Extract year
    year_match = re.search(r"(2020|2021|2022|2023|2024|2025|2026)", sheet_upper)
    year = int(year_match.group(1)) if year_match else None
    
    # Extract month
    for month_key, (month_num, month_abbrev) in MONTH_NAME_MAP.items():
        if month_key in sheet_upper:
            return (year, month_num, month_abbrev)
    
    return (None, None, None)


def find_rig_data_header_row(df_preview: pd.DataFrame) -> int:
    """
    Find the header row for rig data.
    Looks for row containing RIG COMPANY, RIG NAME, or OPERATING COMPANY.
    """
    for i in range(min(20, len(df_preview))):
        row = " ".join(str(x).upper() for x in df_preview.iloc[i] if pd.notna(x))
        if any(keyword in row for keyword in ["RIG COMPANY", "RIG NAME", "OPERATING COMPANY", "OPERATIONAL STATUS"]):
            # Check if next row has data (not another header)
            if i + 1 < len(df_preview):
                next_row = " ".join(str(x).upper() for x in df_preview.iloc[i + 1] if pd.notna(x))
                if "S/N" in next_row or any(char.isdigit() for char in str(df_preview.iloc[i + 1, 0]) if pd.notna(df_preview.iloc[i + 1, 0])):
                    return i + 1  # Data starts on next row
            return i
    
    # Fallback: try row 9-10 (common for rig files)
    for i in [9, 10, 11]:
        if i < len(df_preview):
            return i
    
    return 0  # Default to first row


def read_rig_sheet(path: str, sheet_name: str) -> pd.DataFrame:
    """
    Read a single sheet from rig disposition file.
    Returns DataFrame with rig data.
    """
    # Read preview to find header
    preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=20)
    header_row = find_rig_data_header_row(preview)
    
    # Read full sheet with detected header
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    df.columns = [clean_col(c) for c in df.columns]
    df = df.dropna(how="all")
    
    # Identify key columns (may have different names)
    key_columns = {}
    for col in df.columns:
        col_upper = str(col).upper()
        if "RIG COMPANY" in col_upper or "COMPANY" in col_upper:
            key_columns["rig_company"] = col
        elif "RIG NAME" in col_upper:
            key_columns["rig_name"] = col
        elif "RIG TYPE" in col_upper:
            key_columns["rig_type"] = col
        elif "LOCATION" in col_upper:
            key_columns["location"] = col
        elif "OPERATING COMPANY" in col_upper or "OPERATING COMPANY" in col_upper:
            key_columns["operating_company"] = col
        elif "OPERATIONAL STATUS" in col_upper or "STATUS" in col_upper:
            key_columns["operational_status"] = col
        elif "S/N" in col_upper or "SN" in col_upper:
            key_columns["serial_number"] = col
    
    # Filter to rows with actual rig data (has rig name or company)
    if "rig_name" in key_columns:
        df = df[df[key_columns["rig_name"]].notna()]
    elif "rig_company" in key_columns:
        df = df[df[key_columns["rig_company"]].notna()]
    else:
        # If no clear identifier, keep all non-empty rows
        df = df[df.notna().any(axis=1)]
    
    # Add sheet name for month identification
    df["_sheet_name"] = sheet_name
    
    return df, key_columns


def transform_to_fact(df: pd.DataFrame, key_columns: dict, sheet_name: str, source_file: str) -> pd.DataFrame:
    """
    Transform rig sheet data to fact table format.
    """
    fact = df.copy()
    
    # Extract month/year from sheet name
    year, month_num, month_abbrev = parse_month_from_sheet_name(sheet_name)
    
    if not year:
        # Fallback: try filename
        year = extract_year_from_filename(Path(source_file).name) or 2024
    
    fact["Year"] = year
    fact["MonthNum"] = month_num
    fact["Month"] = month_abbrev
    
    # Create date_key
    if month_num:
        fact["date_key"] = int(f"{year}{month_num:02d}01")
    else:
        fact["date_key"] = None
    
    # Map columns to standard names
    if "rig_company" in key_columns and key_columns["rig_company"] in fact.columns:
        fact["rig_company"] = fact[key_columns["rig_company"]].astype(str)
    else:
        fact["rig_company"] = ""
    
    if "rig_name" in key_columns and key_columns["rig_name"] in fact.columns:
        fact["rig_name"] = fact[key_columns["rig_name"]].astype(str)
    else:
        fact["rig_name"] = ""
    
    if "rig_type" in key_columns and key_columns["rig_type"] in fact.columns:
        fact["rig_type"] = fact[key_columns["rig_type"]].astype(str)
    else:
        fact["rig_type"] = ""
    
    if "location" in key_columns and key_columns["location"] in fact.columns:
        fact["location"] = fact[key_columns["location"]].astype(str)
    else:
        fact["location"] = ""
    
    if "operating_company" in key_columns and key_columns["operating_company"] in fact.columns:
        fact["operating_company"] = fact[key_columns["operating_company"]].astype(str)
    else:
        fact["operating_company"] = ""
    
    if "operational_status" in key_columns and key_columns["operational_status"] in fact.columns:
        fact["operational_status"] = fact[key_columns["operational_status"]].astype(str)
    else:
        fact["operational_status"] = ""
    
    fact["SourceFile"] = Path(source_file).name
    
    # Clean string columns
    for col in ["rig_company", "rig_name", "rig_type", "location", "operating_company", "operational_status"]:
        if col in fact.columns:
            fact[col] = fact[col].astype(str).str.strip()
            fact[col] = fact[col].replace("nan", "")
    
    return fact


def extract_rig_disposition_fact(file_path: str) -> pd.DataFrame:
    """
    Extract and transform rig disposition Excel file directly to fact format.
    Processes all sheets (months) and combines into single DataFrame.
    
    Returns: DataFrame in fact table format (ready for warehouse)
    """
    try:
        excel_file = pd.ExcelFile(file_path)
        all_facts = []
        
        for sheet_name in excel_file.sheet_names:
            try:
                result = read_rig_sheet(file_path, sheet_name)
                if result is None:
                    continue
                df, key_columns = result
                if df.empty:
                    continue
                
                fact = transform_to_fact(df, key_columns, sheet_name, file_path)
                all_facts.append(fact)
            except Exception as e:
                # Skip sheets that fail, continue with others
                continue
        
        if not all_facts:
            return pd.DataFrame()
        
        # Combine all sheets
        combined = pd.concat(all_facts, ignore_index=True)
        
        # Drop the helper column
        if "_sheet_name" in combined.columns:
            combined = combined.drop(columns=["_sheet_name"])
        
        return combined
        
    except Exception as e:
        raise Exception(f"Failed to extract rig disposition from {file_path}: {str(e)}")
