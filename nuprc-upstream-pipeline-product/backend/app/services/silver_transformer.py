# backend/app/services/silver_transformer.py
"""
Transform bronze data to silver layer with cleaning and standardization.
"""
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from datetime import datetime

from app.core.db import engine
from app.services.fuzzy_matcher import standardize_columns, find_canonical_match


def transform_bronze_to_silver(run_id: str, log_func):
    """
    Transform all bronze tables to silver layer.
    Reads from bronze, cleans data, standardizes columns, writes to silver.
    All sources now go through bronze staging (optimized extractors load to bronze first).
    """
    import time
    start_time = time.time()
    log_func(run_id, "INFO", "Starting silver transformation...")
    
    sources = [
        'concession_situation',
        'oil_production_status',  # Will check if bronze data exists
        'gas_production_status',
        'rig_disposition'
    ]
    
    total_transformed = 0
    
    for source_id in sources:
        try:
            # Skip sources that are loaded directly to warehouse (check if bronze data exists)
            from app.core.db import engine
            with engine.connect() as cxn:
                from sqlalchemy import text
                bronze_table = f"bronze.{source_id}_raw"
                try:
                    count = cxn.execute(text(f"""
                        SELECT COUNT(*) FROM {bronze_table}
                    """)).scalar() or 0
                except Exception:
                    count = 0
                
                if count == 0:
                    log_func(run_id, "INFO", f"Skipping {source_id} - no bronze data found")
                    continue
            
            log_func(run_id, "INFO", f"Transforming {source_id} to silver...")
            rows = transform_source_to_silver(source_id, run_id, log_func)
            total_transformed += rows
            log_func(run_id, "INFO", f"Transformed {rows} rows from {source_id}")
        except Exception as e:
            log_func(run_id, "ERROR", f"Failed to transform {source_id}: {str(e)}")
            continue
    
    elapsed = time.time() - start_time
    log_func(run_id, "INFO", f"Silver transformation completed: {total_transformed} rows in {elapsed:.2f}s")


def transform_source_to_silver(source_id: str, run_id: str, log_func) -> int:
    """
    Transform a single source from bronze to silver.
    Returns number of rows transformed.
    """
    bronze_table = f"bronze.{source_id}_raw"
    silver_table = f"silver.{source_id}_cleaned"
    
    # Create silver table if it doesn't exist
    create_silver_table(silver_table, source_id)
    
    with engine.connect() as cxn:
        # Read all bronze records
        bronze_records = cxn.execute(text(f"""
            SELECT id, source_id, file_url, file_sha256, report_period, raw_data, extracted_at
            FROM {bronze_table}
            ORDER BY extracted_at DESC
        """)).mappings().all()
        
        transformed_count = 0
        
        for bronze_record in bronze_records:
            file_rows_count = 0
            try:
                raw_data = bronze_record['raw_data']
                if not raw_data:
                    continue
                
                # Extract tables from JSONB
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                table_metadata = raw_data.get('table_metadata', {})
                tables_data = raw_data.get('data', [])
                
                if not tables_data:
                    continue
                
                # Check if data came from optimized extractor (already transformed)
                extraction_method = table_metadata.get('extraction_method', '')
                is_optimized = extraction_method == 'optimized_extractor'
                
                if is_optimized:
                    # Data is already transformed by optimized extractor - minimal processing needed
                    # Just map the already-clean columns directly
                    columns = table_metadata.get('columns', [])
                    # Create simple mapping (column name to itself, with normalization)
                    column_mapping = {col: col.lower().replace(' ', '_').replace('/', '_') for col in columns}
                else:
                    # Standard extraction - use fuzzy matching
                    columns = table_metadata.get('columns', [])
                    column_mapping = standardize_columns(columns, source_id)
                
                # Transform each row
                for row_data in tables_data:
                    if is_optimized:
                        # For optimized data, minimal cleaning - just normalize column names
                        cleaned_row = clean_optimized_row(
                            row_data,
                            column_mapping,
                            source_id,
                            bronze_record
                        )
                    else:
                        # For standard extraction, full cleaning pipeline
                        cleaned_row = clean_and_standardize_row(
                            row_data,
                            column_mapping,
                            source_id,
                            bronze_record
                        )
                    
                    if cleaned_row:
                        # Insert into silver table
                        insert_cleaned_row(silver_table, cleaned_row, bronze_record)
                        transformed_count += 1
                        file_rows_count += 1
                
                # Update catalog after processing all rows from this bronze file
                if file_rows_count > 0 and bronze_record.get('file_sha256'):
                    try:
                        from app.models.data_catalog import update_file_processing_status
                        update_file_processing_status(
                            file_sha256=bronze_record.get('file_sha256'),
                            silver_loaded=True,
                            silver_table=silver_table,
                            silver_rows=file_rows_count
                        )
                    except Exception:
                        pass  # Don't fail if catalog update fails
                        
            except Exception as e:
                log_func(run_id, "WARN", f"Failed to transform bronze record {bronze_record.get('id')}: {str(e)}")
                continue
    
    return transformed_count


def create_silver_table(table_name: str, source_id: str):
    """Create silver table for a source if it doesn't exist."""
    with engine.begin() as cxn:
        # Check if table exists
        result = cxn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = :schema AND table_name = :table
            )
        """), {
            'schema': table_name.split('.')[0],
            'table': table_name.split('.')[1]
        })
        
        if result.scalar():
            return  # Table already exists
        
        cxn.execute(text(f"""
            CREATE TABLE {table_name} (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                bronze_id BIGINT,
                source_id TEXT NOT NULL,
                file_url TEXT,
                report_period DATE,
                -- Standardized columns (will vary by source)
                operator_name TEXT,
                operator_code TEXT,
                asset_name TEXT,
                asset_type TEXT,
                production_volume NUMERIC(18,2),
                production_unit TEXT,
                report_date DATE,
                report_month INTEGER,
                report_year INTEGER,
                rig_name TEXT,
                rig_status TEXT,
                activity_type TEXT,
                concession_status TEXT,
                concession_type TEXT,
                -- Raw cleaned data as JSONB for flexibility
                cleaned_data JSONB,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """))


def clean_optimized_row(
    row_data: Dict[str, Any],
    column_mapping: Dict[str, str],
    source_id: str,
    bronze_record: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Clean row from optimized extractor (data is already transformed).
    Minimal processing - just normalize column names and handle nulls.
    """
    cleaned = {
        'bronze_id': bronze_record.get('id'),
        'source_id': source_id,
        'file_url': bronze_record.get('file_url'),
        'report_period': bronze_record.get('report_period'),
    }
    
    # Map columns with minimal transformation (data is already clean)
    for original_col, value in row_data.items():
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        
        canonical_col = column_mapping.get(original_col, original_col.lower().replace(' ', '_').replace('/', '_'))
        
        # Minimal cleaning - just ensure proper types
        if isinstance(value, (int, float)):
            cleaned[canonical_col] = value
        elif isinstance(value, str):
            cleaned[canonical_col] = value.strip()
        else:
            cleaned[canonical_col] = value
    
    # Store original data as JSONB for reference
    cleaned['cleaned_data'] = json.dumps(row_data)
    
    return cleaned


def clean_and_standardize_row(
    row_data: Dict[str, Any],
    column_mapping: Dict[str, str],
    source_id: str,
    bronze_record: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Clean and standardize a single row of data.
    Returns cleaned row dict or None if row should be skipped.
    """
    cleaned = {
        'bronze_id': bronze_record.get('id'),
        'source_id': source_id,
        'file_url': bronze_record.get('file_url'),
        'report_period': bronze_record.get('report_period'),
    }
    
    # Map original columns to canonical names
    for original_col, value in row_data.items():
        if value is None or value == '':
            continue
        
        canonical_col = column_mapping.get(original_col, original_col.lower().replace(' ', '_'))
        
        # Clean the value based on canonical column type
        cleaned_value = clean_value(value, canonical_col)
        
        if cleaned_value is not None:
            cleaned[canonical_col] = cleaned_value
    
    # Store original data as JSONB for reference
    cleaned['cleaned_data'] = json.dumps(row_data)
    
    return cleaned


def clean_value(value: Any, column_name: str) -> Any:
    """
    Clean a value based on its column name.
    Handles type conversion, normalization, etc.
    """
    if value is None:
        return None
    
    # Convert to string for processing
    str_value = str(value).strip()
    
    if not str_value or str_value.lower() in ['n/a', 'na', 'null', 'none', '-']:
        return None
    
    # Numeric columns
    if 'volume' in column_name or 'quantity' in column_name or 'qty' in column_name:
        try:
            # Remove commas, spaces, and other formatting
            cleaned = str_value.replace(',', '').replace(' ', '').replace('$', '')
            return float(cleaned)
        except:
            return None
    
    # Date columns
    if 'date' in column_name or 'period' in column_name:
        try:
            from dateutil import parser as date_parser
            return date_parser.parse(str_value, fuzzy=True).date()
        except:
            return None
    
    # Year extraction
    if 'year' in column_name:
        try:
            import re
            year_match = re.search(r'\d{4}', str_value)
            if year_match:
                return int(year_match.group())
        except:
            pass
    
    # Month extraction
    if 'month' in column_name:
        try:
            from dateutil import parser as date_parser
            parsed = date_parser.parse(str_value, fuzzy=True)
            return parsed.month
        except:
            pass
    
    # Text columns - normalize
    if isinstance(str_value, str):
        # Remove extra whitespace
        str_value = ' '.join(str_value.split())
        # Title case for names
        if 'name' in column_name or 'operator' in column_name or 'asset' in column_name:
            str_value = str_value.title()
        return str_value
    
    return value


def insert_cleaned_row(silver_table: str, cleaned_row: Dict[str, Any], bronze_record: Dict[str, Any]):
    """Insert a cleaned row into the silver table."""
    with engine.begin() as cxn:
        # Build dynamic INSERT based on available columns
        columns = list(cleaned_row.keys())
        placeholders = [f":{col}" for col in columns]
        
        insert_sql = f"""
            INSERT INTO {silver_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        # Convert cleaned_data to JSONB if present
        params = cleaned_row.copy()
        if 'cleaned_data' in params and isinstance(params['cleaned_data'], str):
            params['cleaned_data'] = json.loads(params['cleaned_data'])
        
        cxn.execute(text(insert_sql), params)
