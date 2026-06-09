from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import PRIMARY_DATA_PRODUCTS
from app.tanna_connector.schemas.data_product import DataProductItem, DataProductsResponse


def build_data_products() -> DataProductsResponse:
    warnings: list[str] = []
    gold_tables, w = catalog_adapter.get_gold_tables()
    warnings.extend(w)
    table_display, w2 = catalog_adapter.get_table_display()
    warnings.extend(w2)

    by_name = {t["physical_name"]: t for t in gold_tables}
    items: list[DataProductItem] = []

    for table_name, product_id in PRIMARY_DATA_PRODUCTS.items():
        meta = table_display.get(table_name, {})
        table_info = by_name.get(table_name, {})
        row_count = table_info.get("row_count")
        if table_info:
            status = "available" if (row_count or 0) > 0 else "degraded"
        else:
            status = "unavailable"
            warnings.append(f"Gold table {table_name} not found in catalog")

        items.append(DataProductItem(
            product_id=product_id,
            name=product_id.split(".", 1)[-1],
            display_name=meta.get("display_name") or table_info.get("display_name"),
            subject_area=meta.get("subject_area") or table_info.get("subject_area"),
            grain=meta.get("grain") or table_info.get("grain"),
            description=table_info.get("description") or meta.get("display_name"),
            table_name=table_name,
            status=status,
            row_count=row_count,
            last_updated=table_info.get("last_updated"),
        ))

    # Include other gold tables not in primary mapping
    for table_name, table_info in by_name.items():
        if table_name in PRIMARY_DATA_PRODUCTS:
            continue
        meta = table_display.get(table_name, {})
        row_count = table_info.get("row_count")
        items.append(DataProductItem(
            product_id=f"petrocore.{table_name.replace('gold_', '').replace('_', '-')}",
            name=table_name,
            display_name=meta.get("display_name") or table_info.get("display_name"),
            subject_area=meta.get("subject_area"),
            grain=meta.get("grain"),
            description=table_info.get("description"),
            table_name=table_name,
            status="available" if (row_count or 0) > 0 else "degraded",
            row_count=row_count,
            last_updated=table_info.get("last_updated"),
        ))

    status = "available" if items else "degraded"
    return DataProductsResponse(status=status, items=items, warnings=warnings)
