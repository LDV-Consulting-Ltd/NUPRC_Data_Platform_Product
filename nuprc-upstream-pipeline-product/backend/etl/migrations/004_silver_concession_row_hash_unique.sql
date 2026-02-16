-- Silver: unique index on fact_concession_status.row_hash for ON CONFLICT (row_hash) DO NOTHING
-- Run when table is empty or after deduplicating. psql $DATABASE_URL -f etl/migrations/004_silver_concession_row_hash_unique.sql

CREATE UNIQUE INDEX IF NOT EXISTS idx_silver_fact_concession_status_row_hash
  ON silver.fact_concession_status (row_hash);
