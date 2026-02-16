# backend/app/services/async_pipeline_executor.py
"""
Async pipeline execution with concurrent processing for maximum performance.
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import text

from app.core.db import engine
from app.services.sources import get_all_sources
from app.services.async_scraper import scrape_all_sources_async
from app.services.async_downloader import download_files_concurrent
from app.services.async_extractor import extract_multiple_files_concurrent
from app.services.bronze_loader import load_to_bronze
from app.services.fuzzy_matcher import detect_schema_drift, log_schema_drift


async def scrape_and_download_sources_async(run_id: str, log_func, source_ids: Optional[List[str]] = None) -> List[dict]:
    """
    Step 1: Scrape sources concurrently and download files in parallel.
    Returns list of downloaded file info.
    
    Args:
        run_id: Run identifier
        log_func: Logging function
        source_ids: Optional list of source IDs to process. If None, processes all sources.
    """
    all_sources = get_all_sources()
    if source_ids and len(source_ids) > 0:
        sources = [s for s in all_sources if s.source_id in source_ids]
        log_func(run_id, "INFO", f"🔵 FILTERING TO {len(sources)} SOURCE(S): {', '.join(source_ids)}")
        log_func(run_id, "INFO", f"   Will process: {', '.join([s.name for s in sources])}")
    else:
        sources = all_sources
        log_func(run_id, "INFO", f"🔴 PROCESSING ALL {len(sources)} SOURCES (no source_ids provided)")
    
    # Scrape all sources concurrently
    log_func(run_id, "INFO", f"Scraping {len(sources)} sources concurrently...")
    for source in sources:
        log_func(run_id, "INFO", f"  - {source.name} ({source.source_id})")
    
    try:
        # Create a log wrapper that includes run_id
        source_links = await asyncio.wait_for(
            scrape_all_sources_async(sources, log_func=lambda _, level, msg: log_func(run_id, level, msg)),
            timeout=60.0  # 1 minute max for scraping
        )
    except asyncio.TimeoutError:
        log_func(run_id, "ERROR", "Scraping timed out after 60 seconds")
        return []
    except Exception as e:
        err_type = type(e).__name__
        log_func(run_id, "ERROR", f"Scraping failed ({err_type}): {str(e)}")
        return []
    
    # Log results
    for source in sources:
        links = source_links.get(source.source_id, [])
        log_func(run_id, "INFO", f"Found {len(links)} files for {source.name}")
    
    # Download all files concurrently (5 at a time per source)
    downloaded_files = []
    total_downloaded = 0
    total_duplicates = 0
    
    # Process each source's files
    for source in sources:
        links = source_links.get(source.source_id, [])
        if not links:
            log_func(run_id, "INFO", f"No files found for {source.name}, skipping...")
            continue
        
        try:
            log_func(run_id, "INFO", f"Downloading {len(links)} files from {source.name} (concurrent, max 10 at a time)...")
            
            # Download files concurrently with timeout
            # Keep duplicate check enabled but optimized (checks only relevant table)
            # Pass run_id so catalog can track which run downloaded each file
            try:
                # For oil/gas, skip duplicate check for speed (they're fast anyway)
                # Duplicate check adds significant overhead
                skip_dup = source.source_id in ['oil_production_status', 'gas_production_status']
                file_results = await asyncio.wait_for(
                    download_files_concurrent(
                        links, source.source_id, max_concurrent=10,
                        skip_duplicate_check=skip_dup, run_id=run_id, log_func=log_func
                    ),
                    timeout=300.0  # 5 minutes max per source
                )
            except asyncio.TimeoutError:
                log_func(run_id, "ERROR", f"Download from {source.name} timed out after 5 minutes")
                continue
            
            # Process results with progress
            for idx, (file_path, file_hash, is_duplicate, link) in enumerate(file_results, 1):
                if is_duplicate:
                    total_duplicates += 1
                    if idx % 10 == 0 or idx == len(file_results):  # Log every 10th or last
                        log_func(run_id, "INFO", f"[{idx}/{len(file_results)}] Skipped duplicate: {link['filename']}")
                elif file_path:
                    total_downloaded += 1
                    downloaded_files.append({
                        'source': source,
                        'url': link['url'],
                        'file_path': file_path,
                        'file_hash': file_hash,
                        'file_type': link['file_type'],
                        'filename': link['filename']
                    })
                else:
                    log_func(run_id, "WARN", f"[{idx}/{len(file_results)}] ✗ Failed: {link['filename']}")
        
        except Exception as e:
            log_func(run_id, "ERROR", f"Failed to download files from {source.name}: {str(e)}")
            continue
    
    log_func(run_id, "INFO", f"Downloaded {total_downloaded} new files, skipped {total_duplicates} duplicates")
    return downloaded_files


async def extract_and_load_bronze_async(downloaded_files: List[dict], run_id: str, log_func) -> int:
    """
    Step 2: Extract tables from files concurrently and load into warehouse.
    Uses optimized direct-to-warehouse paths for all sources (oil, gas, rig, concession).
    Returns total rows loaded.
    """
    if not downloaded_files:
        return 0
    
    # Map source IDs to their optimized loaders (now load to staging)
    optimized_loaders = {
        'oil_production_status': ('app.services.oil_production_loader', 'load_oil_production_to_staging'),
        'gas_production_status': ('app.services.gas_production_loader', 'load_gas_production_to_staging'),
        'rig_disposition': ('app.services.rig_disposition_loader', 'load_rig_disposition_to_staging'),
        'concession_situation': ('app.services.concession_loader', 'load_concession_to_staging')
    }
    
    # Separate files by source
    optimized_files = {source_id: [] for source_id in optimized_loaders.keys()}
    other_files = []
    
    for fi in downloaded_files:
        source_id = fi['source'].source_id
        if source_id in optimized_loaders:
            optimized_files[source_id].append(fi)
        else:
            other_files.append(fi)
    
    total_rows = 0
    
    # Process all optimized sources (oil, gas, rig, concession) to bronze staging
    # Process files in smaller batches and refresh catalog frequently for faster visibility
    for source_id, files in optimized_files.items():
        if not files:
            continue
        
        log_func(run_id, "INFO", f"Processing {len(files)} {source_id} files with optimized extractor (to staging)...")
        
        # Import the appropriate loader
        loader_module_name, loader_func_name = optimized_loaders[source_id]
        loader_module = __import__(loader_module_name, fromlist=[''])
        loader_func = getattr(loader_module, loader_func_name)
        
        async def load_file_optimized(file_info):
            try:
                rows = await asyncio.to_thread(
                    loader_func,
                    file_info['file_path'],
                    file_info['url'],
                    file_info['file_hash'],
                    run_id,
                    log_func
                )
                return rows
            except Exception as e:
                log_func(run_id, "ERROR", f"Failed to process {source_id} file {file_info['filename']}: {str(e)}")
                import traceback
                log_func(run_id, "ERROR", traceback.format_exc())
                return 0
        
        # Higher concurrency for oil/gas (they're fast and lightweight)
        max_concurrent = 5 if source_id in ['oil_production_status', 'gas_production_status'] else 3
        semaphore = asyncio.Semaphore(max_concurrent)
        log_func(run_id, "INFO", f"Processing with {max_concurrent} concurrent files...")
        
        async def load_with_limit(file_info):
            async with semaphore:
                return await load_file_optimized(file_info)
        
        # Process files in batches of 5 for faster catalog updates
        batch_size = 5
        import time
        start_time = time.time()
        source_rows = 0
        
        for batch_start in range(0, len(files), batch_size):
            batch = files[batch_start:batch_start + batch_size]
            tasks = [load_with_limit(fi) for fi in batch]
            row_counts = await asyncio.gather(*tasks, return_exceptions=True)
            batch_rows = sum(r for r in row_counts if isinstance(r, int))
            source_rows += batch_rows
            total_rows += batch_rows
            
            # Refresh catalog after each batch for faster visibility
            if batch_rows > 0:
                try:
                    from app.models.data_catalog import refresh_available_tables
                    refresh_available_tables()
                    log_func(run_id, "INFO", f"✓ Processed batch {batch_start//batch_size + 1}: {batch_rows} rows (catalog refreshed)")
                except Exception as e:
                    log_func(run_id, "WARN", f"Failed to refresh catalog: {str(e)}")
        
        elapsed = time.time() - start_time
        log_func(run_id, "INFO", f"Completed {source_id}: {source_rows} rows in {elapsed:.2f}s ({source_rows/elapsed:.0f} rows/sec)")
    
    # Final catalog refresh after all optimized files are loaded
    if total_rows > 0:
        try:
            from app.models.data_catalog import refresh_available_tables
            log_func(run_id, "INFO", "Final catalog refresh...")
            refresh_available_tables()
            log_func(run_id, "INFO", "Catalog tables refreshed - all tables should now be visible")
        except Exception as e:
            log_func(run_id, "WARN", f"Failed to refresh catalog: {str(e)}")
    
    # Process any remaining files with standard bronze/silver path (fallback)
    if other_files:
        log_func(run_id, "INFO", f"Extracting tables from {len(other_files)} other files concurrently...")
        
        file_infos = [
            {
                'file_path': fi['file_path'],
                'file_type': fi['file_type'],
                'source': fi['source'],
                'url': fi['url'],
                'file_hash': fi['file_hash'],
                'filename': fi['filename']
            }
            for fi in other_files
        ]
        
        extracted_tables = await extract_multiple_files_concurrent(file_infos, max_concurrent=5)
        
        # Use asyncio to parallelize bronze loading
        async def load_file_to_bronze(file_info):
            source = file_info['source']
            file_path = file_info['file_path']
            
            if file_path not in extracted_tables:
                log_func(run_id, "WARN", f"No tables extracted from {file_info['filename']}")
                return 0
            
            tables = extracted_tables[file_path]
            log_func(run_id, "INFO", f"Extracted {len(tables)} tables from {file_info['filename']}")
            
            # Detect schema drift
            for table in tables:
                columns = table.get('columns', [])
                drift_records = detect_schema_drift(
                    columns,
                    source.source_id,
                    source.bronze_table,
                    run_id
                )
                if drift_records:
                    log_schema_drift(drift_records, run_id)
                    log_func(run_id, "WARN", f"Detected {len(drift_records)} schema drift issues in {file_info['filename']}")
            
            # Load to bronze (run in thread pool since it's DB I/O)
            rows_loaded = await asyncio.to_thread(
                load_to_bronze,
                source,
                file_info['url'],
                file_path,
                file_info['file_hash'],
                tables,
                run_id
            )
            
            log_func(run_id, "INFO", f"Loaded {rows_loaded} rows to {source.bronze_table}")
            return rows_loaded
        
        # Load all files concurrently (10 at a time for better performance)
        semaphore = asyncio.Semaphore(10)
        
        async def load_with_limit(file_info):
            async with semaphore:
                try:
                    return await load_file_to_bronze(file_info)
                except Exception as e:
                    log_func(run_id, "ERROR", f"Failed to process {file_info['filename']}: {str(e)}")
                    return 0
        
        tasks = [load_with_limit(fi) for fi in file_infos]
        row_counts = await asyncio.gather(*tasks, return_exceptions=True)
        total_rows += sum(r for r in row_counts if isinstance(r, int))
    
    return total_rows
