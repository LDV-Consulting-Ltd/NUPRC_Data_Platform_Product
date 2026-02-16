# backend/app/models/data_catalog.py
"""
Central data catalog to track all downloaded files and available tables.
This provides a unified view of all data in the system.
"""
from sqlalchemy import text
from app.core.db import engine


def init_data_catalog():
    """Create data catalog tables for tracking all downloads and tables."""
    with engine.begin() as cxn:
        # Create data_catalog schema
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS data_catalog;"))
        # Main catalog table - tracks all downloaded files
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS data_catalog.downloaded_files (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            file_url TEXT NOT NULL,
            file_path TEXT,
            filename TEXT NOT NULL,
            file_sha256 TEXT NOT NULL,
            file_type TEXT,  -- 'excel', 'pdf', etc.
            file_size BIGINT,
            report_period DATE,
            download_status TEXT NOT NULL,  -- 'downloaded', 'failed', 'duplicate'
            downloaded_at TIMESTAMPTZ DEFAULT now(),
            processed_at TIMESTAMPTZ,
            run_id TEXT,
            -- Processing status
            bronze_loaded BOOLEAN DEFAULT FALSE,
            bronze_table TEXT,
            bronze_rows BIGINT DEFAULT 0,
            silver_loaded BOOLEAN DEFAULT FALSE,
            silver_table TEXT,
            silver_rows BIGINT DEFAULT 0,
            warehouse_loaded BOOLEAN DEFAULT FALSE,
            warehouse_tables TEXT[],  -- Array of warehouse tables this file contributed to
            warehouse_rows BIGINT DEFAULT 0,
            -- Metadata
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(file_sha256)
        );
        """))
        
        # Create indexes for fast queries
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_catalog_source_id 
        ON data_catalog.downloaded_files(source_id);
        """))
        
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_catalog_sha256 
        ON data_catalog.downloaded_files(file_sha256);
        """))
        
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_catalog_downloaded_at 
        ON data_catalog.downloaded_files(downloaded_at DESC);
        """))
        
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_catalog_status 
        ON data_catalog.downloaded_files(downloaded_at DESC, download_status);
        """))
        
        # Available tables catalog - tracks all tables in the system
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS data_catalog.available_tables (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            schema_name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            full_name TEXT NOT NULL,  -- schema.table
            table_type TEXT NOT NULL,  -- 'bronze', 'silver', 'warehouse', 'catalog'
            source_id TEXT,  -- Which source this table belongs to (if applicable)
            description TEXT,
            row_count BIGINT DEFAULT 0,
            last_updated TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(full_name)
        );
        """))
        
        # Create index
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_tables_type 
        ON data_catalog.available_tables(table_type, source_id);
        """))
        
        # Refresh function to populate available_tables from actual database tables
        cxn.execute(text("""
        CREATE OR REPLACE FUNCTION data_catalog.refresh_available_tables()
        RETURNS void AS $$
        BEGIN
            -- Clear existing entries
            DELETE FROM data_catalog.available_tables;
            
            -- Insert all tables from information_schema
            INSERT INTO data_catalog.available_tables (schema_name, table_name, full_name, table_type, source_id, row_count, last_updated)
            SELECT 
                table_schema,
                table_name,
                table_schema || '.' || table_name as full_name,
                CASE 
                    WHEN table_schema = 'bronze' THEN 'bronze'
                    WHEN table_schema = 'silver' THEN 'silver'
                    WHEN table_schema = 'warehouse' THEN 'warehouse'
                    WHEN table_schema = 'data_catalog' THEN 'catalog'
                    ELSE 'other'
                END as table_type,
                CASE 
                    WHEN table_name LIKE '%concession%' THEN 'concession_situation'
                    WHEN table_name LIKE '%oil%' THEN 'oil_production_status'
                    WHEN table_name LIKE '%gas%' THEN 'gas_production_status'
                    WHEN table_name LIKE '%rig%' THEN 'rig_disposition'
                    ELSE NULL
                END as source_id,
                0 as row_count,  -- Will be updated separately
                now() as last_updated
            FROM information_schema.tables
            WHERE table_schema IN ('bronze', 'silver', 'warehouse', 'data_catalog')
            AND table_type = 'BASE TABLE';
            
            -- Update row counts
            UPDATE data_catalog.available_tables t
            SET row_count = (
                SELECT COUNT(*) 
                FROM information_schema.tables ist
                WHERE ist.table_schema = t.schema_name 
                AND ist.table_name = t.table_name
            );
        END;
        $$ LANGUAGE plpgsql;
        """))


def register_downloaded_file(
    source_id: str,
    source_name: str,
    file_url: str,
    file_path: str,
    filename: str,
    file_sha256: str,
    file_type: str,
    file_size: int = None,
    report_period: str = None,
    download_status: str = 'downloaded',
    run_id: str = None
):
    """
    Register a downloaded file in the catalog IMMEDIATELY.
    This is called synchronously during download to ensure catalog is populated within 2-3 minutes.
    Optimized for speed - single INSERT with ON CONFLICT for fast execution.
    """
    with engine.begin() as cxn:
        # Fast single INSERT with conflict handling - no separate SELECT needed
        cxn.execute(text("""
        INSERT INTO data_catalog.downloaded_files 
        (source_id, source_name, file_url, file_path, filename, file_sha256, 
         file_type, file_size, report_period, download_status, run_id)
        VALUES (:source_id, :source_name, :file_url, :file_path, :filename, 
                :file_sha256, :file_type, :file_size, 
                CASE WHEN :report_period = '' OR :report_period IS NULL THEN NULL ELSE :report_period::date END, 
                :download_status, :run_id)
        ON CONFLICT (file_sha256) DO UPDATE SET
            updated_at = now(),
            download_status = EXCLUDED.download_status,
            file_path = COALESCE(EXCLUDED.file_path, data_catalog.downloaded_files.file_path),
            run_id = COALESCE(EXCLUDED.run_id, data_catalog.downloaded_files.run_id)
        """), {
            'source_id': source_id,
            'source_name': source_name,
            'file_url': file_url,
            'file_path': file_path,
            'filename': filename,
            'file_sha256': file_sha256,
            'file_type': file_type,
            'file_size': file_size,
            'report_period': report_period or '',
            'download_status': download_status,
            'run_id': run_id
        })


def update_file_processing_status(
    file_sha256: str,
    bronze_loaded: bool = None,
    bronze_table: str = None,
    bronze_rows: int = None,
    silver_loaded: bool = None,
    silver_table: str = None,
    silver_rows: int = None,
    warehouse_loaded: bool = None,
    warehouse_tables: list = None,
    warehouse_rows: int = None,
    processed_at: str = None
):
    """Update processing status for a file in the catalog."""
    updates = []
    params = {'file_sha256': file_sha256}
    
    if bronze_loaded is not None:
        updates.append("bronze_loaded = :bronze_loaded")
        params['bronze_loaded'] = bronze_loaded
    if bronze_table:
        updates.append("bronze_table = :bronze_table")
        params['bronze_table'] = bronze_table
    if bronze_rows is not None:
        updates.append("bronze_rows = :bronze_rows")
        params['bronze_rows'] = bronze_rows
    if silver_loaded is not None:
        updates.append("silver_loaded = :silver_loaded")
        params['silver_loaded'] = silver_loaded
    if silver_table:
        updates.append("silver_table = :silver_table")
        params['silver_table'] = silver_table
    if silver_rows is not None:
        updates.append("silver_rows = :silver_rows")
        params['silver_rows'] = silver_rows
    if warehouse_loaded is not None:
        updates.append("warehouse_loaded = :warehouse_loaded")
        params['warehouse_loaded'] = warehouse_loaded
    if warehouse_tables:
        updates.append("warehouse_tables = :warehouse_tables")
        params['warehouse_tables'] = warehouse_tables
    if warehouse_rows is not None:
        updates.append("warehouse_rows = :warehouse_rows")
        params['warehouse_rows'] = warehouse_rows
    if processed_at:
        updates.append("processed_at = :processed_at::timestamptz")
        params['processed_at'] = processed_at
    
    if updates:
        updates.append("updated_at = now()")
        with engine.begin() as cxn:
            cxn.execute(text(f"""
            UPDATE data_catalog.downloaded_files
            SET {', '.join(updates)}
            WHERE file_sha256 = :file_sha256
            """), params)


def refresh_available_tables():
    """Refresh the available_tables catalog from actual database tables."""
    with engine.begin() as cxn:
        cxn.execute(text("SELECT data_catalog.refresh_available_tables()"))
