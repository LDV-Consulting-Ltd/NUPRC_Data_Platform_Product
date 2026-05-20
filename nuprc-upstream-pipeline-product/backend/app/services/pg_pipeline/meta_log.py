"""Pipeline run and step logging in meta schema."""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text

from app.core.db import engine

PIPELINE_NAME = "nuprc_upstream"

STEPS = [
    "source_discovery",
    "file_acquisition",
    "bronze_load",
    "silver_standardization",
    "warehouse_load",
    "data_product_refresh",
]


def create_run(run_id: str, status: str = "QUEUED") -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO meta.pipeline_run (run_id, pipeline_name, status)
                VALUES (:run_id, :name, :status)
            """),
            {"run_id": run_id, "name": PIPELINE_NAME, "status": status},
        )


def update_run(
    run_id: str,
    status: str,
    message: Optional[str] = None,
    rows_loaded: Optional[int] = None,
) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                UPDATE meta.pipeline_run
                SET status = :status,
                    message = COALESCE(:message, message),
                    rows_loaded = COALESCE(:rows, rows_loaded),
                    ended_at = CASE WHEN :status IN ('SUCCESS', 'FAILED', 'CANCELLED')
                        THEN now() ELSE ended_at END
                WHERE run_id = :run_id
            """),
            {"run_id": run_id, "status": status, "message": message, "rows": rows_loaded},
        )


def log_line(run_id: str, level: str, message: str) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO meta.pipeline_log (run_id, level, message)
                VALUES (:run_id, :level, :message)
            """),
            {"run_id": run_id, "level": level, "message": message},
        )


def start_step(run_id: str, step_name: str) -> int:
    with engine.begin() as cxn:
        r = cxn.execute(
            text("""
                INSERT INTO meta.pipeline_step_log (run_id, step_name, status)
                VALUES (:run_id, :step, 'RUNNING')
                RETURNING id
            """),
            {"run_id": run_id, "step": step_name},
        )
        return int(r.scalar_one())


def end_step(
    step_id: int,
    status: str,
    rows_processed: int = 0,
    files_processed: int = 0,
    message: Optional[str] = None,
) -> None:
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                UPDATE meta.pipeline_step_log
                SET status = :status,
                    ended_at = now(),
                    duration_seconds = EXTRACT(EPOCH FROM (now() - started_at)),
                    rows_processed = :rows,
                    files_processed = :files,
                    message = :message
                WHERE id = :id
            """),
            {
                "id": step_id,
                "status": status,
                "rows": rows_processed,
                "files": files_processed,
                "message": message,
            },
        )


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    with engine.connect() as cxn:
        run = cxn.execute(
            text("SELECT * FROM meta.pipeline_run WHERE run_id = :id"),
            {"id": run_id},
        ).mappings().first()
        if not run:
            return None
        steps = cxn.execute(
            text("""
                SELECT * FROM meta.pipeline_step_log
                WHERE run_id = :id ORDER BY started_at
            """),
            {"id": run_id},
        ).mappings().all()
        drift = cxn.execute(
            text("""
                SELECT * FROM meta.schema_drift
                WHERE run_id = :id ORDER BY detected_at
            """),
            {"id": run_id},
        ).mappings().all()
    return {
        "run": dict(run),
        "steps": [dict(s) for s in steps],
        "schema_drift": [dict(d) for d in drift],
    }
