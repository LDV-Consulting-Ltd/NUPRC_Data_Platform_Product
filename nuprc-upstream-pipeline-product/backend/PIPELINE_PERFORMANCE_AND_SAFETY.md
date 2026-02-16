# Pipeline Performance and Safety Improvements

## Safety: Pipeline Can ONLY Start from Button

✅ **Fixed**: Added guard to prevent multiple simultaneous pipeline runs.

### What Changed:
- The `/pipeline/run` endpoint now checks if a pipeline is already running
- Returns HTTP 409 (Conflict) if you try to start a new run while one is active
- Prevents accidental double-starts or race conditions

### How It Works:
```python
# Checks for running pipelines before starting
running_pipeline = check_for_running_pipeline()
if running_pipeline:
    raise HTTPException(409, "Pipeline already running!")
```

**The pipeline can ONLY be started by:**
1. Clicking the "Run All Sources" button on the home page
2. Clicking individual source buttons (Oil, Gas, Rig, Concession)
3. Making a POST request to `/pipeline/run` (API only)

**The pipeline will NOT:**
- Start automatically on page load
- Start from status polling (only checks status)
- Start from any other trigger

## Performance: Why It Might Be Slow

### Added Performance Logging

The pipeline now logs timing for each step to help identify bottlenecks:

1. **Step 2 (Bronze Loading)**: Logs total time and rows/sec
   - Example: `"Step 2 completed in 45.23s (1250 rows loaded)"`
   - Per-source timing: `"Completed oil_production_status: 500 rows in 12.34s (40 rows/sec)"`

2. **Step 3 (Silver Transformation)**: Logs per-source timing
   - Example: `"Transformed 500 rows from oil_production_status in 8.76s (57 rows/sec)"`

3. **Step 4 (Warehouse Loading)**: Logs total time

### Common Performance Issues:

1. **Excel File Size**: Large Excel files take longer to parse
   - Optimized extractors help, but very large files (100MB+) can still be slow
   - Multiple sheets in rig files add processing time

2. **Silver Transformation**: 
   - Processes all bronze data row-by-row
   - Optimized data uses minimal processing, but standard extraction is slower
   - Check logs to see which source is slow

3. **Database Operations**:
   - Multiple INSERT operations can be slow
   - Bulk inserts are used where possible, but some operations are sequential

4. **Network/Download**:
   - Step 1 (downloading) can be slow if files are large or network is slow
   - Check logs for download times

### How to Check Performance:

1. **View Pipeline Logs**: Go to `/showcase/runs?run_id=<run_id>`
2. **Look for timing messages**: 
   - `"Step X completed in Y.XXs"`
   - `"Completed source_id: X rows in Y.XXs (Z rows/sec)"`
3. **Identify slow steps**: Compare times between sources

## Tables Not Showing: Fixed

✅ **Fixed**: Catalog now auto-refreshes after data is loaded.

### What Changed:
- After each optimized loader completes, `refresh_available_tables()` is called
- After all bronze loading completes, catalog is refreshed again
- After warehouse loading completes, final catalog refresh ensures all tables are visible

### Why Tables Weren't Showing Before:
- The `data_catalog.available_tables` table needs to be refreshed from actual database tables
- It wasn't being refreshed automatically after data loads
- Now it refreshes:
  1. After each file is loaded to bronze
  2. After all files are loaded (batch refresh)
  3. After warehouse loading completes

### Manual Refresh:
If tables still don't show, you can manually refresh:
- Click "Refresh Catalog" button on the catalog page
- Or call `POST /catalog/refresh` API endpoint

## Expected Performance

Based on optimized extractors:

- **Small files (< 5MB)**: 2-5 seconds per file
- **Medium files (5-20MB)**: 5-15 seconds per file  
- **Large files (20MB+)**: 15-30+ seconds per file
- **Multiple sheets (rig files)**: Add 2-5 seconds per sheet

**Total pipeline time for 4 sources:**
- If each source has 1-2 files: 30-60 seconds
- If each source has multiple files: 2-5 minutes
- With network delays: Add 10-30 seconds for downloads

## Troubleshooting Slow Performance

1. **Check logs for timing**: See which step/source is slow
2. **Check file sizes**: Large files take longer
3. **Check database**: Slow database can bottleneck everything
4. **Check network**: Slow downloads affect Step 1
5. **Check concurrent processing**: Should process 5 files at a time

If a specific source is consistently slow, we can optimize it further.
