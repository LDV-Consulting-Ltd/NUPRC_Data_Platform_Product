# backend/app/services/async_downloader.py
"""
Async file download service with concurrent downloads and progress tracking.
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import aiohttp
import aiofiles
from sqlalchemy import text

from app.core.db import engine


DATA_DIR = Path("data/raw")


def ensure_data_dir(source_id: str) -> Path:
    """Ensure data directory exists for a source."""
    source_dir = DATA_DIR / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    return source_dir


def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content for deduplication."""
    return hashlib.sha256(content).hexdigest()


def check_duplicate_sync(file_hash: str, source_id: str = None) -> bool:
    """
    Check if file hash already exists in database (synchronous version for thread pool).
    Optimized: if source_id provided, only check that table. Otherwise check all.
    """
    with engine.connect() as cxn:
        if source_id:
            # Optimized: only check the relevant table for this source
            table_map = {
                "concession_situation": "bronze.concession_situation_raw",
                "oil_production_status": "bronze.oil_production_status_raw",
                "gas_production_status": "bronze.gas_production_status_raw",
                "rig_disposition": "bronze.rig_disposition_raw"
            }
            table = table_map.get(source_id)
            if table:
                existing = cxn.execute(text(f"""
                    SELECT 1 FROM {table}
                    WHERE file_sha256 = :hash
                    LIMIT 1
                """), {"hash": file_hash}).first()
                return existing is not None
        
        # Fallback: check all tables (slower but more thorough)
        # Optimized: use LIMIT 1 and check each table separately (stops on first match)
        for table in ["bronze.concession_situation_raw", "bronze.oil_production_status_raw", 
                      "bronze.gas_production_status_raw", "bronze.rig_disposition_raw"]:
            existing = cxn.execute(text(f"""
                SELECT 1 FROM {table}
                WHERE file_sha256 = :hash
                LIMIT 1
            """), {"hash": file_hash}).first()
            if existing:
                return True
        
        return False


async def download_file_async(
    session: aiohttp.ClientSession,
    url: str,
    source_id: str,
    filename: str,
    semaphore: asyncio.Semaphore,
    max_size: int = 100 * 1024 * 1024,  # 100MB
    skip_duplicate_check: bool = False,  # Skip duplicate check for performance
    run_id: str = None  # Run ID for catalog tracking
) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Async download a file from URL with size limit.
    Returns: (file_path, sha256_hash, is_duplicate)
    """
    async with semaphore:  # Limit concurrent downloads
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(
                url, 
                headers=headers, 
                allow_redirects=True
            ) as response:
                response.raise_for_status()
                
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_size:
                    raise Exception(f"File too large: {content_length} bytes (max {max_size})")
                
                # Stream download with progress tracking
                content = b''
                downloaded = 0
                chunk_size = 8192
                
                async for chunk in response.content.iter_chunked(chunk_size):
                    if chunk:
                        content += chunk
                        downloaded += len(chunk)
                        
                        if downloaded > max_size:
                            raise Exception(f"File too large: {downloaded} bytes (max {max_size})")
                
                file_hash = compute_file_hash(content)
                
                # Check for duplicates (run in thread pool since it's DB I/O)
                # Skip if flag is set for performance (e.g., when running specific sources)
                is_duplicate = False
                if not skip_duplicate_check:
                    try:
                        is_duplicate = await asyncio.wait_for(
                            asyncio.to_thread(check_duplicate_sync, file_hash, source_id),
                            timeout=5.0  # Reduced timeout to 5 seconds
                        )
                    except asyncio.TimeoutError:
                        # If duplicate check times out, assume not duplicate and proceed
                        is_duplicate = False
                    except Exception as e:
                        # If duplicate check fails, log and proceed (assume not duplicate)
                        is_duplicate = False
                
                if is_duplicate:
                    # Register duplicate in catalog immediately (synchronous for fast catalog population)
                    try:
                        from app.models.data_catalog import register_downloaded_file
                        from app.services.sources import get_all_sources
                        
                        sources = get_all_sources()
                        source_name = next((s.name for s in sources if s.source_id == source_id), source_id)
                        
                        # Register immediately (don't use thread pool - catalog should be fast)
                        register_downloaded_file(
                            source_id=source_id,
                            source_name=source_name,
                            file_url=url,
                            file_path=None,
                            filename=filename,
                            file_sha256=file_hash,
                            file_type=filename.split('.')[-1] if '.' in filename else 'unknown',
                            file_size=None,
                            download_status='duplicate',
                            run_id=run_id
                        )
                    except Exception as e:
                        # Log but don't fail - catalog shouldn't block downloads
                        pass
                    
                    return None, file_hash, True
                
                # Save file locally using aiofiles for async I/O
                source_dir = ensure_data_dir(source_id)
                file_path = source_dir / f"{file_hash[:16]}_{filename}"
                
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                
                # Register in data catalog IMMEDIATELY (synchronous for fast catalog population)
                # Catalog registration is fast DB operation, no need for thread pool
                try:
                    from app.models.data_catalog import register_downloaded_file
                    from app.services.sources import get_all_sources
                    
                    # Get source name
                    sources = get_all_sources()
                    source_name = next((s.name for s in sources if s.source_id == source_id), source_id)
                    
                    # Register immediately - catalog should populate within 2-3 mins as files download
                    register_downloaded_file(
                        source_id=source_id,
                        source_name=source_name,
                        file_url=url,
                        file_path=str(file_path),
                        filename=filename,
                        file_sha256=file_hash,
                        file_type=filename.split('.')[-1] if '.' in filename else 'unknown',
                        file_size=len(content),
                        download_status='downloaded',
                        run_id=run_id
                    )
                except Exception as e:
                    # Log but don't fail - catalog shouldn't block downloads
                    # But we want to know if it fails
                    import logging
                    logging.warning(f"Catalog registration failed for {filename}: {e}")
                    pass
                
                return str(file_path), file_hash, False
                
        except asyncio.TimeoutError:
            raise Exception(f"Download timeout for {url}")
        except Exception as e:
            raise Exception(f"Failed to download {url}: {str(e)}")


async def download_files_concurrent(
    file_links: List[Dict[str, str]],
    source_id: str,
    max_concurrent: int = 5,
    skip_duplicate_check: bool = False,
    run_id: str = None,  # Run ID for catalog tracking
    log_func=None  # Optional (run_id, level, msg) for run logs
) -> List[Tuple[Optional[str], Optional[str], bool, Dict[str, str]]]:
    """
    Download multiple files concurrently.
    Returns list of (file_path, file_hash, is_duplicate, link_info) tuples.
    When log_func is provided, failed downloads are logged with the actual exception.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create session with timeout and connection limits
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # Create download tasks (will run concurrently up to semaphore limit)
        async def download_with_timeout(link):
            try:
                result = await asyncio.wait_for(
                    download_file_async(
                        session,
                        link['url'],
                        source_id,
                        link['filename'],
                        semaphore,
                        skip_duplicate_check=skip_duplicate_check,
                        run_id=run_id
                    ),
                    timeout=120.0  # 2 minutes per file max
                )
                return result
            except asyncio.TimeoutError:
                raise Exception(f"Download timeout (120s) for {link.get('filename', link.get('url', '?'))}")
            except Exception:
                raise  # Propagate so we can log the real error
        
        # Run all downloads concurrently (semaphore limits to max_concurrent)
        tasks = [download_with_timeout(link) for link in file_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results with link info; log failure reason when log_func provided
        file_results = []
        for link, result in zip(file_links, results):
            if isinstance(result, Exception):
                if log_func and run_id:
                    fn = link.get('filename', link.get('url', '?'))
                    log_func(run_id, "WARN", f"Download failed for {fn}: {result}")
                file_results.append((None, None, False, link))
            else:
                file_path, file_hash, is_duplicate = result
                file_results.append((file_path, file_hash, is_duplicate, link))
        
        return file_results
