-- Gold: dataset-specific dimensional marts (from Silver). No forced shared star schema.
-- Conformed: gold_dim_date only. Each domain gets its own dims/facts.
-- Run after Silver is populated. Apply with: psql $DATABASE_URL -f etl/migrations/006_gold_dataset_marts.sql

CREATE SCHEMA IF NOT EXISTS gold;

-- Conformed dimension: date only (shared across marts that need it)
CREATE TABLE IF NOT EXISTS gold.gold_dim_date (
  date_key INT PRIMARY KEY,
  date_actual DATE NOT NULL,
  year INT,
  month INT,
  day INT
);

-- ---- Oil Production Mart ----
CREATE TABLE IF NOT EXISTS gold.gold_oil_dim_operator (
  operator_sk SERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_oil_fact_production (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT NOT NULL REFERENCES gold.gold_dim_date(date_key),
  operator_sk INT NOT NULL REFERENCES gold.gold_oil_dim_operator(operator_sk),
  production_volume NUMERIC(18,4),
  production_unit TEXT,
  condensate_volume NUMERIC(18,4),
  CONSTRAINT fk_oil_date FOREIGN KEY (date_key) REFERENCES gold.gold_dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_gold_oil_fact_date ON gold.gold_oil_fact_production(date_key);
CREATE INDEX IF NOT EXISTS idx_gold_oil_fact_operator ON gold.gold_oil_fact_production(operator_sk);

-- ---- Gas Production Mart ----
CREATE TABLE IF NOT EXISTS gold.gold_gas_dim_operator (
  operator_sk SERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_gas_fact_production (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT NOT NULL REFERENCES gold.gold_dim_date(date_key),
  operator_sk INT NOT NULL REFERENCES gold.gold_gas_dim_operator(operator_sk),
  gas_volume NUMERIC(18,4),
  gas_unit TEXT,
  flared_volume NUMERIC(18,4),
  utilized_volume NUMERIC(18,4),
  CONSTRAINT fk_gas_date FOREIGN KEY (date_key) REFERENCES gold.gold_dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_gold_gas_fact_date ON gold.gold_gas_fact_production(date_key);
CREATE INDEX IF NOT EXISTS idx_gold_gas_fact_operator ON gold.gold_gas_fact_production(operator_sk);

-- ---- Rig Disposition Mart ----
CREATE TABLE IF NOT EXISTS gold.gold_rig_dim_operator (
  operator_sk SERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_rig_dim_rig (
  rig_sk SERIAL PRIMARY KEY,
  rig_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_rig_dim_status (
  status_sk SERIAL PRIMARY KEY,
  activity_type TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_rig_fact_activity (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT NOT NULL REFERENCES gold.gold_dim_date(date_key),
  operator_sk INT NOT NULL REFERENCES gold.gold_rig_dim_operator(operator_sk),
  rig_sk INT NOT NULL REFERENCES gold.gold_rig_dim_rig(rig_sk),
  status_sk INT NOT NULL REFERENCES gold.gold_rig_dim_status(status_sk),
  rig_count INT DEFAULT 1,
  CONSTRAINT fk_rig_date FOREIGN KEY (date_key) REFERENCES gold.gold_dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_gold_rig_fact_date ON gold.gold_rig_fact_activity(date_key);
CREATE INDEX IF NOT EXISTS idx_gold_rig_fact_operator ON gold.gold_rig_fact_activity(operator_sk);

-- ---- Concession Mart (register + snapshot) ----
CREATE TABLE IF NOT EXISTS gold.gold_concession_dim_concession (
  concession_sk SERIAL PRIMARY KEY,
  concession_no TEXT NOT NULL DEFAULT '',
  concession_category_full TEXT NOT NULL,
  company_operator_name TEXT,
  contract_type TEXT,
  geological_location TEXT,
  derived_from TEXT,
  block_excised_from TEXT,
  grant_date DATE,
  expiration_date DATE,
  area_sqkm NUMERIC(18,4),
  UNIQUE (concession_no, concession_category_full)
);

CREATE TABLE IF NOT EXISTS gold.gold_concession_fact_snapshot (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  report_date_key INT NOT NULL REFERENCES gold.gold_dim_date(date_key),
  concession_sk INT NOT NULL REFERENCES gold.gold_concession_dim_concession(concession_sk),
  is_active INT NOT NULL DEFAULT 1,
  tenure_days_remaining INT,
  area_sqkm NUMERIC(18,4),
  concession_count INT NOT NULL DEFAULT 1,
  CONSTRAINT fk_concession_snap_date FOREIGN KEY (report_date_key) REFERENCES gold.gold_dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_gold_concession_snap_date ON gold.gold_concession_fact_snapshot(report_date_key);
CREATE INDEX IF NOT EXISTS idx_gold_concession_snap_concession ON gold.gold_concession_fact_snapshot(concession_sk);
