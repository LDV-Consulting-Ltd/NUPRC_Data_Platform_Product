# Quick Fix: Clear Stuck Pipeline Run

You have a stuck pipeline run blocking new runs. Here's how to clear it:

## Option 1: Use the API (Easiest)

Open in browser or use curl:
```
POST http://localhost:8001/pipeline/clear-stuck-runs
```

Or use curl:
```powershell
curl -X POST http://localhost:8001/pipeline/clear-stuck-runs
```

## Option 2: Cancel Specific Run

If you know the run ID (`c876973a-9ecb-47db-8c58-40bf632e0ea8`):

```
POST http://localhost:8001/pipeline/runs/c876973a-9ecb-47db-8c58-40bf632e0ea8/cancel
```

Or use the frontend - go to the runs page and click "Cancel" on that run.

## Option 3: Direct Database (If API doesn't work)

```python
from app.core.db import engine
from sqlalchemy import text

with engine.begin() as cxn:
    cxn.execute(text("""
        UPDATE pipeline_run
        SET status = 'FAILED', ended_at = now(),
            message = 'Manually cleared stuck run'
        WHERE run_id = 'c876973a-9ecb-47db-8c58-40bf632e0ea8'
    """))
    print("✅ Cleared stuck run")
```

## After Clearing

1. Clear the stuck run using one of the methods above
2. Try running the pipeline again
3. Watch the backend terminal - you should now see the print statements
