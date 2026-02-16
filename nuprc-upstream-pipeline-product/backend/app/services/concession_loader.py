# backend/app/services/concession_loader.py
"""
Optimized loader for concession situation data.
Uses optimized extractor, then loads to bronze staging area.
"""
import pandas as pd
import json
from typing import List, Dict, Any
from sqlalchemy import text
from datetime import datetime
from pathlib import Path

from app.core.db import engine
from app.services.concession_extractor import extract_concession_fact


def load_concession_to_staging(
    file_path: str,
    file_url: str,
    file_hash: str,
    run_id: str,
    log_func
) -> int:
    """
    Extract concession data using optimized extractor and load to bronze staging.
    Returns number of rows loaded to bronze.
    """
    try:
        # Extract using optimized extractor
        fact_df = extract_concession_fact(file_path)
        
        if fact_df.empty:
            log_func(run_id, "WARN", f"No data extracted from {file_path}")
            return 0
        
        log_func(run_id, "INFO", f"Extracted {len(fact_df)} fact rows from {file_path}")
        
        # Convert DataFrame to records for JSONB storage
        records = fact_df.to_dict('records')
        
        # Prepare bronze data structure
        raw_data = {
            'table_metadata': {
                'sheet_name': 'pdf_tables',  # Concession is from PDF
                'columns': list(fact_df.columns),
                'row_count': len(fact_df),
                'extraction_method': 'optimized_extractor'
            },
            'data': records
        }
        
        # Extract report period from filename
        report_period = extract_report_period(file_url)
        
        # Load to bronze staging
        with engine.begin() as cxn:
            cxn.execute(text("""
                INSERT INTO bronze.concession_situation_raw
                (source_id, source_url, file_url, file_sha256, report_period, raw_data)
                VALUES (:source_id, :source_url, :file_url, :file_hash, :report_period, :raw_data::jsonb)
            """), {
                'source_id': 'concession_situation',
                'source_url': file_url,
                'file_url': file_url,
                'file_hash': file_hash,
                'report_period': report_period,
                'raw_data': json.dumps(raw_data)
            })
        
        log_func(run_id, "INFO", f"Loaded {len(fact_df)} rows to bronze staging")
        
        # Update catalog
        try:
            from app.models.data_catalog import update_file_processing_status, refresh_available_tables
            update_file_processing_status(
                file_sha256=file_hash,
                bronze_loaded=True,
                bronze_table='bronze.concession_situation_raw',
                bronze_rows=len(fact_df),
                processed_at=None
            )
            refresh_available_tables()
        except Exception:
            pass
        
        return len(fact_df)
            
    except Exception as e:
        log_func(run_id, "ERROR", f"Failed to load concession to staging from {file_path}: {str(e)}")
        import traceback
        log_func(run_id, "ERROR", traceback.format_exc())
        return 0


def extract_report_period(file_url: str):
    """Extract report period from filename."""
    import re
    from dateutil import parser as date_parser
    
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{4}/\d{2}/\d{2})',
        r'(\w+\s+\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, file_url)
        if match:
            try:
                return date_parser.parse(match.group(1), fuzzy=True).date()
            except:
                pass
    
    return None
