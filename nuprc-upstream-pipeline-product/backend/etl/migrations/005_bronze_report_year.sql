-- Bronze: add report_year for partitioning / segmenting by year
-- Run with: psql $DATABASE_URL -f etl/migrations/005_bronze_report_year.sql

ALTER TABLE bronze.etl_oil_production_raw ADD COLUMN IF NOT EXISTS report_year INT;
ALTER TABLE bronze.etl_gas_production_raw ADD COLUMN IF NOT EXISTS report_year INT;
ALTER TABLE bronze.etl_rig_disposition_raw ADD COLUMN IF NOT EXISTS report_year INT;
ALTER TABLE bronze.etl_concessions_raw ADD COLUMN IF NOT EXISTS report_year INT;
ALTER TABLE bronze.etl_concessions_sections ADD COLUMN IF NOT EXISTS report_year INT;

CREATE INDEX IF NOT EXISTS idx_etl_oil_production_raw_report_year ON bronze.etl_oil_production_raw(report_year);
CREATE INDEX IF NOT EXISTS idx_etl_gas_production_raw_report_year ON bronze.etl_gas_production_raw(report_year);
CREATE INDEX IF NOT EXISTS idx_etl_rig_disposition_raw_report_year ON bronze.etl_rig_disposition_raw(report_year);
CREATE INDEX IF NOT EXISTS idx_etl_concessions_raw_report_year ON bronze.etl_concessions_raw(report_year);
CREATE INDEX IF NOT EXISTS idx_etl_concessions_sections_report_year ON bronze.etl_concessions_sections(report_year);
