"""Knowledge asset service — index existing docs and glossaries only (v0.2.1)."""
from app.tanna_connector.adapters import diagrams_adapter, docs_adapter
from app.tanna_connector.config import MODULE_ID, OWNER, PRIMARY_GOLD_TABLES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import knowledge_asset_id

GOLD_PRODUCT_IDS = [meta["id"] for meta in PRIMARY_GOLD_TABLES.values()]


def get_knowledge_assets() -> dict:
    warnings: list[str] = []
    items: list[dict] = []

    docs, w = docs_adapter.scan_markdown_docs()
    warnings.extend(w)
    for doc in docs:
        name = doc["asset_id"].replace("doc:", "")
        eid = knowledge_asset_id("documentation", name)
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "title": doc["title"],
            "asset_type": doc.get("asset_type", "documentation"),
            "description": doc.get("summary"),
            "owner": OWNER,
            "status": "active",
            "linked_data_products": [],
            "linked_entities": [],
            "linked_decision_products": [],
            "content_url": doc.get("path"),
            "content_text": doc.get("content_text"),
            "source": doc.get("source"),
        })

    glossary, w = docs_adapter.get_table_display_glossary()
    warnings.extend(w)
    for g in glossary:
        table_name = g["asset_id"].replace("glossary:table:", "")
        eid = knowledge_asset_id("table_display", table_name)
        linked = [g["linked_data_product_id"]] if g.get("linked_data_product_id") else []
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "title": g["title"],
            "asset_type": g.get("asset_type", "metadata/TABLE_DISPLAY"),
            "description": g.get("summary"),
            "owner": OWNER,
            "status": "active",
            "linked_data_products": linked,
            "linked_entities": [],
            "linked_decision_products": [],
            "content_url": g.get("path"),
        })

    columns, w = docs_adapter.get_canonical_columns_glossary()
    warnings.extend(w)
    for c in columns:
        col_name = c["asset_id"].replace("glossary:column:", "")
        eid = knowledge_asset_id("canonical_columns", col_name)
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "title": c["title"],
            "asset_type": c.get("asset_type", "metadata/CANONICAL_COLUMNS"),
            "description": c.get("summary"),
            "owner": OWNER,
            "status": "active",
            "linked_data_products": [],
            "linked_entities": [],
            "linked_decision_products": [],
            "content_url": c.get("path"),
        })

    diagram, w = diagrams_adapter.get_latest_diagram()
    warnings.extend(w)
    if diagram:
        eid = knowledge_asset_id("er_diagram", "pipeline_diagrams_latest")
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "title": "PetroCore Data Model ER Diagram",
            "asset_type": "metadata/ER_diagram",
            "description": (
                f"Latest Mermaid ER diagram from pipeline_diagrams "
                f"(id={diagram.get('id', 'latest')})"
            ),
            "owner": OWNER,
            "status": "active",
            "linked_data_products": GOLD_PRODUCT_IDS,
            "linked_entities": [],
            "linked_decision_products": [],
            "content_url": "/diagrams/latest",
            "content_text": (diagram.get("diagram_content") or "")[:500] or None,
        })
    else:
        mermaid, w2 = diagrams_adapter.get_static_mermaid_fallback()
        warnings.extend(w2)
        if mermaid:
            eid = knowledge_asset_id("er_diagram", "static_fallback")
            items.append({
                "id": eid,
                "external_id": eid,
                "module_id": MODULE_ID,
                "title": "PetroCore Static ER Diagram",
                "asset_type": "metadata/ER_diagram",
                "description": "Generated from diagram_generator (no DB diagram stored)",
                "owner": OWNER,
                "status": "active",
                "linked_data_products": GOLD_PRODUCT_IDS,
                "linked_entities": [],
                "linked_decision_products": [],
                "content_text": mermaid[:500] if mermaid else None,
            })

    return build_envelope(
        object_type="knowledge_assets",
        implementation_status="partial",
        items=items,
        source="README, ABOUT, ETL/pipeline/troubleshooting docs, TABLE_DISPLAY, CANONICAL_COLUMNS, ER diagram",
        notes="Read/index only. Documentation is not ingested, rewritten, or stored in a new database.",
        warnings=warnings,
    )
