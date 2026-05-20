"""
PostgreSQL-first pipeline runner: discovery → acquisition → bronze → silver → warehouse → catalog.
"""
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

from etl.acquire import download_file, download_concession_pdf
from etl.config import DATA_RAW

from app.models.pg_schemas import init_pg_schemas
from app.services.pg_pipeline import meta_log
from app.services.pg_pipeline.bronze_loader import load_file_to_bronze
from app.services.pg_pipeline.discovery import discover_files
from app.services.pg_pipeline.diagrams import save_diagrams
from app.services.pg_pipeline.registry import (
    file_hash_path,
    is_processed,
    mark_processed,
    register_file,
    truncate_layers,
)
from app.services.pg_pipeline.silver_loader import standardize_bronze_to_silver
from app.services.pg_pipeline.warehouse_loader import load_silver_to_warehouse
from sqlalchemy import text
from app.core.db import engine


def _run_exists(run_id: str) -> bool:
    with engine.connect() as cxn:
        return cxn.execute(
            text("SELECT 1 FROM meta.pipeline_run WHERE run_id = :id"),
            {"id": run_id},
        ).first() is not None


def run_pipeline(mode: str = "incremental", run_id: str | None = None) -> Tuple[str, bool, str | None]:
    """
    mode: incremental | full_rebuild
    Returns (run_id, success, error_message).
    """
    full_rebuild = mode == "full_rebuild"
    run_id = run_id or str(uuid.uuid4())
    init_pg_schemas()
    if not _run_exists(run_id):
        meta_log.create_run(run_id, "RUNNING")
    else:
        meta_log.update_run(run_id, "RUNNING")
    meta_log.log_line(run_id, "INFO", f"Pipeline started mode={mode}")

    try:
        if full_rebuild:
            truncate_layers(True)
            meta_log.log_line(run_id, "INFO", "Full rebuild: truncated bronze/silver/warehouse layers")

        # 1. Source discovery
        sid = meta_log.start_step(run_id, "source_discovery")
        discovered, disc_errors = discover_files()
        meta_log.end_step(
            sid, "SUCCESS" if discovered else "FAILED",
            files_processed=len(discovered),
            message="; ".join(disc_errors) if disc_errors else None,
        )
        if not discovered:
            meta_log.update_run(run_id, "FAILED", "No files discovered")
            return run_id, False, "No files discovered from NUPRC sources"

        # 2. File acquisition (parallel downloads)
        sid = meta_log.start_step(run_id, "file_acquisition")
        acquired = _acquire_files(run_id, discovered, full_rebuild)
        meta_log.end_step(sid, "SUCCESS", files_processed=len(acquired))

        if not acquired:
            meta_log.update_run(run_id, "SUCCESS", "No new files to process", rows_loaded=0)
            return run_id, True, None

        # 3. Bronze load
        sid = meta_log.start_step(run_id, "bronze_load")
        bronze_rows = 0
        for item in acquired:
            n, _ = load_file_to_bronze(
                run_id,
                item["source_key"],
                item["source_name"],
                item["path"],
                item["url"],
                item["file_hash"],
            )
            bronze_rows += n
            mark_processed(item["file_hash"])
        meta_log.end_step(sid, "SUCCESS", rows_processed=bronze_rows, files_processed=len(acquired))

        # 4. Silver
        sid = meta_log.start_step(run_id, "silver_standardization")
        silver_rows = standardize_bronze_to_silver(run_id)
        meta_log.end_step(sid, "SUCCESS", rows_processed=silver_rows)

        # 5. Warehouse
        sid = meta_log.start_step(run_id, "warehouse_load")
        wh_rows = load_silver_to_warehouse(run_id)
        meta_log.end_step(sid, "SUCCESS", rows_processed=wh_rows)

        # 6. Data products
        sid = meta_log.start_step(run_id, "data_product_refresh")
        try:
            from app.models.data_catalog import refresh_available_tables
            refresh_available_tables()
        except Exception:
            pass
        save_diagrams(run_id)
        meta_log.end_step(sid, "SUCCESS")

        meta_log.update_run(run_id, "SUCCESS", rows_loaded=bronze_rows)
        return run_id, True, None

    except Exception as e:
        meta_log.log_line(run_id, "ERROR", str(e))
        meta_log.update_run(run_id, "FAILED", str(e))
        return run_id, False, traceback.format_exc()


def _acquire_files(
    run_id: str,
    discovered: list,
    full_rebuild: bool,
) -> List[dict]:
    """Download files in parallel; skip already processed when incremental."""
    to_fetch = []
    for f in discovered:
        to_fetch.append(f)

    def _download_one(f: dict) -> dict | None:
        sk = f["source_key"]
        url = f["url"]
        if sk == "concession":
            path, sha, err = download_concession_pdf(url, sk)
        else:
            path, sha, size, ct, err = download_file(url, sk, allowed_content_types=None)
        if err or not path:
            register_file(sha or "unknown", f["source_name"], url, None, f.get("file_type"), "FAILED", err)
            return None
        p = Path(path)
        fh = file_hash_path(p) if p.exists() else sha
        if is_processed(fh, full_rebuild):
            return None
        register_file(fh, f["source_name"], url, str(p), f.get("file_type"), "DOWNLOADED")
        return {
            "source_key": sk,
            "source_name": f["source_name"],
            "url": url,
            "path": p,
            "file_hash": fh,
        }

    acquired: List[dict] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_download_one, f): f for f in to_fetch}
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                acquired.append(result)
    return acquired
