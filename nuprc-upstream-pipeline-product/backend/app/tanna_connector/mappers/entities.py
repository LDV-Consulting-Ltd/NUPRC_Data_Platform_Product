from typing import Any, Optional

from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import ENTITY_TYPE_SLUGS
from app.tanna_connector.schemas.entity import EntitiesResponse, EntitySampleResponse, EntityTypeItem

ENTITY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "operator": {
        "entity_type": "Operator",
        "description": "Upstream operator dimension from gold marts.",
        "backing_tables": [
            "gold.gold_oil_dim_operator",
            "gold.gold_gas_dim_operator",
            "gold.gold_rig_dim_operator",
        ],
        "sample_table": ("gold", "gold_oil_dim_operator"),
    },
    "calendar_date": {
        "entity_type": "CalendarDate",
        "description": "Conformed calendar date dimension.",
        "backing_tables": ["gold.gold_dim_date"],
        "sample_table": ("gold", "gold_dim_date"),
    },
    "concession": {
        "entity_type": "Concession",
        "description": "Concession register dimension.",
        "backing_tables": ["gold.gold_concession_dim_concession"],
        "sample_table": ("gold", "gold_concession_dim_concession"),
    },
    "rig": {
        "entity_type": "Rig",
        "description": "Rig dimension from rig disposition mart.",
        "backing_tables": ["gold.gold_rig_dim_rig"],
        "sample_table": ("gold", "gold_rig_dim_rig"),
    },
    "upstream_source": {
        "entity_type": "UpstreamSource",
        "description": "Configured NUPRC upstream regulatory sources.",
        "backing_tables": [],
        "sample_table": None,
    },
    "ingested_document": {
        "entity_type": "IngestedDocument",
        "description": "Downloaded source files tracked in data catalog.",
        "backing_tables": ["data_catalog.downloaded_files"],
        "sample_table": None,
    },
}


def _resolve_count(slug: str, defn: dict[str, Any]) -> tuple[Optional[int], list[str]]:
    warnings: list[str] = []
    if slug == "upstream_source":
        try:
            from app.services.sources import get_all_sources
            return len(get_all_sources()), warnings
        except Exception as exc:
            warnings.append(f"Upstream sources unavailable: {exc}")
            return None, warnings
    if slug == "ingested_document":
        _, total, w = catalog_adapter.get_ingested_documents(1, 0)
        return total, w
    tables = defn.get("backing_tables") or []
    counts = []
    for full in tables:
        schema, table = full.split(".", 1)
        count, w = catalog_adapter.safe_count(schema, table)
        warnings.extend(w)
        if count is not None:
            counts.append(count)
    if not counts:
        return None, warnings
    return max(counts), warnings


def build_entities() -> EntitiesResponse:
    warnings: list[str] = []
    items: list[EntityTypeItem] = []

    for slug, defn in ENTITY_DEFINITIONS.items():
        count, w = _resolve_count(slug, defn)
        warnings.extend(w)
        if slug == "upstream_source":
            status = "available" if count is not None else "unavailable"
        elif count is None:
            status = "unavailable"
        elif count == 0:
            status = "degraded"
        else:
            status = "available"
        items.append(EntityTypeItem(
            entity_type=defn["entity_type"],
            slug=slug,
            status=status,
            count=count,
            backing_tables=defn.get("backing_tables", []),
            description=defn.get("description"),
        ))

    return EntitiesResponse(status="available", items=items, warnings=warnings)


def build_entity_samples(entity_type: str, limit: int, offset: int) -> EntitySampleResponse:
    warnings: list[str] = []
    slug = entity_type.lower().replace("-", "_")
    if slug not in ENTITY_DEFINITIONS:
        return EntitySampleResponse(
            entity_type=entity_type,
            slug=slug,
            status="unavailable",
            limit=limit,
            offset=offset,
            warnings=[f"Unknown entity type: {entity_type}. Valid: {', '.join(ENTITY_TYPE_SLUGS.keys())}"],
        )

    defn = ENTITY_DEFINITIONS[slug]

    if slug == "upstream_source":
        try:
            from app.services.sources import get_all_sources
            sources = get_all_sources()
            sliced = sources[offset: offset + limit]
            items = [
                {
                    "source_id": s.source_id,
                    "name": s.name,
                    "base_url": s.base_url,
                    "bronze_table": s.bronze_table,
                    "description": s.description,
                }
                for s in sliced
            ]
            return EntitySampleResponse(
                entity_type=defn["entity_type"],
                slug=slug,
                status="available",
                limit=limit,
                offset=offset,
                total=len(sources),
                items=items,
            )
        except Exception as exc:
            warnings.append(str(exc))
            return EntitySampleResponse(
                entity_type=defn["entity_type"],
                slug=slug,
                status="unavailable",
                limit=limit,
                offset=offset,
                warnings=warnings,
            )

    if slug == "ingested_document":
        items, total, w = catalog_adapter.get_ingested_documents(limit, offset)
        warnings.extend(w)
        status = "available" if items or total == 0 else "unavailable"
        return EntitySampleResponse(
            entity_type=defn["entity_type"],
            slug=slug,
            status=status,
            limit=limit,
            offset=offset,
            total=total,
            items=items,
            warnings=warnings,
        )

    sample = defn.get("sample_table")
    if not sample:
        return EntitySampleResponse(
            entity_type=defn["entity_type"],
            slug=slug,
            status="unavailable",
            limit=limit,
            offset=offset,
            warnings=["No sample table configured for this entity type"],
        )

    schema, table = sample
    items, total, w = catalog_adapter.fetch_entity_rows(schema, table, limit, offset)
    warnings.extend(w)
    status = "available" if items or total == 0 else "unavailable"
    if total == 0:
        status = "degraded"
    return EntitySampleResponse(
        entity_type=defn["entity_type"],
        slug=slug,
        status=status,
        limit=limit,
        offset=offset,
        total=total,
        items=items,
        warnings=warnings,
    )
