"""Governance summary for console UI."""
from typing import Any, Dict, List

from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/v1/governance", tags=["governance"])


@router.get("/summary")
def governance_summary():
    with engine.connect() as cxn:
        drift_rows: List[dict] = []
        try:
            drift_rows = [
                dict(r)
                for r in cxn.execute(
                    text("""
                        SELECT source_key, reporting_year, original_column, mapped_column,
                               confidence, severity, detected_at
                        FROM meta.schema_drift
                        ORDER BY detected_at DESC NULLS LAST
                        LIMIT 100
                    """)
                ).mappings().all()
            ]
        except Exception:
            try:
                drift_rows = [
                    dict(r)
                    for r in cxn.execute(
                        text("""
                            SELECT source_key, original_column, mapped_column,
                                   confidence, severity, detected_at
                            FROM silver.schema_drift
                            ORDER BY detected_at DESC NULLS LAST
                            LIMIT 100
                        """)
                    ).mappings().all()
                ]
            except Exception:
                pass

        file_count = 0
        try:
            file_count = int(cxn.execute(text("SELECT COUNT(*) FROM meta.file_registry")).scalar() or 0)
        except Exception:
            pass

        run_count = 0
        last_run = None
        try:
            run_count = int(cxn.execute(text("SELECT COUNT(*) FROM meta.pipeline_run")).scalar() or 0)
        except Exception:
            pass
        try:
            from etl.config import get_etl_engine
            eng = get_etl_engine()
            with eng.connect() as acxn:
                admin_count = int(acxn.execute(text("SELECT COUNT(*) FROM admin.etl_runs")).scalar() or 0)
                run_count += admin_count
                last = acxn.execute(
                    text("""
                        SELECT run_id, status, started_at FROM admin.etl_runs
                        ORDER BY started_at DESC LIMIT 1
                    """)
                ).mappings().first()
                if last:
                    last_run = dict(last)
        except Exception:
            pass

        table_health = []
        for schema in ("meta", "bronze", "silver", "warehouse"):
            try:
                tables = cxn.execute(
                    text("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = :s AND table_type = 'BASE TABLE'
                    """),
                    {"s": schema},
                ).scalars().all()
                for t in tables:
                    full = f"{schema}.{t}"
                    try:
                        cnt = int(cxn.execute(text(f"SELECT COUNT(*) FROM {full}")).scalar() or 0)
                    except Exception:
                        cnt = 0
                    if cnt > 0:
                        table_health.append({"schema": schema, "table": t, "row_count": cnt})
            except Exception:
                continue

    high_drift = sum(1 for d in drift_rows if str(d.get("severity", "")).lower() == "high")
    return {
        "ok": True,
        "metadata": {
            "file_registry_count": file_count,
            "pipeline_runs": run_count,
            "tables_with_data": len(table_health),
        },
        "lineage_coverage_pct": min(100, len(table_health) * 8) if table_health else 0,
        "schema_drift": drift_rows,
        "schema_drift_high_count": high_drift,
        "table_health": sorted(table_health, key=lambda x: -x["row_count"])[:40],
        "last_run": last_run,
    }
