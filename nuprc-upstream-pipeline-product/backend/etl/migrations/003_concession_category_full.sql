-- Add full header text column for concession raw table
-- concession_category_full = exact section header text (PETROLEUM ... LICENCE/LEASE)

ALTER TABLE bronze.etl_concessions_raw
  ADD COLUMN IF NOT EXISTS concession_category_full TEXT;

CREATE INDEX IF NOT EXISTS idx_etl_concessions_raw_category_full
  ON bronze.etl_concessions_raw(concession_category_full);
