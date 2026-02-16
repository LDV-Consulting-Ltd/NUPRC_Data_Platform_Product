# backend/app/services/bronze_loader.py
"""
Load extracted data into bronze layer tables.
"""
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text

from app.core.db import engine
from app.services.sources import SourceConfig


def load_to_bronze(
    source: SourceConfig,
    file_url: str,
    file_path: str,
    file_hash: str,
    tables: List[Dict[str, Any]],
    run_id: str
) -> int:
    """
    Load extracted tables into the bronze table for a source.
    Returns number of rows loaded.
    Optimized with bulk insert for better performance.
    """
    total_rows = 0
    
    # Try to extract report period from filename or metadata
    report_period = extract_report_period(file_url)
    
    if not tables:
        return 0
    
    # Prepare all inserts for bulk operation
    insert_values = []
    for table in tables:
        # Store each table as JSONB in raw_data
        raw_data = {
            'table_metadata': {
                'sheet_name': table.get('sheet_name'),
                'page': table.get('page'),
                'table_number': table.get('table_number'),
                'columns': table.get('columns', []),
                'row_count': table.get('row_count', 0)
            },
            'data': table.get('data', [])
        }
        
        insert_values.append({
            'source_id': source.source_id,
            'source_url': source.base_url,
            'file_url': file_url,
            'file_hash': file_hash,
            'report_period': report_period,
            'raw_data': json.dumps(raw_data)
        })
        
        total_rows += table.get('row_count', 0)
    
    # Bulk insert all tables at once for better performance
    # All inserts happen in one transaction (faster than multiple transactions)
    with engine.begin() as cxn:
        insert_sql = f"""
            INSERT INTO {source.bronze_table}
            (source_id, source_url, file_url, file_sha256, report_period, raw_data)
            VALUES (:source_id, :source_url, :file_url, :file_hash, :report_period, :raw_data::jsonb)
        """
        
        # Execute all inserts in one transaction
        # SQLAlchemy will handle the list of dictionaries
        for values in insert_values:
            cxn.execute(text(insert_sql), values)
    
    # Update catalog
    try:
        from app.models.data_catalog import update_file_processing_status
        update_file_processing_status(
            file_sha256=file_hash,
            bronze_loaded=True,
            bronze_table=source.bronze_table,
            bronze_rows=total_rows,
            processed_at=None  # Will use current timestamp
        )
    except Exception:
        pass  # Don't fail if catalog update fails
    
    return total_rows


def extract_report_period(file_url: str) -> Any:
    """
    Try to extract report period (date) from filename or URL.
    Returns date or None.
    """
    import re
    from dateutil import parser as date_parser
    
    # Look for date patterns in filename
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
