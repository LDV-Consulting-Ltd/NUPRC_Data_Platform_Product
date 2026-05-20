"""File registry and incremental processing."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import text

from app.core.db import engine


def file_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash_path(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_processed(file_hash: str, full_rebuild: bool) -> bool:
    if full_rebuild:
        return False
    with engine.connect() as cxn:
        row = cxn.execute(
            text("""
                SELECT status FROM meta.file_registry
                WHERE file_hash = :h AND status = 'PROCESSED'
            """),
            {"h": file_hash},
        ).first()
    return row is not None


def register_file(
    file_hash: str,
    source_name: str,
    file_url: str,
    local_path: Optional[str],
    file_type: Optional[str],
    status: str = "DOWNLOADED",
    error: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO meta.file_registry (
                    file_hash, source_name, file_url, local_path, file_type,
                    status, error, metadata, downloaded_at
                ) VALUES (
                    :file_hash, :source_name, :file_url, :local_path, :file_type,
                    :status, :error, CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (file_hash) DO UPDATE SET
                    local_path = EXCLUDED.local_path,
                    status = EXCLUDED.status,
                    error = EXCLUDED.error,
                    metadata = EXCLUDED.metadata,
                    downloaded_at = COALESCE(meta.file_registry.downloaded_at, now())
            """),
            {
                "file_hash": file_hash,
                "source_name": source_name,
                "file_url": file_url,
                "local_path": local_path,
                "file_type": file_type,
                "status": status,
                "error": error,
                "metadata": json.dumps(metadata or {}),
            },
        )


def mark_processed(file_hash: str) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                UPDATE meta.file_registry
                SET status = 'PROCESSED', processed_at = now(), error = NULL
                WHERE file_hash = :h
            """),
            {"h": file_hash},
        )


def truncate_layers(full_rebuild: bool) -> None:
    if not full_rebuild:
        return
    tables = [
        "bronze.oil_production_status_raw",
        "bronze.gas_production_status_raw",
        "bronze.rig_disposition_raw",
        "bronze.concession_situation_raw",
        "silver.upstream_activity_standardized",
        "warehouse.fact_upstream_activity",
    ]
    with engine.begin() as cxn:
        for t in tables:
            cxn.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE"))
        cxn.execute(text("DELETE FROM meta.file_registry"))
