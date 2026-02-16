-- Silver: conformed dimensions and facts
-- Gold: analytics-ready star schema (gold_*)

CREATE SCHEMA IF NOT EXISTS silver;

-- Conformed dimensions (silver)
CREATE TABLE IF NOT EXISTS silver.dim_date (
  date_key INTEGER PRIMARY KEY,
  date_actual DATE NOT NULL,
  year INT, month INT, day INT
);

CREATE TABLE IF NOT EXISTS silver.dim_operator (
  operator_key SERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.dim_operator_aliases (
  alias_key SERIAL PRIMARY KEY,
  operator_key INT REFERENCES silver.dim_operator(operator_key),
  alias TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.dim_concession (
  concession_key SERIAL PRIMARY KEY,
  concession_id TEXT,
  category TEXT,
  operator_name TEXT,
  status TEXT
);

-- Facts (silver)
CREATE TABLE IF NOT EXISTS silver.fact_oil_production (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT REFERENCES silver.dim_date(date_key),
  operator_key INT REFERENCES silver.dim_operator(operator_key),
  payload JSONB,
  row_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.fact_gas_production (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT REFERENCES silver.dim_date(date_key),
  operator_key INT REFERENCES silver.dim_operator(operator_key),
  payload JSONB,
  row_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.fact_rig_disposition (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT REFERENCES silver.dim_date(date_key),
  operator_key INT REFERENCES silver.dim_operator(operator_key),
  payload JSONB,
  row_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS silver.fact_concession_status (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concession_key INT REFERENCES silver.dim_concession(concession_key),
  concession_category TEXT,
  payload JSONB,
  row_hash TEXT
);

-- Gold schema
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.gold_dim_date (
  date_key INTEGER PRIMARY KEY,
  date_actual DATE NOT NULL,
  year INT, month INT, day INT
);

CREATE TABLE IF NOT EXISTS gold.gold_dim_operator (
  operator_key SERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.gold_dim_concession (
  concession_key SERIAL PRIMARY KEY,
  concession_id TEXT,
  category TEXT,
  operator_name TEXT
);

CREATE TABLE IF NOT EXISTS gold.gold_fact_upstream_production (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT REFERENCES gold.gold_dim_date(date_key),
  operator_key INT REFERENCES gold.gold_dim_operator(operator_key),
  production_volume NUMERIC(18,2),
  production_unit TEXT,
  source_type TEXT
);

CREATE TABLE IF NOT EXISTS gold.gold_fact_rig_activity (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_key INT REFERENCES gold.gold_dim_date(date_key),
  operator_key INT REFERENCES gold.gold_dim_operator(operator_key),
  rig_name TEXT,
  activity_type TEXT
);

CREATE TABLE IF NOT EXISTS gold.gold_fact_concessions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concession_key INT REFERENCES gold.gold_dim_concession(concession_key),
  category TEXT,
  status TEXT
);
