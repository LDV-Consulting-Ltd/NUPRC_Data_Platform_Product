"""Data products service — gold marts from catalog registry only."""
from typing import Any

from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import MODULE_ID, PRIMARY_GOLD_TABLES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import data_product_id


def _parse_dt(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def get_data_products() -> dict:
    warnings: list[str] = []
    gold_tables, w = catalog_adapter.get_gold_tables()
    warnings.extend(w)
    table_display, w2 = catalog_adapter.get_table_display()
    warnings.extend(w2)
    by_name = {t["physical_name"]: t for t in gold_tables}
    items: list[dict] = []
    seen: set[str] = set()

    for table_name, meta in PRIMARY_GOLD_TABLES.items():
        info = by_name.get(table_name, {})
        display = table_display.get(table_name, {})
        row_count = info.get("row_count") or 0
        eid = meta["id"]
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "name": display.get("display_name") or table_name,
            "description": info.get("description") or display.get("display_name"),
            "domain": meta["domain"],
            "classification": "analytical_data_product",
            "business_owner": "LDV",
            "technical_owner": "PetroCore Data Engineering",
            "steward": "Upstream Regulatory Intelligence",
            "source_systems": ["NUPRC Upstream Reports"],
            "quality_status": "monitored" if row_count > 0 else "unknown",
            "refresh_frequency": "daily",
            "lifecycle_stage": "active",
            "latest_refresh_at": _parse_dt(info.get("last_updated")),
            "tags": [meta["domain"].lower(), "gold", table_name],
            "backing_table": f"gold.{table_name}",
            "row_count": row_count,
        })
        seen.add(table_name)

    for table_name, info in by_name.items():
        if table_name in seen or not table_name.startswith("gold_"):
            continue
        display = table_display.get(table_name, {})
        eid = data_product_id(table_name)
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "name": display.get("display_name") or table_name,
            "description": info.get("description"),
            "domain": display.get("subject_area"),
            "classification": "analytical_data_product",
            "source_systems": ["NUPRC Upstream Reports"],
            "quality_status": "monitored" if (info.get("row_count") or 0) > 0 else "unknown",
            "lifecycle_stage": "active",
            "latest_refresh_at": _parse_dt(info.get("last_updated")),
            "tags": ["gold", table_name],
            "backing_table": f"gold.{table_name}",
            "row_count": info.get("row_count") or 0,
        })

    return build_envelope(
        object_type="data_products",
        implementation_status="implemented",
        items=items,
        source="catalog_registry.get_tables_for_layer(gold) + TABLE_DISPLAY",
        notes="Only real gold marts are exposed. No invented Field/Asset Performance products.",
        warnings=warnings,
    )
