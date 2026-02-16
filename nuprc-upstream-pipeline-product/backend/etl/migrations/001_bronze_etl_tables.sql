-- ETL Bronze tables: payload JSONB + metadata columns
-- Names use etl_ prefix to avoid clashing with existing bronze.*_raw tables from the legacy app.
-- Run with: psql $DATABASE_URL -f etl/migrations/001_bronze_etl_tables.sql

CREATE SCHEMA IF NOT EXISTS bronze;

-- Oil production (Excel rows)
CREATE TABLE IF NOT EXISTS bronze.etl_oil_production_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingest_run_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  file_url TEXT,
  file_name TEXT,
  downloaded_at TIMESTAMPTZ,
  sheet_name TEXT,
  row_number INT,
  row_hash TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_etl_oil_production_raw_run ON bronze.etl_oil_production_raw(ingest_run_id);
CREATE INDEX IF NOT EXISTS idx_etl_oil_production_raw_row_hash ON bronze.etl_oil_production_raw(row_hash);

-- Gas production (Excel rows)
CREATE TABLE IF NOT EXISTS bronze.etl_gas_production_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingest_run_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  file_url TEXT,
  file_name TEXT,
  downloaded_at TIMESTAMPTZ,
  sheet_name TEXT,
  row_number INT,
  row_hash TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_etl_gas_production_raw_run ON bronze.etl_gas_production_raw(ingest_run_id);
CREATE INDEX IF NOT EXISTS idx_etl_gas_production_raw_row_hash ON bronze.etl_gas_production_raw(row_hash);

-- Rig disposition (Excel rows)
CREATE TABLE IF NOT EXISTS bronze.etl_rig_disposition_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingest_run_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  file_url TEXT,
  file_name TEXT,
  downloaded_at TIMESTAMPTZ,
  sheet_name TEXT,
  row_number INT,
  row_hash TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_etl_rig_disposition_raw_run ON bronze.etl_rig_disposition_raw(ingest_run_id);
CREATE INDEX IF NOT EXISTS idx_etl_rig_disposition_raw_row_hash ON bronze.etl_rig_disposition_raw(row_hash);

-- Concession raw rows (from PDF with section category)
CREATE TABLE IF NOT EXISTS bronze.etl_concessions_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingest_run_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  file_url TEXT,
  file_name TEXT,
  downloaded_at TIMESTAMPTZ,
  page_number INT,
  row_number_on_page INT,
  concession_category TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_etl_concessions_raw_run ON bronze.etl_concessions_raw(ingest_run_id);
CREATE INDEX IF NOT EXISTS idx_etl_concessions_raw_category ON bronze.etl_concessions_raw(concession_category);

-- Concession section header events
CREATE TABLE IF NOT EXISTS bronze.etl_concessions_sections (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingest_run_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  file_url TEXT,
  file_name TEXT,
  page_number INT NOT NULL,
  header_text TEXT,
  concession_category TEXT NOT NULL,
  line_index INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_etl_concessions_sections_run ON bronze.etl_concessions_sections(ingest_run_id);
