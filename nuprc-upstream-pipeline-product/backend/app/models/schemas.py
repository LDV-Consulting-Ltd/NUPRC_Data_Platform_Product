# backend/app/models/schemas.py
"""
Schema initialization for Bronze, Silver, and Warehouse layers.
"""
from sqlalchemy import text
from app.core.db import engine


def init_bronze_schema():
    """Create bronze schema and raw tables for 4 sources."""
    with engine.begin() as cxn:
        # Create bronze schema
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        
        # Concession Situation
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze.concession_situation_raw (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_url TEXT NOT NULL,
          file_url TEXT NOT NULL,
          file_sha256 TEXT,
          report_period DATE,
          extracted_at TIMESTAMPTZ DEFAULT now(),
          raw_data JSONB,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        # Create index on file_sha256 for fast duplicate checks
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_concession_file_sha256 
        ON bronze.concession_situation_raw(file_sha256);
        """))
        
        # Oil Production Status
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze.oil_production_status_raw (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_url TEXT NOT NULL,
          file_url TEXT NOT NULL,
          file_sha256 TEXT,
          report_period DATE,
          extracted_at TIMESTAMPTZ DEFAULT now(),
          raw_data JSONB,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        # Create index on file_sha256 for fast duplicate checks
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_oil_file_sha256 
        ON bronze.oil_production_status_raw(file_sha256);
        """))
        
        # Gas Production Status
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze.gas_production_status_raw (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_url TEXT NOT NULL,
          file_url TEXT NOT NULL,
          file_sha256 TEXT,
          report_period DATE,
          extracted_at TIMESTAMPTZ DEFAULT now(),
          raw_data JSONB,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        # Create index on file_sha256 for fast duplicate checks
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_gas_file_sha256 
        ON bronze.gas_production_status_raw(file_sha256);
        """))
        
        # Rig Disposition
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze.rig_disposition_raw (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_url TEXT NOT NULL,
          file_url TEXT NOT NULL,
          file_sha256 TEXT,
          report_period DATE,
          extracted_at TIMESTAMPTZ DEFAULT now(),
          raw_data JSONB,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        # Create index on file_sha256 for fast duplicate checks
        cxn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_rig_file_sha256 
        ON bronze.rig_disposition_raw(file_sha256);
        """))


def init_silver_schema():
    """Create silver schema with conformed dimensions."""
    with engine.begin() as cxn:
        # Create silver schema
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        
        # Schema drift tracking
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS silver.schema_drift (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          source_id TEXT NOT NULL,
          table_name TEXT NOT NULL,
          column_name TEXT,
          canonical_name TEXT,
          similarity_score NUMERIC(5,2),
          drift_type TEXT,
          detected_at TIMESTAMPTZ DEFAULT now(),
          resolved BOOLEAN DEFAULT FALSE
        );
        """))


def init_warehouse_schema():
    """Create warehouse schema with dimensional model."""
    with engine.begin() as cxn:
        # Create warehouse schema
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse;"))
        
        # Dimension: Date
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_date (
          date_key INTEGER PRIMARY KEY,
          date_actual DATE NOT NULL,
          day_of_week INTEGER,
          day_name TEXT,
          month INTEGER,
          month_name TEXT,
          quarter INTEGER,
          year INTEGER,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Dimension: Operator
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_operator (
          operator_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          operator_name TEXT NOT NULL UNIQUE,
          operator_code TEXT,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Dimension: Asset
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_asset (
          asset_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          asset_name TEXT NOT NULL,
          asset_type TEXT,
          block_name TEXT,
          field_name TEXT,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Fact: Oil Production
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.fact_oil_production (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          date_key INTEGER REFERENCES warehouse.dim_date(date_key),
          operator_key BIGINT REFERENCES warehouse.dim_operator(operator_key),
          asset_key BIGINT REFERENCES warehouse.dim_asset(asset_key),
          production_volume NUMERIC(18,2),
          production_unit TEXT,
          report_period DATE,
          source_id TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Fact: Gas Production
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.fact_gas_production (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          date_key INTEGER REFERENCES warehouse.dim_date(date_key),
          operator_key BIGINT REFERENCES warehouse.dim_operator(operator_key),
          asset_key BIGINT REFERENCES warehouse.dim_asset(asset_key),
          production_volume NUMERIC(18,2),
          production_unit TEXT,
          report_period DATE,
          source_id TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Fact: Rig Activity
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.fact_rig_activity (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          date_key INTEGER REFERENCES warehouse.dim_date(date_key),
          operator_key BIGINT REFERENCES warehouse.dim_operator(operator_key),
          asset_key BIGINT REFERENCES warehouse.dim_asset(asset_key),
          rig_name TEXT,
          rig_status TEXT,
          activity_type TEXT,
          report_period DATE,
          source_id TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Fact: Concession Status
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.fact_concession_status (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          date_key INTEGER REFERENCES warehouse.dim_date(date_key),
          operator_key BIGINT REFERENCES warehouse.dim_operator(operator_key),
          asset_key BIGINT REFERENCES warehouse.dim_asset(asset_key),
          concession_status TEXT,
          concession_type TEXT,
          report_period DATE,
          source_id TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        # Oil Production Specific Dimensions (for optimized loading)
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_terminal_stream (
          terminal_stream_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          "TERMINAL/STREAM" TEXT UNIQUE NOT NULL
        );
        """))
        
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_liquid_type (
          liquid_type_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          "Liquid Type" TEXT UNIQUE NOT NULL
        );
        """))
        
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.dim_date_month (
          date_key INTEGER PRIMARY KEY,
          year INTEGER NOT NULL,
          monthnum INTEGER NOT NULL,
          month TEXT,
          month_start_date DATE,
          yearmonth TEXT UNIQUE
        );
        """))
        
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse.fact_production (
          terminal_stream_key INTEGER REFERENCES warehouse.dim_terminal_stream(terminal_stream_key),
          liquid_type_key INTEGER REFERENCES warehouse.dim_liquid_type(liquid_type_key),
          date_key INTEGER REFERENCES warehouse.dim_date_month(date_key),
          production_barrels DOUBLE PRECISION NOT NULL,
          sourcefile TEXT,
          PRIMARY KEY (terminal_stream_key, liquid_type_key, date_key)
        );
        """))


def init_all_schemas():
    """Initialize all schemas (bronze, silver, warehouse, data_catalog)."""
    init_bronze_schema()
    init_silver_schema()
    init_warehouse_schema()
    # Initialize data catalog
    from app.models.data_catalog import init_data_catalog
    init_data_catalog()
