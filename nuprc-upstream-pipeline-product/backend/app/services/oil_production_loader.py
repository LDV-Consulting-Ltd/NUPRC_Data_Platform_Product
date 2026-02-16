# backend/app/services/oil_production_loader.py
"""
Optimized loader for oil production data.
Uses optimized extractor, then loads to bronze staging area.
"""
import pandas as pd
import json
from typing import List, Dict, Any
from sqlalchemy import text
from datetime import datetime
from pathlib import Path

from app.core.db import engine
from app.services.oil_production_extractor import extract_oil_production_fact


def load_oil_production_to_staging(
    file_path: str,
    file_url: str,
    file_hash: str,
    run_id: str,
    log_func
) -> int:
    """
    Extract oil production data using optimized extractor and load to bronze staging.
    Returns number of rows loaded to bronze.
    """
    import time
    start_time = time.time()
    try:
        # Extract using optimized extractor
        log_func(run_id, "INFO", f"Extracting oil data from {Path(file_path).name}...")
        fact_df = extract_oil_production_fact(file_path)
        extract_time = time.time() - start_time
        
        if fact_df.empty:
            log_func(run_id, "WARN", f"No data extracted from {file_path}")
            return 0
        
        log_func(run_id, "INFO", f"Extracted {len(fact_df)} rows in {extract_time:.1f}s from {Path(file_path).name}")
        
        # Clean key columns
        if "Liquid Type" in fact_df.columns:
            fact_df["Liquid Type"] = fact_df["Liquid Type"].astype(str).str.strip()
        
        if "TERMINAL/STREAM" in fact_df.columns:
            fact_df["TERMINAL/STREAM"] = fact_df["TERMINAL/STREAM"].astype(str).str.strip()
        
        # Drop unnamed columns
        unnamed_cols = [c for c in fact_df.columns if str(c).upper().startswith("UNNAMED")]
        if unnamed_cols:
            fact_df = fact_df.drop(columns=unnamed_cols)
        
        # Convert DataFrame to records for JSONB storage
        records = fact_df.to_dict('records')
        
        # Prepare bronze data structure
        raw_data = {
            'table_metadata': {
                'sheet_name': 'OPEC-PROD',  # Default sheet name for oil
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
                INSERT INTO bronze.oil_production_status_raw
                (source_id, source_url, file_url, file_sha256, report_period, raw_data)
                VALUES (:source_id, :source_url, :file_url, :file_hash, :report_period, :raw_data::jsonb)
            """), {
                'source_id': 'oil_production_status',
                'source_url': file_url,
                'file_url': file_url,
                'file_hash': file_hash,
                'report_period': report_period,
                'raw_data': json.dumps(raw_data)
            })
        
        load_time = time.time() - start_time
        log_func(run_id, "INFO", f"Loaded {len(fact_df)} rows to bronze in {load_time:.1f}s total ({len(fact_df)/load_time:.0f} rows/sec)")
        
        # Update catalog (but don't refresh every time - batch refresh is faster)
        try:
            from app.models.data_catalog import update_file_processing_status
            update_file_processing_status(
                file_sha256=file_hash,
                bronze_loaded=True,
                bronze_table='bronze.oil_production_status_raw',
                bronze_rows=len(fact_df),
                processed_at=None  # Will use current timestamp
            )
            # Don't refresh catalog here - let batch refresh handle it
        except Exception:
            pass
        
        return len(fact_df)
            
    except Exception as e:
        log_func(run_id, "ERROR", f"Failed to load oil production to staging from {file_path}: {str(e)}")
        import traceback
        log_func(run_id, "ERROR", traceback.format_exc())
        return 0


def extract_report_period(file_url: str):
    """Extract report period from filename."""
    import re
    from dateutil import parser as date_parser
    
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
        r'(\d{4}/\d{2}/\d{2})',  # YYYY/MM/DD
        r'(\w+\s+\d{4})',        # Month YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, file_url)
        if match:
            try:
                return date_parser.parse(match.group(1), fuzzy=True).date()
            except:
                pass
    
    return None
