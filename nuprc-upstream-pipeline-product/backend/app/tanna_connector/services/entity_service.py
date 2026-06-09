"""Entity service — read-only from confirmed dimension tables and catalog."""
from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import MODULE_ID, PRIMARY_GOLD_TABLES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import entity_id


def get_entities() -> dict:
    warnings: list[str] = []
    items: list[dict] = []
    type_summaries: list[dict] = []
    seen_operators: set[str] = set()

    oil_dp = PRIMARY_GOLD_TABLES["gold_oil_fact_production"]["id"]

    for schema, table, name_col in [
        ("gold", "gold_oil_dim_operator", "operator_name"),
        ("gold", "gold_gas_dim_operator", "operator_name"),
        ("gold", "gold_rig_dim_operator", "operator_name"),
    ]:
        rows, total, w = catalog_adapter.fetch_entity_rows(schema, table, 100, 0)
        warnings.extend(w)
        type_summaries.append({
            "entity_type": "operator",
            "backing_table": f"{schema}.{table}",
            "count": total,
            "instance_limit": 100,
        })
        for row in rows:
            name = row.get(name_col) or row.get("operator_name")
            if not name or name in seen_operators:
                continue
            seen_operators.add(name)
            eid = entity_id("operator", name)
            items.append({
                "id": eid,
                "external_id": eid,
                "module_id": MODULE_ID,
                "entity_type": "operator",
                "entity_name": str(name),
                "description": "Operator from PetroCore gold dimension",
                "domain": "Oil & Gas",
                "attributes": {k: v for k, v in row.items()},
                "source_data_product_id": oil_dp,
                "status": "active",
                "tags": ["operator"],
            })

    concession_dp = PRIMARY_GOLD_TABLES["gold_concession_fact_snapshot"]["id"]
    rows, total, w = catalog_adapter.fetch_entity_rows("gold", "gold_concession_dim_concession", 100, 0)
    warnings.extend(w)
    type_summaries.append({
        "entity_type": "concession",
        "backing_table": "gold.gold_concession_dim_concession",
        "count": total,
        "instance_limit": 100,
    })
    for row in rows:
        name = row.get("concession_category_full") or row.get("concession_no") or row.get("company_operator_name")
        if not name:
            continue
        eid = entity_id("concession", name)
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "entity_type": "concession",
            "entity_name": str(name),
            "description": "Concession register entry",
            "domain": "Concessions",
            "attributes": {k: v for k, v in row.items()},
            "source_data_product_id": concession_dp,
            "status": "active",
            "tags": ["concession"],
        })

    rig_dp = PRIMARY_GOLD_TABLES["gold_rig_fact_activity"]["id"]
    rows, total, w = catalog_adapter.fetch_entity_rows("gold", "gold_rig_dim_rig", 100, 0)
    warnings.extend(w)
    type_summaries.append({
        "entity_type": "rig",
        "backing_table": "gold.gold_rig_dim_rig",
        "count": total,
        "instance_limit": 100,
    })
    for row in rows:
        name = row.get("rig_name")
        if not name:
            continue
        eid = entity_id("rig", name)
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "entity_type": "rig",
            "entity_name": str(name),
            "description": "Rig dimension from rig disposition mart",
            "domain": "Rigs",
            "attributes": {k: v for k, v in row.items()},
            "source_data_product_id": rig_dp,
            "status": "active",
            "tags": ["rig"],
        })

    try:
        from app.services.sources import get_all_sources
        sources = get_all_sources()
        type_summaries.append({
            "entity_type": "upstream_source",
            "backing_table": "sources.py configuration",
            "count": len(sources),
        })
        for source in sources:
            eid = entity_id("upstream_source", source.source_id)
            items.append({
                "id": eid,
                "external_id": eid,
                "module_id": MODULE_ID,
                "entity_type": "upstream_source",
                "entity_name": source.name,
                "description": source.description,
                "domain": "Regulatory Sources",
                "attributes": {
                    "source_id": source.source_id,
                    "base_url": source.base_url,
                    "bronze_table": source.bronze_table,
                },
                "status": "active",
                "tags": ["source", source.source_id],
            })
    except Exception as exc:
        warnings.append(f"Upstream sources unavailable: {exc}")

    docs, doc_total, w = catalog_adapter.get_ingested_documents(50, 0)
    warnings.extend(w)
    type_summaries.append({
        "entity_type": "ingested_document",
        "backing_table": "data_catalog.downloaded_files",
        "count": doc_total,
        "instance_limit": 50,
    })
    for row in docs:
        sha = row.get("file_sha256") or row.get("filename")
        if not sha:
            continue
        eid = entity_id("ingested_document", str(sha)[:16])
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "entity_type": "ingested_document",
            "entity_name": str(row.get("filename") or sha),
            "description": "Downloaded NUPRC source file in data catalog",
            "domain": "Catalog",
            "attributes": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()},
            "status": "active",
            "tags": ["catalog", str(row.get("source_id", ""))],
        })

    asset_count, w = catalog_adapter.safe_count("warehouse", "dim_asset")
    warnings.extend(w)
    if asset_count is not None and asset_count > 0:
        asset_rows, _, w2 = catalog_adapter.fetch_entity_rows("warehouse", "dim_asset", 100, 0)
        warnings.extend(w2)
        type_summaries.append({
            "entity_type": "asset",
            "backing_table": "warehouse.dim_asset",
            "count": asset_count,
            "instance_limit": 100,
        })
        for row in asset_rows:
            name = row.get("asset_name")
            if not name:
                continue
            eid = entity_id("asset", name)
            items.append({
                "id": eid,
                "external_id": eid,
                "module_id": MODULE_ID,
                "entity_type": "asset",
                "entity_name": str(name),
                "description": "Asset from legacy warehouse.dim_asset (when populated)",
                "domain": "Assets",
                "attributes": {k: v for k, v in row.items()},
                "status": "active",
                "tags": ["asset", "warehouse"],
            })

    envelope_items = items if items else type_summaries
    notes = (
        "Entity instances are sampled read-only rows (max 100 per type). "
        "No invented Shell/Chevron/Bonga/Field/Terminal/License entities."
    )
    if not items and type_summaries:
        notes += " Only entity type summaries available when DB instances are empty."

    return build_envelope(
        object_type="entities",
        implementation_status="partial",
        items=envelope_items,
        source="gold dimensions, sources.py, data_catalog.downloaded_files, warehouse.dim_asset",
        notes=notes,
        warnings=warnings,
    )
