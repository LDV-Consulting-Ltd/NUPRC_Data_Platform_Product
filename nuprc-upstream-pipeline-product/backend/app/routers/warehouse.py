"""
Legacy warehouse tables endpoint. Returns same canonical tables as v1 catalog:
Bronze: etl_* tables; Warehouse (Gold): gold_* tables with correct row counts.
Used by legacy Datawarehouse Tables UI.
"""
from fastapi import APIRouter

from app.services.catalog_registry import get_engine_for_layer, get_tables_for_layer

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.get("/tables")
def list_warehouse_tables():
    """
    List bronze and warehouse (gold) tables with row counts.
    Proxies v1 catalog: canonical etl_* for bronze, gold_* for warehouse.
    No legacy table names (oil_production_status_raw, etc.).
    """
    tables_info = []
    # Bronze layer
    try:
        engine_bronze = get_engine_for_layer("bronze")
        bronze_tables = get_tables_for_layer(engine_bronze, "bronze", include_deprecated=False)
        for t in bronze_tables:
            tables_info.append({
                "schema": "bronze",
                "table_name": t["physical_name"],
                "full_name": f"bronze.{t['physical_name']}",
                "row_count": t["row_count"],
                "layer": "bronze",
            })
    except Exception:
        pass
    # Warehouse layer = Gold (dimensional model)
    try:
        engine_gold = get_engine_for_layer("gold")
        gold_tables = get_tables_for_layer(engine_gold, "gold", include_deprecated=False)
        for t in gold_tables:
            tables_info.append({
                "schema": "gold",
                "table_name": t["physical_name"],
                "full_name": f"gold.{t['physical_name']}",
                "row_count": t["row_count"],
                "layer": "warehouse",  # legacy UI expects "warehouse"
            })
    except Exception:
        pass
    return {"ok": True, "tables": tables_info}
