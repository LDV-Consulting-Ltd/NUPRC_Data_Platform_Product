# backend/app/services/downloader.py
"""
File download service with deduplication and local storage.
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import requests
from sqlalchemy import text

from app.core.db import engine
from app.services.scraper import compute_file_hash


DATA_DIR = Path("data/raw")


def ensure_data_dir(source_id: str) -> Path:
    """Ensure data directory exists for a source."""
    source_dir = DATA_DIR / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    return source_dir


def download_file(
    url: str,
    source_id: str,
    filename: str,
    run_id: str
) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Download a file from URL.
    Returns: (file_path, sha256_hash, is_duplicate)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Use shorter timeout and stream for large files
        response = requests.get(url, headers=headers, timeout=20, stream=True)
        response.raise_for_status()
        
        # Stream download for large files with timeout protection
        content = b''
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        max_size = 100 * 1024 * 1024  # 100MB limit to prevent memory issues
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                downloaded += len(chunk)
                # Prevent downloading files that are too large
                if downloaded > max_size:
                    raise Exception(f"File too large: {downloaded} bytes (max {max_size})")
        
        file_hash = compute_file_hash(content)
        
        # Check if we've already downloaded this file (by hash)
        with engine.connect() as cxn:
            existing = cxn.execute(text("""
                SELECT file_url, file_sha256
                FROM bronze.concession_situation_raw
                WHERE file_sha256 = :hash
                UNION
                SELECT file_url, file_sha256
                FROM bronze.oil_production_status_raw
                WHERE file_sha256 = :hash
                UNION
                SELECT file_url, file_sha256
                FROM bronze.gas_production_status_raw
                WHERE file_sha256 = :hash
                UNION
                SELECT file_url, file_sha256
                FROM bronze.rig_disposition_raw
                WHERE file_sha256 = :hash
            """), {"hash": file_hash}).first()
            
            if existing:
                return None, file_hash, True  # Duplicate
        
        # Save file locally
        source_dir = ensure_data_dir(source_id)
        file_path = source_dir / f"{file_hash[:16]}_{filename}"
        file_path.write_bytes(content)
        
        return str(file_path), file_hash, False
        
    except Exception as e:
        raise Exception(f"Failed to download {url}: {str(e)}")


def get_file_info(file_path: str) -> dict:
    """Get file metadata."""
    path = Path(file_path)
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        'size': stat.st_size,
        'modified': stat.st_mtime,
        'extension': path.suffix.lower()
    }
