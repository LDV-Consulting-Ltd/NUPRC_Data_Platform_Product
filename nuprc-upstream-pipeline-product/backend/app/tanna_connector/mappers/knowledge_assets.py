from app.tanna_connector.adapters import diagrams_adapter, docs_adapter
from app.tanna_connector.schemas.knowledge_asset import KnowledgeAssetItem, KnowledgeAssetsResponse


def build_knowledge_assets() -> KnowledgeAssetsResponse:
    warnings: list[str] = []
    items: list[KnowledgeAssetItem] = []

    docs, w = docs_adapter.scan_markdown_docs()
    warnings.extend(w)
    for doc in docs:
        items.append(KnowledgeAssetItem(**doc))

    glossary, w = docs_adapter.get_table_display_glossary()
    warnings.extend(w)
    for g in glossary:
        items.append(KnowledgeAssetItem(**g))

    columns, w = docs_adapter.get_canonical_columns_glossary()
    warnings.extend(w)
    for c in columns:
        items.append(KnowledgeAssetItem(**c))

    diagram, w = diagrams_adapter.get_latest_diagram()
    warnings.extend(w)
    if diagram:
        items.append(KnowledgeAssetItem(
            asset_id=f"diagram:db:{diagram.get('id', 'latest')}",
            title="Latest Pipeline ER Diagram (DB)",
            asset_type="diagram/data_model",
            path=None,
            summary=f"type={diagram.get('diagram_type')}; stored in pipeline_diagrams",
            source="pipeline_diagrams",
            status="available",
        ))
    else:
        mermaid, w2 = diagrams_adapter.get_static_mermaid_fallback()
        warnings.extend(w2)
        if mermaid:
            items.append(KnowledgeAssetItem(
                asset_id="diagram:static:mermaid_er",
                title="Static Mermaid ER Diagram",
                asset_type="diagram/data_model",
                path=None,
                summary="Generated from diagram_generator.generate_mermaid_er_diagram()",
                source="diagram_generator",
                status="available",
            ))

    status = "available" if items else "degraded"
    return KnowledgeAssetsResponse(status=status, items=items, warnings=warnings)
