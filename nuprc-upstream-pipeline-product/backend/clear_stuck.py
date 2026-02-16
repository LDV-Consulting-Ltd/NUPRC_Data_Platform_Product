#!/usr/bin/env python3
"""Clear all stuck RUNNING pipeline runs."""
from app.core.db import engine
from sqlalchemy import text

print("Clearing all stuck RUNNING pipeline runs...")
with engine.begin() as cxn:
    result = cxn.execute(text("""
        UPDATE pipeline_run
        SET status = 'FAILED', ended_at = now(),
            message = 'Cleared stuck run - was running for too long'
        WHERE status = 'RUNNING'
    """))
    print(f"[OK] Cleared {result.rowcount} stuck run(s)")

# Show current status
print("\nCurrent pipeline runs:")
with engine.connect() as cxn:
    runs = cxn.execute(text("""
        SELECT run_id, pipeline_name, status, started_at
        FROM pipeline_run
        ORDER BY started_at DESC
        LIMIT 5
    """)).mappings().all()
    for run in runs:
        print(f"  {run['run_id'][:8]}... | {run['status']:10} | {run['pipeline_name']}")
