import uuid
from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/runs", tags=["runs"])

def _mark_success(run_id: str, rows_loaded: int):
    with engine.begin() as cxn:
        cxn.execute(text("""
            UPDATE pipeline_run
            SET status='SUCCESS', ended_at=now(), rows_loaded=:rows, message=NULL
            WHERE run_id=:rid
        """), {"rid": run_id, "rows": int(rows_loaded or 0)})

def _mark_failed(run_id: str, err: Exception):
    msg = str(err)
    if len(msg) > 2000:
        msg = msg[:2000] + "…"
    with engine.begin() as cxn:
        cxn.execute(text("""
            UPDATE pipeline_run
            SET status='FAILED', ended_at=now(), message=:msg
            WHERE run_id=:rid
        """), {"rid": run_id, "msg": msg})

@router.get("/summary")
def runs_summary():
    with engine.connect() as cxn:
        total = int(cxn.execute(text("SELECT COUNT(*) FROM pipeline_run")).scalar() or 0)
        success = int(cxn.execute(text("SELECT COUNT(*) FROM pipeline_run WHERE status='SUCCESS'")).scalar() or 0)
        failed = int(cxn.execute(text("SELECT COUNT(*) FROM pipeline_run WHERE status='FAILED'")).scalar() or 0)
        running = int(cxn.execute(text("SELECT COUNT(*) FROM pipeline_run WHERE status='RUNNING'")).scalar() or 0)
        last = cxn.execute(text("""
            SELECT run_id, pipeline_name, status, started_at, ended_at, rows_loaded, message
            FROM pipeline_run
            ORDER BY started_at DESC
            LIMIT 1
        """)).mappings().first()

    return {"ok": True, "total_runs": total, "success": success, "failed": failed, "running": running, "last_run": dict(last) if last else None}

@router.get("/")
def list_runs():
    with engine.connect() as cxn:
        rows = cxn.execute(text("""
            SELECT run_id, pipeline_name, status, started_at, ended_at, rows_loaded, message
            FROM pipeline_run
            ORDER BY started_at DESC
            LIMIT 50
        """)).mappings().all()
    return {"ok": True, "runs": rows}
