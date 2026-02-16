#!/usr/bin/env python3
"""
Clear a stuck pipeline run.
Usage: python clear_stuck_run.py <run_id>
Or: python clear_stuck_run.py --all (clears all RUNNING runs)
"""
import sys
from app.core.db import engine
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

def clear_run(run_id: str):
    """Mark a specific run as failed."""
    with engine.begin() as cxn:
        result = cxn.execute(text("""
            UPDATE pipeline_run
            SET status = 'FAILED', ended_at = now(),
                message = 'Manually cleared stuck run'
            WHERE run_id = :rid
        """), {"rid": run_id})
        
        if result.rowcount > 0:
            print(f"✅ Cleared run {run_id}")
        else:
            print(f"❌ Run {run_id} not found")

def clear_all_stuck():
    """Clear all RUNNING runs."""
    with engine.begin() as cxn:
        runs = cxn.execute(text("""
            SELECT run_id, pipeline_name, started_at
            FROM pipeline_run
            WHERE status = 'RUNNING'
        """)).mappings().all()
        
        if not runs:
            print("No running pipelines found")
            return
        
        print(f"Found {len(runs)} running pipeline(s):")
        for run in runs:
            print(f"  - {run['run_id']}: {run['pipeline_name']} (started: {run['started_at']})")
        
        result = cxn.execute(text("""
            UPDATE pipeline_run
            SET status = 'FAILED', ended_at = now(),
                message = 'Manually cleared all stuck runs'
            WHERE status = 'RUNNING'
        """))
        
        print(f"✅ Cleared {result.rowcount} stuck run(s)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            clear_all_stuck()
        else:
            clear_run(sys.argv[1])
    else:
        print("Usage: python clear_stuck_run.py <run_id>")
        print("   or: python clear_stuck_run.py --all")
        print("\nCurrent running runs:")
        with engine.connect() as cxn:
            runs = cxn.execute(text("""
                SELECT run_id, pipeline_name, started_at
                FROM pipeline_run
                WHERE status = 'RUNNING'
                ORDER BY started_at DESC
            """)).mappings().all()
            for run in runs:
                print(f"  {run['run_id']}: {run['pipeline_name']}")
