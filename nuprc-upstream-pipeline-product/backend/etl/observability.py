"""
Observability: etl_runs and etl_run_steps.
Create tables in admin schema (or public if preferred); use single DB engine.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import text

from etl.config import get_etl_engine


def init_observability_schema(engine=None):
    engine = engine or get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(text("CREATE SCHEMA IF NOT EXISTS admin;"))
        cxn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin.etl_runs (
                run_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ DEFAULT now(),
                ended_at TIMESTAMPTZ,
                triggered_by TEXT,
                meta_json JSONB
            );
        """))
        cxn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin.etl_run_steps (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                run_id TEXT NOT NULL,
                step_key TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ DEFAULT now(),
                ended_at TIMESTAMPTZ,
                metrics_json JSONB,
                error_json JSONB
            );
        """))
        cxn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_etl_run_steps_run_id
            ON admin.etl_run_steps(run_id);
        """))


def start_run(mode: str, triggered_by: str = "api", meta: Optional[dict] = None) -> str:
    run_id = str(uuid.uuid4())
    engine = get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO admin.etl_runs (run_id, mode, status, triggered_by, meta_json)
                VALUES (:run_id, :mode, 'running', :triggered_by, :meta)
            """),
            {
                "run_id": run_id,
                "mode": mode,
                "triggered_by": triggered_by,
                "meta": json.dumps(meta or {}),
            },
        )
    return run_id


def create_run(run_id: str, mode: str, triggered_by: str = "api", meta: Optional[dict] = None) -> None:
    """Insert a run with the given run_id (for API callers who generate run_id themselves)."""
    engine = get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO admin.etl_runs (run_id, mode, status, triggered_by, meta_json)
                VALUES (:run_id, :mode, 'running', :triggered_by, :meta)
            """),
            {
                "run_id": run_id,
                "mode": mode,
                "triggered_by": triggered_by,
                "meta": json.dumps(meta or {}),
            },
        )


def end_run(run_id: str, status: str = "success", meta: Optional[dict] = None):
    engine = get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                UPDATE admin.etl_runs
                SET status = :status, ended_at = now(),
                    meta_json = COALESCE(CAST(:meta AS jsonb), meta_json)
                WHERE run_id = :run_id
            """),
            {"run_id": run_id, "status": status, "meta": json.dumps(meta or {})},
        )


def start_step(run_id: str, step_key: str) -> None:
    engine = get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                INSERT INTO admin.etl_run_steps (run_id, step_key, status)
                VALUES (:run_id, :step_key, 'running')
            """),
            {"run_id": run_id, "step_key": step_key},
        )


def end_step(
    run_id: str,
    step_key: str,
    status: str = "success",
    metrics: Optional[dict] = None,
    error: Optional[dict] = None,
):
    engine = get_etl_engine()
    with engine.begin() as cxn:
        cxn.execute(
            text("""
                UPDATE admin.etl_run_steps
                SET status = :status, ended_at = now(),
                    metrics_json = COALESCE(CAST(:metrics AS jsonb), metrics_json),
                    error_json = CAST(:error AS jsonb)
                WHERE run_id = :run_id AND step_key = :step_key
                AND ended_at IS NULL
            """),
            {
                "run_id": run_id,
                "step_key": step_key,
                "status": status,
                "metrics": json.dumps(metrics or {}),
                "error": json.dumps(error) if error else "null",
            },
        )


def get_run(run_id: str) -> Optional[dict]:
    engine = get_etl_engine()
    with engine.connect() as cxn:
        row = cxn.execute(
            text("""
                SELECT run_id, mode, status, started_at, ended_at, triggered_by, meta_json
                FROM admin.etl_runs WHERE run_id = :run_id
            """),
            {"run_id": run_id},
        ).mappings().first()
    return dict(row) if row else None


def get_run_steps(run_id: str) -> list:
    engine = get_etl_engine()
    with engine.connect() as cxn:
        rows = cxn.execute(
            text("""
                SELECT step_key, status, started_at, ended_at, metrics_json, error_json
                FROM admin.etl_run_steps WHERE run_id = :run_id ORDER BY started_at
            """),
            {"run_id": run_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def get_run_diagnostics(run_id: str) -> dict:
    run = get_run(run_id)
    if not run:
        return {"found": False, "run_id": run_id}
    steps = get_run_steps(run_id)
    return {
        "found": True,
        "run_id": run_id,
        "run": run,
        "steps": steps,
    }


def cancel_run(run_id: str) -> bool:
    """Mark run as cancelled. Returns True if run was running and is now cancelled."""
    engine = get_etl_engine()
    with engine.begin() as cxn:
        result = cxn.execute(
            text("""
                UPDATE admin.etl_runs
                SET status = 'cancelled', ended_at = now(),
                    meta_json = COALESCE(meta_json, '{}'::jsonb) || '{"cancelled": true}'::jsonb
                WHERE run_id = :run_id AND status = 'running'
                RETURNING run_id
            """),
            {"run_id": run_id},
        )
        return result.fetchone() is not None
