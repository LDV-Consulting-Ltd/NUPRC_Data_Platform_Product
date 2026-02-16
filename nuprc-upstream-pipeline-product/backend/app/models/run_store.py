from sqlalchemy import text
from app.core.db import engine

def init_run_tables():
    with engine.begin() as cxn:
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_run (
          run_id TEXT PRIMARY KEY,
          pipeline_name TEXT NOT NULL,
          status TEXT NOT NULL,
          started_at TEXT DEFAULT (CURRENT_TIMESTAMP),
          ended_at TEXT NULL,
          rows_loaded INTEGER DEFAULT 0,
          message TEXT NULL
        )
        """))
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id TEXT NOT NULL,
          ts TEXT DEFAULT (CURRENT_TIMESTAMP),
          level TEXT NOT NULL,
          message TEXT NOT NULL
        )
        """))

def log(run_id: str, level: str, message: str):
    with engine.begin() as cxn:
        cxn.execute(text("""
          INSERT INTO pipeline_log (run_id, level, message)
          VALUES (:run_id, :level, :message)
        """), {"run_id": run_id, "level": level, "message": message})

def set_run(run_id: str, pipeline_name: str, status: str, message: str | None = None):
    with engine.begin() as cxn:
        cxn.execute(text("""
          INSERT INTO pipeline_run (run_id, pipeline_name, status, message)
          VALUES (:run_id, :pipeline_name, :status, :message)
          ON CONFLICT(run_id) DO UPDATE SET
            pipeline_name=excluded.pipeline_name,
            status=excluded.status,
            message=excluded.message
        """), {"run_id": run_id, "pipeline_name": pipeline_name, "status": status, "message": message})
