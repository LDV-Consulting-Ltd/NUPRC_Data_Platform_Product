-- Fix started_at column type if it's TEXT instead of TIMESTAMPTZ
-- Run this in your PostgreSQL database if started_at is stored as TEXT

-- Check current column type
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pipeline_run' AND column_name = 'started_at';

-- If it's TEXT, convert it to TIMESTAMPTZ
-- WARNING: This will convert existing data. Make sure to backup first!
-- ALTER TABLE pipeline_run 
-- ALTER COLUMN started_at TYPE TIMESTAMPTZ 
-- USING started_at::timestamptz;

-- Or if you want to be safer, create a new column, migrate data, then drop old:
-- ALTER TABLE pipeline_run ADD COLUMN started_at_new TIMESTAMPTZ;
-- UPDATE pipeline_run SET started_at_new = started_at::timestamptz;
-- ALTER TABLE pipeline_run DROP COLUMN started_at;
-- ALTER TABLE pipeline_run RENAME COLUMN started_at_new TO started_at;
