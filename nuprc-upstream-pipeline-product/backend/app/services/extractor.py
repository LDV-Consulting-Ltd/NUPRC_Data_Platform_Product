# backend/app/services/extractor.py
"""
Extract tables from Excel and PDF files.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def extract_excel_tables(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract all tables from an Excel file.
    Returns list of tables, each as a dict with 'sheet_name', 'data', 'columns'.
    """
    tables = []
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Skip empty sheets
            if df.empty:
                continue
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Convert to records (list of dicts)
            records = df.to_dict('records')
            
            tables.append({
                'sheet_name': sheet_name,
                'columns': list(df.columns),
                'row_count': len(df),
                'data': records
            })
            
    except Exception as e:
        raise Exception(f"Failed to extract Excel tables from {file_path}: {str(e)}")
    
    return tables


def extract_pdf_tables(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from a PDF file.
    Returns list of tables, each as a dict with 'page', 'data', 'columns'.
    """
    if not PDF_AVAILABLE:
        raise Exception("pdfplumber not installed. Install with: pip install pdfplumber")
    
    tables = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract tables from this page
                page_tables = page.extract_tables()
                
                for table_num, table in enumerate(page_tables, 1):
                    if not table or len(table) < 2:  # Need at least header + 1 row
                        continue
                    
                    # First row is usually headers
                    headers = [str(cell).strip() if cell else f"col_{i}" 
                              for i, cell in enumerate(table[0])]
                    
                    # Remaining rows are data
                    rows = []
                    for row in table[1:]:
                        if any(cell for cell in row):  # Skip completely empty rows
                            rows.append([str(cell).strip() if cell else "" 
                                       for cell in row])
                    
                    if rows:
                        # Convert to records
                        records = []
                        for row in rows:
                            # Pad row if needed
                            while len(row) < len(headers):
                                row.append("")
                            record = dict(zip(headers, row[:len(headers)]))
                            records.append(record)
                        
                        tables.append({
                            'page': page_num,
                            'table_number': table_num,
                            'columns': headers,
                            'row_count': len(records),
                            'data': records
                        })
                        
    except Exception as e:
        raise Exception(f"Failed to extract PDF tables from {file_path}: {str(e)}")
    
    return tables


def extract_tables(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    """
    Extract tables from a file based on its type.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_type == 'excel' or path.suffix.lower() in ['.xlsx', '.xls']:
        return extract_excel_tables(file_path)
    elif file_type == 'pdf' or path.suffix.lower() == '.pdf':
        return extract_pdf_tables(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
