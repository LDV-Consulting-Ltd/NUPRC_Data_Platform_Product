"""
Warehouse tables endpoint: list bronze, silver, warehouse, and meta tables with row counts.
"""
from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/warehouse", tags=["warehouse"])

_LAYERS = [
    ("meta", "meta"),
    ("bronze", "bronze"),
    ("silver", "silver"),
    ("warehouse", "warehouse"),
]


# Canonical tables with data (legacy ETL path — primary source of row counts today)
_PRIORITY_TABLES = {
    "bronze": {
        "etl_oil_production_raw",
        "etl_gas_production_raw",
        "etl_rig_disposition_raw",
        "etl_concessions_raw",
        "etl_concessions_sections",
        "oil_production_status_raw",
        "gas_production_status_raw",
        "rig_disposition_raw",
        "concession_situation_raw",
    },
    "silver": {
        "fact_oil_production",
        "fact_gas_production",
        "fact_rig_disposition",
        "fact_concession_status",
        "upstream_activity_standardized",
        "dim_date",
        "dim_operator",
    },
    "warehouse": {
        "fact_oil_production",
        "fact_gas_production",
        "fact_rig_disposition",
        "fact_concession_status",
        "fact_upstream_activity",
        "fact_production",
        "dim_operator",
        "dim_date",
    },
    "meta": {
        "pipeline_run",
        "pipeline_step_log",
        "pipeline_log",
        "file_registry",
        "schema_drift",
        "pipeline_diagrams",
    },
}


@router.get("/tables")
def list_warehouse_tables(non_empty: bool = True):
    tables_info = []
    with engine.connect() as cxn:
        for schema, layer in _LAYERS:
            try:
                rows = cxn.execute(
                    text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """),
                    {"schema": schema},
                ).mappings().all()
            except Exception:
                rows = []
            for r in rows:
                tname = r["table_name"]
                full = f"{schema}.{tname}"
                try:
                    count = cxn.execute(text(f"SELECT COUNT(*) FROM {full}")).scalar() or 0
                except Exception as e:
                    count = 0
                    err = str(e)
                else:
                    err = None
                entry = {
                    "schema": schema,
                    "table_name": tname,
                    "full_name": full,
                    "row_count": int(count),
                    "layer": layer,
                    "canonical": tname in _PRIORITY_TABLES.get(schema, set()),
                    **({"error": err} if err else {}),
                }
                if non_empty and int(count) == 0:
                    continue
                tables_info.append(entry)
    tables_info.sort(key=lambda t: (-t["row_count"], t["layer"], t["table_name"]))
    return {"ok": True, "tables": tables_info, "non_empty": non_empty}
