# backend/app/services/oil_production_extractor.py
"""
Optimized extractor for oil production Excel files.
Uses proven logic: dynamic header detection + month column melting.
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path


# Month-name mapping (for 2021+ style headers)
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


def is_month_col(colname) -> bool:
    """
    True if header is:
      - a Timestamp (2020 style), OR
      - a month name like JANUARY (2021+ style), OR
      - a date-parsable string.
    Excludes TOTAL and Unnamed columns.
    """
    if colname is None or (isinstance(colname, float) and pd.isna(colname)):
        return False

    if isinstance(colname, pd.Timestamp):
        return True

    s = clean_col(colname).upper()

    if s in {"TOTAL", "GRAND TOTAL"} or s.startswith("UNNAMED"):
        return False

    if s in MONTH_NAME_MAP:
        return True

    dt = pd.to_datetime(s, errors="coerce")
    return pd.notna(dt)


def normalize_month(colname, fallback_year: int):
    """
    Returns (year, month_num, month_abbrev)
    - If header is a date → use its year/month
    - If header is a month name (JANUARY) → use fallback_year + mapped month
    """
    if isinstance(colname, pd.Timestamp):
        return (int(colname.year), int(colname.month), colname.strftime("%b"))

    s = clean_col(colname).upper()

    if s in MONTH_NAME_MAP:
        mnum, mname = MONTH_NAME_MAP[s]
        return (fallback_year, mnum, mname)

    dt = pd.to_datetime(s, errors="coerce")
    if pd.notna(dt):
        return (int(dt.year), int(dt.month), dt.strftime("%b"))

    return (None, None, None)


def read_with_dynamic_header(path: str) -> pd.DataFrame:
    """
    Detect correct header row by finding a row containing both 'TERMINAL' and 'STREAM'.
    This is the proven logic from the working script.
    """
    preview = pd.read_excel(path, header=None, nrows=45)
    header_row = None

    for i in range(len(preview)):
        row = " ".join(str(x).upper() for x in preview.iloc[i] if pd.notna(x))
        if "TERMINAL" in row and "STREAM" in row:
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Header not found in {path}")

    df = pd.read_excel(path, header=header_row)
    df.columns = [clean_col(c) for c in df.columns]
    df = df.dropna(how="all")

    # Drop rows that look like repeated headers inside the data
    if "TERMINAL/STREAM" in df.columns:
        df = df[~df["TERMINAL/STREAM"].astype(str).str.upper().str.contains("TERMINAL", na=False)]

    return df


def transform_to_fact(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Transform oil production Excel to fact table format.
    Melts month columns into rows immediately (proven approach).
    """
    df.columns = [clean_col(c) for c in df.columns]

    month_cols = [c for c in df.columns if is_month_col(c)]
    id_cols = [c for c in df.columns if c not in month_cols]

    if not month_cols:
        return pd.DataFrame()

    # Optional: remove blank/total rows
    if "TERMINAL/STREAM" in df.columns:
        df = df.dropna(subset=["TERMINAL/STREAM"], how="all")
        df = df[~df["TERMINAL/STREAM"].astype(str).str.upper().str.contains("TOTAL", na=False)]

    # If TOTAL exists, keep it for validation (stays in id_cols)
    if "TOTAL" in df.columns:
        df["TOTAL"] = pd.to_numeric(df["TOTAL"], errors="coerce")

    # Melt months to rows (this is the key optimization!)
    fact = df.melt(
        id_vars=id_cols,
        value_vars=month_cols,
        var_name="MonthRaw",
        value_name="Production_Barrels"
    )

    file_year = extract_year_from_filename(Path(source_file).name)

    ym = fact["MonthRaw"].apply(lambda x: normalize_month(x, file_year))
    fact["Year"] = ym.apply(lambda x: x[0])
    fact["MonthNum"] = ym.apply(lambda x: x[1])
    fact["Month"] = ym.apply(lambda x: x[2])
    fact.drop(columns=["MonthRaw"], inplace=True)

    fact["SourceFile"] = Path(source_file).name

    # Numeric cleanup
    fact["Production_Barrels"] = pd.to_numeric(fact["Production_Barrels"], errors="coerce")
    fact = fact.dropna(subset=["Production_Barrels"])

    return fact


def extract_oil_production_fact(file_path: str) -> pd.DataFrame:
    """
    Extract and transform oil production Excel file directly to fact format.
    This bypasses the generic bronze/silver layers for better performance.
    
    Returns: DataFrame in fact table format (ready for warehouse)
    """
    try:
        df = read_with_dynamic_header(file_path)
        fact = transform_to_fact(df, file_path)
        return fact
    except Exception as e:
        raise Exception(f"Failed to extract oil production from {file_path}: {str(e)}")
