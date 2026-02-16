# backend/app/models/run_store.py
from sqlalchemy import text
from app.core.db import engine

def init_run_tables():
    with engine.begin() as cxn:
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_run (
          run_id TEXT PRIMARY KEY,
          pipeline_name TEXT NOT NULL,
          status TEXT NOT NULL,
          started_at TIMESTAMPTZ DEFAULT now(),
          ended_at TIMESTAMPTZ NULL,
          rows_loaded BIGINT DEFAULT 0,
          message TEXT NULL
        );
        """))

        # ✅ Postgres identity instead of AUTOINCREMENT
        cxn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_log (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          run_id TEXT NOT NULL,
          ts TIMESTAMPTZ DEFAULT now(),
          level TEXT NOT NULL,
          message TEXT NOT NULL
        );
        """))
