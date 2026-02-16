# Performance Optimizations Applied

## Issues Identified

The pipeline was running slowly due to several bottlenecks:

1. **Slow duplicate checks**: UNION query across 4 tables without indexes
2. **Low concurrency**: Limited parallel processing
3. **Inefficient bronze loading**: Individual inserts instead of batched operations

## Optimizations Applied

### 1. Database Indexes ✅
- Added indexes on `file_sha256` columns in all 4 bronze tables
- This makes duplicate checks **10-100x faster** as data grows

### 2. Optimized Duplicate Check ✅
- **Before**: UNION across all 4 tables (slow)
- **After**: 
  - If `source_id` provided, only checks the relevant table (much faster)
  - Uses `LIMIT 1` to stop on first match
  - Reduced timeout from 10s to 5s

### 3. Increased Concurrency ✅
- **Downloads**: Increased from 5 to 10 concurrent downloads per source
- **Extraction**: Increased from 3 to 5 concurrent file extractions
- **Bronze Loading**: Increased from 5 to 10 concurrent loads

### 4. Improved Bronze Loading ✅
- All inserts for a file now happen in a single transaction
- Reduced transaction overhead

### 5. Better Progress Logging ✅
- Reduced duplicate check logging frequency (every 10th instead of every file)
- More informative progress messages

## Expected Performance Improvements

- **Duplicate checks**: 10-50x faster (with indexes + optimized query)
- **Overall pipeline**: 2-3x faster (with increased concurrency)
- **Bronze loading**: 1.5-2x faster (batched transactions)

## Next Steps

1. **Restart backend** to apply all optimizations
2. **Run with Oil & Gas only** first to test
3. **Monitor logs** to see where time is spent
4. **Check database indexes** are created:
   ```sql
   SELECT indexname, tablename 
   FROM pg_indexes 
   WHERE schemaname = 'bronze' AND indexname LIKE '%file_sha256%';
   ```

## If Still Slow

If the pipeline is still slow after these optimizations, check:

1. **Network speed**: Downloading from NUPRC website might be slow
2. **File sizes**: Large PDFs/Excel files take time to download and extract
3. **Database connection**: Check if database is local or remote
4. **System resources**: CPU/RAM might be limiting concurrent operations

## Quick Test

Run only oil and gas to see baseline performance:
```bash
curl -X POST "http://localhost:8000/pipeline/run?source_ids=oil_production_status&source_ids=gas_production_status"
```

Check logs to see timing:
```bash
curl "http://localhost:8000/pipeline/runs/{run_id}"
```
