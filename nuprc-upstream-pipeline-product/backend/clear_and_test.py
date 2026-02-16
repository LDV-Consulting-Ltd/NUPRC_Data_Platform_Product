#!/usr/bin/env python3
"""Clear stuck run and test pipeline execution."""
from app.core.db import engine
from sqlalchemy import text

# Clear all RUNNING runs
print("Clearing all stuck runs...")
with engine.begin() as cxn:
    result = cxn.execute(text("""
        UPDATE pipeline_run
        SET status = 'FAILED', ended_at = now(),
            message = 'Cleared for testing'
        WHERE status = 'RUNNING'
    """))
    print(f"✅ Cleared {result.rowcount} stuck run(s)")

# Test pipeline execution directly
print("\nTesting pipeline execution...")
from app.routers.pipeline import execute_pipeline
import uuid

test_run_id = str(uuid.uuid4())
print(f"Test run ID: {test_run_id}")
print("Calling execute_pipeline directly...\n")

try:
    execute_pipeline(test_run_id, ["oil_production_status"])
    print("\n✅ Pipeline execution completed!")
except Exception as e:
    print(f"\n❌ Pipeline execution failed: {e}")
    import traceback
    traceback.print_exc()
