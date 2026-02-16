# Debugging Pipeline Issues

## Current Issue: Pipeline Running but No Data/Logs

If the pipeline shows as "RUNNING" but:
- No logs appear
- No data is loaded
- Tables remain empty

## Diagnostic Steps

### 1. Check Backend Terminal

Look at the terminal where you're running the backend. You should see:
- `🚀 Adding background task for run {run_id}...`
- `✅ Background task added...`
- Any error messages or tracebacks

### 2. Check if Background Task is Executing

The pipeline runs in a background task. If you don't see logs, the task might not be starting.

**Check backend terminal for:**
- `🚀 Pipeline execution started! Run ID: {run_id}`
- `📋 Source IDs received: [...]`
- `🎯 Processing X source(s): ...`

If you don't see these, the background task isn't executing.

### 3. Check Database Logs Directly

```sql
SELECT * FROM pipeline_log 
WHERE run_id = '056b3411-a0c2-4b72-855f-207443aafd39'
ORDER BY ts ASC;
```

If this returns no rows, logging is failing.

### 4. Check for Silent Failures

The pipeline might be failing before it can log. Check:
- Backend terminal for Python errors
- Database connection issues
- Import errors

### 5. Test Pipeline Manually

Try running the pipeline steps manually in Python:

```python
from app.services.pipeline_executor import scrape_and_download_sources
from app.routers.pipeline import log_message

def test_log(run_id):
    log_message(run_id, "INFO", "Test log message")
    print("Log message sent")

# Check if it appears in database
```

### 6. Common Issues

**Issue: Background tasks not executing**
- FastAPI background tasks run in the same process
- If the server crashes, tasks stop
- Check if backend is still running

**Issue: Database connection problems**
- Logging requires database access
- Check if PostgreSQL is running
- Check connection string

**Issue: Import errors**
- Pipeline imports many modules
- Check backend terminal for ImportError
- Verify all dependencies installed

## Quick Fixes

1. **Restart Backend** - Sometimes background tasks get stuck
2. **Check Database** - Make sure PostgreSQL is running
3. **Check Logs** - Look at backend terminal output
4. **Cancel and Retry** - Cancel current run and start fresh
