# backend/app/services/warehouse_loader.py
"""
Load warehouse dimensional model from silver/bronze data.
"""
from typing import Dict, Any, Optional
from sqlalchemy import text
from datetime import datetime

from app.core.db import engine


def populate_dimensions(run_id: str, log_func):
    """
    Populate dimension tables (dim_operator, dim_asset) from bronze/silver data.
    """
    log_func(run_id, "INFO", "Populating dimension tables...")
    
    # Populate operators
    populate_operators(run_id, log_func)
    
    # Populate assets
    populate_assets(run_id, log_func)
    
    log_func(run_id, "INFO", "Dimension tables populated")


def populate_operators(run_id: str, log_func):
    """Extract and populate dim_operator from bronze/silver data."""
    with engine.connect() as cxn:
        # Extract operators from all bronze tables
        operators = set()
        
        # Try to extract from silver tables first (cleaner data)
        silver_tables = [
            'silver.concession_situation_cleaned',
            'silver.oil_production_status_cleaned',
            'silver.gas_production_status_cleaned',
            'silver.rig_disposition_cleaned'
        ]
        
        for table in silver_tables:
            try:
                rows = cxn.execute(text(f"""
                    SELECT DISTINCT operator_name, operator_code
                    FROM {table}
                    WHERE operator_name IS NOT NULL AND operator_name != ''
                """)).mappings().all()
                
                for row in rows:
                    if row['operator_name']:
                        operators.add((
                            row['operator_name'].strip(),
                            row['operator_code'].strip() if row['operator_code'] else None
                        ))
            except Exception as e:
                # Table might not exist or column might not be present
                continue
        
        # Also try bronze tables as fallback
        bronze_tables = [
            'bronze.concession_situation_raw',
            'bronze.oil_production_status_raw',
            'bronze.gas_production_status_raw',
            'bronze.rig_disposition_raw'
        ]
        
        for table in bronze_tables:
            try:
                rows = cxn.execute(text(f"""
                    SELECT raw_data
                    FROM {table}
                """)).mappings().all()
                
                for row in rows:
                    raw_data = row['raw_data']
                    if not raw_data:
                        continue
                    
                    # Extract operator names from JSONB data
                    if isinstance(raw_data, dict):
                        data_rows = raw_data.get('data', [])
                        for data_row in data_rows:
                            # Look for operator-related fields
                            for key, value in data_row.items():
                                if 'operator' in key.lower() or 'company' in key.lower():
                                    if value and str(value).strip():
                                        operators.add((str(value).strip().title(), None))
            except Exception as e:
                continue
        
        # Insert operators into dim_operator
        inserted = 0
        with engine.begin() as cxn:
            for op_name, op_code in operators:
                try:
                    cxn.execute(text("""
                        INSERT INTO warehouse.dim_operator (operator_name, operator_code)
                        VALUES (:name, :code)
                        ON CONFLICT (operator_name) DO UPDATE SET
                            operator_code = COALESCE(EXCLUDED.operator_code, warehouse.dim_operator.operator_code),
                            updated_at = now()
                    """), {'name': op_name, 'code': op_code})
                    inserted += 1
                except Exception as e:
                    continue
        
        log_func(run_id, "INFO", f"Populated {inserted} operators")


def populate_assets(run_id: str, log_func):
    """Extract and populate dim_asset from bronze/silver data."""
    with engine.connect() as cxn:
        assets = set()
        
        # Extract from silver tables
        silver_tables = [
            'silver.concession_situation_cleaned',
            'silver.oil_production_status_cleaned',
            'silver.gas_production_status_cleaned',
            'silver.rig_disposition_cleaned'
        ]
        
        for table in silver_tables:
            try:
                rows = cxn.execute(text(f"""
                    SELECT DISTINCT asset_name, asset_type
                    FROM {table}
                    WHERE asset_name IS NOT NULL AND asset_name != ''
                """)).mappings().all()
                
                for row in rows:
                    if row['asset_name']:
                        assets.add((
                            row['asset_name'].strip(),
                            row['asset_type'].strip() if row['asset_type'] else None,
                            None,  # block_name
                            None   # field_name
                        ))
            except Exception as e:
                continue
        
        # Insert assets into dim_asset
        inserted = 0
        with engine.begin() as cxn:
            for asset_name, asset_type, block_name, field_name in assets:
                try:
                    cxn.execute(text("""
                        INSERT INTO warehouse.dim_asset (asset_name, asset_type, block_name, field_name)
                        VALUES (:name, :type, :block, :field)
                        ON CONFLICT DO NOTHING
                    """), {
                        'name': asset_name,
                        'type': asset_type,
                        'block': block_name,
                        'field': field_name
                    })
                    inserted += 1
                except Exception as e:
                    continue
        
        log_func(run_id, "INFO", f"Populated {inserted} assets")


def populate_fact_tables(run_id: str, log_func):
    """
    Populate warehouse fact tables from silver data.
    """
    log_func(run_id, "INFO", "Populating warehouse fact tables...")
    
    # Populate oil production facts
    populate_oil_production_facts(run_id, log_func)
    
    # Populate gas production facts
    populate_gas_production_facts(run_id, log_func)
    
    # Populate rig activity facts
    populate_rig_activity_facts(run_id, log_func)
    
    # Populate concession status facts
    populate_concession_status_facts(run_id, log_func)
    
    log_func(run_id, "INFO", "Warehouse fact tables populated")


def populate_oil_production_facts(run_id: str, log_func):
    """Populate fact_oil_production from silver data."""
    silver_table = 'silver.oil_production_status_cleaned'
    
    try:
        with engine.begin() as cxn:
            # Check if silver table exists
            try:
                result = cxn.execute(text(f"""
                    SELECT COUNT(*) FROM {silver_table}
                """))
                row_count = result.scalar() or 0
            except Exception:
                log_func(run_id, "WARN", f"Silver table {silver_table} does not exist yet")
                return
            
            if row_count == 0:
                log_func(run_id, "WARN", "No oil production data in silver layer")
                return
            
            # Insert facts - handle missing columns gracefully
            cxn.execute(text(f"""
                INSERT INTO warehouse.fact_oil_production
                (date_key, operator_key, asset_key, production_volume, production_unit, report_period, source_id)
                SELECT
                    TO_CHAR(COALESCE(s.report_date, s.report_period, CURRENT_DATE), 'YYYYMMDD')::INTEGER as date_key,
                    op.operator_key,
                    ast.asset_key,
                    s.production_volume,
                    s.production_unit,
                    COALESCE(s.report_period, s.report_date) as report_period,
                    s.source_id
                FROM {silver_table} s
                LEFT JOIN warehouse.dim_operator op ON op.operator_name = s.operator_name
                LEFT JOIN warehouse.dim_asset ast ON ast.asset_name = s.asset_name
                WHERE s.production_volume IS NOT NULL
                ON CONFLICT DO NOTHING
            """))
            
            count = cxn.execute(text("SELECT COUNT(*) FROM warehouse.fact_oil_production")).scalar()
            log_func(run_id, "INFO", f"Populated {count} oil production facts")
            
            # Update catalog for all files that contributed to this fact table
            try:
                from app.models.data_catalog import update_file_processing_status
                # Get file hashes from bronze table via bronze_id
                bronze_table = 'bronze.oil_production_status_raw'
                file_hashes = cxn.execute(text(f"""
                    SELECT DISTINCT b.file_sha256 
                    FROM {silver_table} s
                    JOIN {bronze_table} b ON s.bronze_id = b.id
                    WHERE b.file_sha256 IS NOT NULL
                """)).scalars().all()
                
                for file_hash in file_hashes:
                    update_file_processing_status(
                        file_sha256=file_hash,
                        warehouse_loaded=True,
                        warehouse_tables=['warehouse.fact_oil_production', 'warehouse.dim_operator', 'warehouse.dim_asset', 'warehouse.dim_date'],
                        warehouse_rows=count  # Total count, not per-file
                    )
            except Exception:
                pass
            
    except Exception as e:
        log_func(run_id, "WARN", f"Failed to populate oil production facts: {str(e)}")


def populate_gas_production_facts(run_id: str, log_func):
    """Populate fact_gas_production from silver data."""
    silver_table = 'silver.gas_production_status_cleaned'
    
    try:
        with engine.begin() as cxn:
            try:
                result = cxn.execute(text(f"""
                    SELECT COUNT(*) FROM {silver_table}
                """))
                row_count = result.scalar() or 0
            except Exception:
                log_func(run_id, "WARN", f"Silver table {silver_table} does not exist yet")
                return
            
            if row_count == 0:
                log_func(run_id, "WARN", "No gas production data in silver layer")
                return
            
            cxn.execute(text(f"""
                INSERT INTO warehouse.fact_gas_production
                (date_key, operator_key, asset_key, production_volume, production_unit, report_period, source_id)
                SELECT
                    TO_CHAR(COALESCE(s.report_date, s.report_period, CURRENT_DATE), 'YYYYMMDD')::INTEGER as date_key,
                    op.operator_key,
                    ast.asset_key,
                    s.production_volume,
                    s.production_unit,
                    COALESCE(s.report_period, s.report_date) as report_period,
                    s.source_id
                FROM {silver_table} s
                LEFT JOIN warehouse.dim_operator op ON op.operator_name = s.operator_name
                LEFT JOIN warehouse.dim_asset ast ON ast.asset_name = s.asset_name
                WHERE s.production_volume IS NOT NULL
                ON CONFLICT DO NOTHING
            """))
            
            count = cxn.execute(text("SELECT COUNT(*) FROM warehouse.fact_gas_production")).scalar()
            log_func(run_id, "INFO", f"Populated {count} gas production facts")
            
            # Update catalog
            try:
                from app.models.data_catalog import update_file_processing_status
                bronze_table = 'bronze.gas_production_status_raw'
                file_hashes = cxn.execute(text(f"""
                    SELECT DISTINCT b.file_sha256 
                    FROM {silver_table} s
                    JOIN {bronze_table} b ON s.bronze_id = b.id
                    WHERE b.file_sha256 IS NOT NULL
                """)).scalars().all()
                
                for file_hash in file_hashes:
                    update_file_processing_status(
                        file_sha256=file_hash,
                        warehouse_loaded=True,
                        warehouse_tables=['warehouse.fact_gas_production', 'warehouse.dim_operator', 'warehouse.dim_asset', 'warehouse.dim_date'],
                        warehouse_rows=count
                    )
            except Exception:
                pass
            
    except Exception as e:
        log_func(run_id, "WARN", f"Failed to populate gas production facts: {str(e)}")


def populate_rig_activity_facts(run_id: str, log_func):
    """Populate fact_rig_activity from silver data."""
    silver_table = 'silver.rig_disposition_cleaned'
    
    try:
        with engine.begin() as cxn:
            try:
                result = cxn.execute(text(f"""
                    SELECT COUNT(*) FROM {silver_table}
                """))
                row_count = result.scalar() or 0
            except Exception:
                log_func(run_id, "WARN", f"Silver table {silver_table} does not exist yet")
                return
            
            if row_count == 0:
                log_func(run_id, "WARN", "No rig activity data in silver layer")
                return
            
            cxn.execute(text(f"""
                INSERT INTO warehouse.fact_rig_activity
                (date_key, operator_key, asset_key, rig_name, rig_status, activity_type, report_period, source_id)
                SELECT
                    TO_CHAR(COALESCE(s.report_date, s.report_period, CURRENT_DATE), 'YYYYMMDD')::INTEGER as date_key,
                    op.operator_key,
                    ast.asset_key,
                    s.rig_name,
                    s.rig_status,
                    s.activity_type,
                    COALESCE(s.report_period, s.report_date) as report_period,
                    s.source_id
                FROM {silver_table} s
                LEFT JOIN warehouse.dim_operator op ON op.operator_name = s.operator_name
                LEFT JOIN warehouse.dim_asset ast ON ast.asset_name = s.asset_name
                WHERE s.rig_name IS NOT NULL OR s.rig_status IS NOT NULL
                ON CONFLICT DO NOTHING
            """))
            
            count = cxn.execute(text("SELECT COUNT(*) FROM warehouse.fact_rig_activity")).scalar()
            log_func(run_id, "INFO", f"Populated {count} rig activity facts")
            
    except Exception as e:
        log_func(run_id, "WARN", f"Failed to populate rig activity facts: {str(e)}")


def populate_concession_status_facts(run_id: str, log_func):
    """Populate fact_concession_status from silver data."""
    silver_table = 'silver.concession_situation_cleaned'
    
    try:
        with engine.begin() as cxn:
            try:
                result = cxn.execute(text(f"""
                    SELECT COUNT(*) FROM {silver_table}
                """))
                row_count = result.scalar() or 0
            except Exception:
                log_func(run_id, "WARN", f"Silver table {silver_table} does not exist yet")
                return
            
            if row_count == 0:
                log_func(run_id, "WARN", "No concession status data in silver layer")
                return
            
            cxn.execute(text(f"""
                INSERT INTO warehouse.fact_concession_status
                (date_key, operator_key, asset_key, concession_status, concession_type, report_period, source_id)
                SELECT
                    TO_CHAR(COALESCE(s.report_date, s.report_period, CURRENT_DATE), 'YYYYMMDD')::INTEGER as date_key,
                    op.operator_key,
                    ast.asset_key,
                    s.concession_status,
                    s.concession_type,
                    COALESCE(s.report_period, s.report_date) as report_period,
                    s.source_id
                FROM {silver_table} s
                LEFT JOIN warehouse.dim_operator op ON op.operator_name = s.operator_name
                LEFT JOIN warehouse.dim_asset ast ON ast.asset_name = s.asset_name
                WHERE s.concession_status IS NOT NULL OR s.concession_type IS NOT NULL
                ON CONFLICT DO NOTHING
            """))
            
            count = cxn.execute(text("SELECT COUNT(*) FROM warehouse.fact_concession_status")).scalar()
            log_func(run_id, "INFO", f"Populated {count} concession status facts")
            
            # Update catalog
            try:
                from app.models.data_catalog import update_file_processing_status
                bronze_table = 'bronze.concession_situation_raw'
                file_hashes = cxn.execute(text(f"""
                    SELECT DISTINCT b.file_sha256 
                    FROM {silver_table} s
                    JOIN {bronze_table} b ON s.bronze_id = b.id
                    WHERE b.file_sha256 IS NOT NULL
                """)).scalars().all()
                
                for file_hash in file_hashes:
                    update_file_processing_status(
                        file_sha256=file_hash,
                        warehouse_loaded=True,
                        warehouse_tables=['warehouse.fact_concession_status', 'warehouse.dim_operator', 'warehouse.dim_asset', 'warehouse.dim_date'],
                        warehouse_rows=count
                    )
            except Exception:
                pass
            
    except Exception as e:
        log_func(run_id, "WARN", f"Failed to populate concession status facts: {str(e)}")
