# backend/app/services/async_extractor.py
"""
Async table extraction with concurrent processing for multiple files.
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

try:
    import pdfplumber
    PDF_PLUMBER_AVAILABLE = True
except ImportError:
    PDF_PLUMBER_AVAILABLE = False

# Note: camelot and tabula are optional - they require additional system dependencies
# For now, we'll use pdfplumber which is more reliable and doesn't need system deps
CAMELOT_AVAILABLE = False
TABULA_AVAILABLE = False


async def extract_excel_tables_async(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract all tables from an Excel file (async wrapper).
    """
    # Run CPU-bound operation in thread pool
    return await asyncio.to_thread(extract_excel_tables_sync, file_path)


def extract_excel_tables_sync(file_path: str) -> List[Dict[str, Any]]:
    """Synchronous Excel extraction."""
    tables = []
    
    try:
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            if df.empty:
                continue
            
            df.columns = [str(col).strip() for col in df.columns]
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


async def extract_pdf_tables_async(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF using multiple methods for best results.
    Tries: pdfplumber (fastest) -> camelot (best quality) -> tabula (fallback)
    """
    # Run CPU-bound operation in thread pool
    return await asyncio.to_thread(extract_pdf_tables_sync, file_path)


def extract_pdf_tables_sync(file_path: str) -> List[Dict[str, Any]]:
    """Synchronous PDF extraction with multiple methods."""
    tables = []
    
    # Method 1: Try pdfplumber (fastest, good for simple tables)
    if PDF_PLUMBER_AVAILABLE:
        try:
            tables = extract_pdf_with_pdfplumber(file_path)
            if tables:
                return tables
        except Exception:
            pass
    
    # Method 2: Try camelot (best quality, slower)
    if CAMELOT_AVAILABLE:
        try:
            tables = extract_pdf_with_camelot(file_path)
            if tables:
                return tables
        except Exception:
            pass
    
    # Method 3: Try tabula (fallback)
    if TABULA_AVAILABLE:
        try:
            tables = extract_pdf_with_tabula(file_path)
            if tables:
                return tables
        except Exception:
            pass
    
    # If all methods failed, return empty
    if not tables:
        raise Exception(f"All PDF extraction methods failed for {file_path}")
    
    return tables


def extract_pdf_with_pdfplumber(file_path: str) -> List[Dict[str, Any]]:
    """Extract using pdfplumber (fast)."""
    tables = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_tables = page.extract_tables()
            
            for table_num, table in enumerate(page_tables, 1):
                if not table or len(table) < 2:
                    continue
                
                headers = [str(cell).strip() if cell else f"col_{i}" 
                          for i, cell in enumerate(table[0])]
                
                rows = []
                for row in table[1:]:
                    if any(cell for cell in row):
                        rows.append([str(cell).strip() if cell else "" 
                                   for cell in row])
                
                if rows:
                    records = []
                    for row in rows:
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
    
    return tables


def extract_pdf_with_camelot(file_path: str) -> List[Dict[str, Any]]:
    """Extract using camelot (best quality, requires ghostscript)."""
    tables = []
    
    # Try lattice mode first (for tables with lines)
    try:
        camelot_tables = camelot.read_pdf(file_path, flavor='lattice', pages='all')
    except:
        # Fallback to stream mode (for tables without lines)
        try:
            camelot_tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
        except:
            return []
    
    for idx, table in enumerate(camelot_tables, 1):
        df = table.df
        
        if df.empty:
            continue
        
        headers = [str(col).strip() for col in df.columns]
        records = df.to_dict('records')
        
        tables.append({
            'page': table.page,
            'table_number': idx,
            'columns': headers,
            'row_count': len(df),
            'data': records
        })
    
    return tables


def extract_pdf_with_tabula(file_path: str) -> List[Dict[str, Any]]:
    """Extract using tabula (fallback)."""
    tables = []
    
    try:
        dfs = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
        
        for idx, df in enumerate(dfs, 1):
            if df.empty:
                continue
            
            headers = [str(col).strip() for col in df.columns]
            records = df.to_dict('records')
            
            tables.append({
                'page': None,
                'table_number': idx,
                'columns': headers,
                'row_count': len(df),
                'data': records
            })
    except:
        return []
    
    return tables


async def extract_tables_async(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    """
    Extract tables from a file based on its type (async).
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_type == 'excel' or path.suffix.lower() in ['.xlsx', '.xls']:
        return await extract_excel_tables_async(file_path)
    elif file_type == 'pdf' or path.suffix.lower() == '.pdf':
        return await extract_pdf_tables_async(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


async def extract_multiple_files_concurrent(
    file_infos: List[Dict[str, Any]],
    max_concurrent: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract tables from multiple files concurrently.
    Returns dict mapping file_path to list of tables.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_with_limit(file_info):
        async with semaphore:
            try:
                tables = await extract_tables_async(
                    file_info['file_path'],
                    file_info['file_type']
                )
                return file_info['file_path'], tables
            except Exception as e:
                return file_info['file_path'], []
    
    tasks = [extract_with_limit(fi) for fi in file_infos]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Map results
    extracted_tables = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        file_path, tables = result
        extracted_tables[file_path] = tables
    
    return extracted_tables
