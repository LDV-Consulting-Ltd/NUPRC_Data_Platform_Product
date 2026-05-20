-- PostgreSQL-first: meta, bronze, silver, warehouse (NUPRC Upstream Pipeline Product)

CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS warehouse;

-- meta.pipeline_run
CREATE TABLE IF NOT EXISTS meta.pipeline_run (
  run_id TEXT PRIMARY KEY,
  pipeline_name TEXT NOT NULL DEFAULT 'nuprc_upstream',
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ NULL,
  rows_loaded BIGINT DEFAULT 0,
  message TEXT NULL
);

-- meta.pipeline_log
CREATE TABLE IF NOT EXISTS meta.pipeline_log (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  ts TIMESTAMPTZ DEFAULT now(),
  level TEXT NOT NULL,
  message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_log_run_id ON meta.pipeline_log(run_id);

-- meta.pipeline_step_log
CREATE TABLE IF NOT EXISTS meta.pipeline_step_log (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_name TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ NULL,
  duration_seconds DOUBLE PRECISION NULL,
  rows_processed BIGINT DEFAULT 0,
  files_processed BIGINT DEFAULT 0,
  message TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_step_log_run_id ON meta.pipeline_step_log(run_id);

-- meta.file_registry
CREATE TABLE IF NOT EXISTS meta.file_registry (
  file_hash TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  local_path TEXT NULL,
  file_type TEXT NULL,
  downloaded_at TIMESTAMPTZ DEFAULT now(),
  processed_at TIMESTAMPTZ NULL,
  status TEXT NOT NULL DEFAULT 'DOWNLOADED',
  error TEXT NULL,
  metadata JSONB NULL
);

CREATE INDEX IF NOT EXISTS idx_file_registry_source ON meta.file_registry(source_name);

-- meta.schema_drift
CREATE TABLE IF NOT EXISTS meta.schema_drift (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  file_url TEXT NULL,
  detected_at TIMESTAMPTZ DEFAULT now(),
  drift_type TEXT NOT NULL,
  original_column TEXT NULL,
  mapped_column TEXT NULL,
  match_score DOUBLE PRECISION NULL,
  message TEXT NULL,
  severity TEXT DEFAULT 'WARN'
);

CREATE INDEX IF NOT EXISTS idx_schema_drift_run_id ON meta.schema_drift(run_id);

-- Bronze (one table per NUPRC source)
CREATE TABLE IF NOT EXISTS bronze.oil_production_status_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  file_url TEXT,
  file_hash TEXT,
  report_period TEXT NULL,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  row_payload JSONB NOT NULL,
  canonical_payload JSONB NULL,
  schema_version TEXT NULL,
  drift_flag BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_bronze_oil_run ON bronze.oil_production_status_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_bronze_oil_hash ON bronze.oil_production_status_raw(file_hash);

CREATE TABLE IF NOT EXISTS bronze.gas_production_status_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  file_url TEXT,
  file_hash TEXT,
  report_period TEXT NULL,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  row_payload JSONB NOT NULL,
  canonical_payload JSONB NULL,
  schema_version TEXT NULL,
  drift_flag BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_bronze_gas_run ON bronze.gas_production_status_raw(run_id);

CREATE TABLE IF NOT EXISTS bronze.rig_disposition_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  file_url TEXT,
  file_hash TEXT,
  report_period TEXT NULL,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  row_payload JSONB NOT NULL,
  canonical_payload JSONB NULL,
  schema_version TEXT NULL,
  drift_flag BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_bronze_rig_run ON bronze.rig_disposition_raw(run_id);

CREATE TABLE IF NOT EXISTS bronze.concession_situation_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  file_url TEXT,
  file_hash TEXT,
  report_period TEXT NULL,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  row_payload JSONB NOT NULL,
  canonical_payload JSONB NULL,
  schema_version TEXT NULL,
  drift_flag BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_bronze_concession_run ON bronze.concession_situation_raw(run_id);

-- Silver standardized
CREATE TABLE IF NOT EXISTS silver.upstream_activity_standardized (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  report_period TEXT NULL,
  operator_name TEXT NULL,
  asset_name TEXT NULL,
  field_name TEXT NULL,
  terminal_stream TEXT NULL,
  product_type TEXT NULL,
  rig_name TEXT NULL,
  concession_name TEXT NULL,
  concession_type TEXT NULL,
  status TEXT NULL,
  volume_value DOUBLE PRECISION NULL,
  volume_unit TEXT NULL,
  row_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_silver_activity_run ON silver.upstream_activity_standardized(run_id);
CREATE INDEX IF NOT EXISTS idx_silver_activity_type ON silver.upstream_activity_standardized(activity_type);

-- Warehouse dimensions
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
  date_key INTEGER PRIMARY KEY,
  full_date DATE NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  quarter INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_source (
  source_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_name TEXT NOT NULL UNIQUE,
  source_url TEXT NULL,
  activity_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_operator (
  operator_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_asset (
  asset_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  asset_name TEXT NOT NULL,
  field_name TEXT NULL,
  UNIQUE (asset_name, field_name)
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
  product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_type TEXT NOT NULL,
  terminal_stream TEXT NULL,
  UNIQUE (product_type, terminal_stream)
);

-- Warehouse fact
CREATE TABLE IF NOT EXISTS warehouse.fact_upstream_activity (
  fact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INTEGER NULL,
  source_key BIGINT NOT NULL,
  operator_key BIGINT NULL,
  asset_key BIGINT NULL,
  product_key BIGINT NULL,
  activity_type TEXT NOT NULL,
  report_period TEXT NULL,
  status TEXT NULL,
  volume_value DOUBLE PRECISION NULL,
  volume_unit TEXT NULL,
  source_row_id BIGINT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_activity_type ON warehouse.fact_upstream_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_fact_report_period ON warehouse.fact_upstream_activity(report_period);
CREATE INDEX IF NOT EXISTS idx_fact_operator ON warehouse.fact_upstream_activity(operator_key);
CREATE INDEX IF NOT EXISTS idx_fact_asset ON warehouse.fact_upstream_activity(asset_key);
CREATE INDEX IF NOT EXISTS idx_fact_source ON warehouse.fact_upstream_activity(source_key);

-- Diagram metadata (mermaid stored as JSONB)
CREATE TABLE IF NOT EXISTS meta.pipeline_diagrams (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id TEXT NULL,
  diagram_type TEXT NOT NULL,
  diagram_content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
