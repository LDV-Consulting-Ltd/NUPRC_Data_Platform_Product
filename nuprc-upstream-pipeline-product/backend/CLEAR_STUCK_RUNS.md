# How to Clear Stuck Pipeline Runs

If you're getting 409 Conflict errors when trying to run the pipeline, it might be because there's a stuck pipeline run in the database.

## Automatic Clearing

The pipeline now automatically clears stuck runs (running for more than 3 hours) when you try to start a new run.

## Manual Clearing

### Option 1: Use the API Endpoint

```bash
POST http://localhost:8000/pipeline/clear-stuck-runs
```

This will:
- Find all runs that have been "RUNNING" for more than 3 hours
- Mark them as "FAILED" with a message
- Return the list of cleared run IDs

### Option 2: Cancel Specific Run

If you know the run_id:

```bash
POST http://localhost:8000/pipeline/runs/{run_id}/cancel
```

### Option 3: Direct Database Query

If you have database access:

```sql
-- See all running pipelines
SELECT run_id, pipeline_name, status, started_at
FROM pipeline_run
WHERE status = 'RUNNING'
ORDER BY started_at DESC;

-- Mark a specific run as failed
UPDATE pipeline_run
SET status = 'FAILED', ended_at = now(),
    message = 'Manually cleared stuck run'
WHERE run_id = 'your-run-id-here';

-- Or clear all stuck runs (running for more than 3 hours)
UPDATE pipeline_run
SET status = 'FAILED', ended_at = now(),
    message = 'Automatically cleared stuck run'
WHERE status = 'RUNNING' 
  AND started_at < NOW() - INTERVAL '3 hours';
```

## Why Runs Get Stuck

1. **Process crashed**: The Python process running the pipeline crashed but the database record wasn't updated
2. **Timeout**: The pipeline exceeded the 2-hour timeout but wasn't properly marked as failed
3. **Manual termination**: The backend was stopped while a pipeline was running
4. **Database connection issues**: Lost connection during execution

## Prevention

The pipeline now:
- Auto-clears stuck runs (3+ hours) when starting new runs
- Has a 2-hour timeout that marks runs as failed
- Better error handling to ensure runs are marked as completed/failed
