# Troubleshooting Guide

## 500 Internal Server Error

If you're getting a 500 error when trying to run the pipeline, follow these steps:

### Step 1: Check if Backend is Running

Open your browser and go to:
- `http://localhost:8001/health/summary` (or `http://127.0.0.1:8001/health/summary`)

You should see: `{"ok": true, "status": "green"}`

If this doesn't work, the backend is not running. Start it:
```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Step 2: Test Pipeline Endpoint

Go to:
- `http://localhost:8001/pipeline/test`

This will show you:
- Database connection status
- Source configuration status
- Pipeline run table status

### Step 3: Check Backend Logs

Look at the terminal where you're running the backend. The error message should show:
- What failed
- The full traceback

Common issues:
1. **Database not running**: Make sure PostgreSQL is running
2. **Database connection string wrong**: Check `DATABASE_URL` in your environment or `.env` file
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **Port conflict**: Another process is using port 8001

### Step 4: Check Database Connection

Test your database connection:
```python
from app.core.db import engine
with engine.connect() as cxn:
    result = cxn.execute(text("SELECT 1"))
    print(result.scalar())
```

### Step 5: Check Source Configurations

Test if sources load correctly:
```python
from app.services.sources import get_all_sources
sources = get_all_sources()
print(f"Loaded {len(sources)} sources")
for s in sources:
    print(f"  - {s.source_id}: {s.source_name}")
```

## Common Error Messages

### "Database connection failed"
- PostgreSQL is not running
- Wrong connection string
- Database doesn't exist

### "Failed to load source configurations"
- Missing `sources.py` file
- Error in source configuration
- Missing required fields

### "Port already in use"
- Another process is using the port
- Kill the process or use a different port

## Quick Fixes

1. **Restart Backend**: Kill all Python processes and restart
2. **Check Ports**: `netstat -ano | findstr :8001`
3. **Check Database**: Make sure PostgreSQL is running
4. **Check Logs**: Look at the backend terminal output
