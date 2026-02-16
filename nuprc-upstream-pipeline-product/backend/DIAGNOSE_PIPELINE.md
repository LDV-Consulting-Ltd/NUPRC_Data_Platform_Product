# Pipeline Diagnosis

## What to Check When Pipeline "Runs for Short Period and Stops"

### 1. Check Backend Terminal Output

Look for these messages in order:
```
🔥🔥🔥 ENDPOINT CALLED: POST /pipeline/run 🔥🔥🔥
🚀 [MAIN] Starting pipeline thread...
🔥🔥🔥 THREAD EXECUTING - Pipeline starting! 🔥🔥🔥
🔥🔥🔥 execute_pipeline() FUNCTION CALLED! 🔥🔥🔥
📥 STEP 1: Scraping and downloading...
   [scrape_and_download_sources] Starting...
   [scrape_and_download_sources] Creating event loop...
   [scrape_and_download_sources] Running async function...
```

### 2. Common Issues

**Issue A: Thread doesn't start**
- You see "ENDPINT CALLED" but NOT "THREAD EXECUTING"
- **Fix**: Restart backend, check for errors in terminal

**Issue B: No files downloaded (all duplicates)**
- You see "STEP 1 Complete: 0 files downloaded"
- You see "No files downloaded - checking if files already exist..."
- **Fix**: Check if bronze has data. If yes, pipeline should continue to silver/warehouse

**Issue C: Scraping fails silently**
- You see "STEP 1" but no "Complete" message
- **Fix**: Check network, source URLs, see error logs

**Issue D: Event loop fails**
- You see "Creating event loop" but nothing after
- **Fix**: This is a threading issue - may need different approach

### 3. Quick Test

Run this to see what's in the database:
```python
from app.core.db import engine
from sqlalchemy import text

with engine.connect() as cxn:
    bronze = cxn.execute(text("SELECT COUNT(*) FROM bronze")).scalar()
    silver = cxn.execute(text("SELECT COUNT(*) FROM silver")).scalar()
    warehouse = cxn.execute(text("SELECT COUNT(*) FROM warehouse")).scalar()
    catalog = cxn.execute(text("SELECT COUNT(*) FROM data_catalog")).scalar()
    
    print(f"Bronze: {bronze} rows")
    print(f"Silver: {silver} rows")
    print(f"Warehouse: {warehouse} rows")
    print(f"Catalog: {catalog} files")
```

### 4. Check Pipeline Logs

```python
from app.core.db import engine
from sqlalchemy import text

with engine.connect() as cxn:
    logs = cxn.execute(text("""
        SELECT level, message, created_at
        FROM pipeline_log
        ORDER BY created_at DESC
        LIMIT 20
    """)).mappings().all()
    
    for log in logs:
        print(f"{log['level']:5} | {log['created_at']} | {log['message']}")
```
