# IMMEDIATE FIX - Do This Now

## Step 1: Clear Stuck Run

Run this in Python (in backend directory):
```python
from app.core.db import engine
from sqlalchemy import text

with engine.begin() as cxn:
    cxn.execute(text("""
        UPDATE pipeline_run
        SET status = 'FAILED', ended_at = now(),
            message = 'Cleared stuck run'
        WHERE status = 'RUNNING'
    """))
    print("✅ Cleared all stuck runs")
```

Or use the API:
```
POST http://localhost:8001/pipeline/clear-stuck-runs
```

## Step 2: Restart Backend

**CRITICAL**: Restart the backend to get the new threading code:
```powershell
# Stop backend (Ctrl+C)
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Step 3: Test Direct Execution

Run this to test if pipeline works:
```powershell
cd backend
python clear_and_test.py
```

This will:
1. Clear stuck runs
2. Test pipeline execution directly
3. Show you exactly what happens

## Step 4: Try Again

After clearing and restarting:
1. Click "Run Oil Production" 
2. **IMMEDIATELY** watch backend terminal
3. You should see:
   ```
   🔥🔥🔥 ENDPOINT CALLED: POST /pipeline/run 🔥🔥🔥
   🚀 [MAIN] Starting pipeline thread...
   🔥🔥🔥 THREAD EXECUTING - Pipeline starting! 🔥🔥🔥
   🔥🔥🔥 execute_pipeline() FUNCTION CALLED! 🔥🔥🔥
   ```

If you STILL see nothing, the thread isn't starting. In that case, we need to use a different approach (like running the pipeline synchronously or using a task queue).
