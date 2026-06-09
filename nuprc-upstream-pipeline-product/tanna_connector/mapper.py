"""Map confirmed PetroCore assets to Tanna Connector SDK schemas (read-only)."""
from datetime import datetime
from typing import Any, Optional

from tanna_connector_sdk.models import KnowledgeAssetType, RelationshipType, SignalSeverity
from tanna_connector_sdk.schemas import (
    ConnectorDataProduct,
    ConnectorDecisionProduct,
    ConnectorEntity,
    ConnectorHealthResponse,
    ConnectorIllumination,
    ConnectorKnowledgeAsset,
    ConnectorPattern,
    ConnectorRelationship,
    ConnectorSignal,
)

from tanna_connector.config import (
    FRESHNESS_DEGRADED_THRESHOLD,
    MODULE_ID,
    MODULE_NAME,
    OWNER,
    PRIMARY_DATA_PRODUCTS,
)
from tanna_connector_sdk.health import build_health
from tanna_connector_sdk.manifest import build_manifest

from app.tanna_connector.adapters import catalog_adapter, diagrams_adapter, docs_adapter, health_adapter, pipeline_adapter
from app.tanna_connector.services.signal_generator import generate_signals


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except Exception:
        return None


def map_health() -> ConnectorHealthResponse:
    raw, _ = health_adapter.collect_health_raw()
    db_ok = raw.get("database", {}).get("connected", False)
    latest = raw.get("latest_run")
    freshness = raw.get("gold_freshness") or []

    status = "healthy"
    if not db_ok:
        status = "degraded"
    if latest and (latest.get("status") or "").lower() == "failed":
        status = "degraded"
    if any(
        f.get("freshness_score", 100) < FRESHNESS_DEGRADED_THRESHOLD
        or f.get("status") in ("degraded", "down")
        for f in freshness
    ):
        status = "degraded" if status == "healthy" else status

    latest_refresh = None
    if latest:
        latest_refresh = _parse_dt(latest.get("ended_at") or latest.get("started_at"))

    message = "PetroCore Tanna connector operational"
    if not db_ok:
        message = "Connector operational; database connectivity degraded"
    elif status == "degraded":
        message = "Connector operational with degraded upstream data or pipeline health"

    return build_health(
        MODULE_ID,
        status=status,
        health_status=status,
        message=message,
        latest_refresh_at=latest_refresh,
    )


def map_manifest():
    canonical, _ = catalog_adapter.get_canonical_tables()
    return build_manifest(
        module_id=MODULE_ID,
        module_name=MODULE_NAME,
        module_description=(
            "Upstream petroleum intelligence for NUPRC regulatory production, rig, "
            "and concession datasets. Exposes curated gold marts and operational metadata only."
        ),
        module_category="Upstream Petroleum Intelligence",
        owner=OWNER,
        module_version="1.0.0",
        latest_refresh_at=_parse_dt((pipeline_adapter.get_latest_run()[0] or {}).get("ended_at")),
        data_quality_status="monitored" if canonical.get("gold") else "unknown",
    )


def map_data_products() -> list[ConnectorDataProduct]:
    gold_tables, _ = catalog_adapter.get_gold_tables()
    table_display, _ = catalog_adapter.get_table_display()
    by_name = {t["physical_name"]: t for t in gold_tables}
    products: list[ConnectorDataProduct] = []
    seen: set[str] = set()

    for table_name, meta in PRIMARY_DATA_PRODUCTS.items():
        info = by_name.get(table_name, {})
        display = table_display.get(table_name, {})
        row_count = info.get("row_count") or 0
        quality = "monitored" if row_count > 0 else "unknown"
        products.append(
            ConnectorDataProduct(
                id=meta["id"],
                external_id=meta["id"],
                module_id=MODULE_ID,
                name=display.get("display_name") or meta["name"],
                description=info.get("description") or display.get("display_name"),
                domain=meta["domain"],
                classification="analytical_data_product",
                business_owner="LDV",
                technical_owner="PetroCore Data Engineering",
                steward="Upstream Regulatory Intelligence",
                source_systems=["NUPRC Upstream Reports"],
                quality_status=quality,
                refresh_frequency="daily",
                lifecycle_stage="active",
                latest_refresh_at=_parse_dt(info.get("last_updated")),
                tags=[meta["domain"].lower(), "gold", table_name],
            )
        )
        seen.add(table_name)

    for table_name, info in by_name.items():
        if table_name in seen:
            continue
        display = table_display.get(table_name, {})
        if not table_name.startswith("gold_"):
            continue
        dp_id = f"pc-dp-{table_name.replace('gold_', '').replace('_', '-')}"
        products.append(
            ConnectorDataProduct(
                id=dp_id,
                external_id=dp_id,
                module_id=MODULE_ID,
                name=display.get("display_name") or table_name,
                description=info.get("description"),
                domain=display.get("subject_area"),
                classification="analytical_data_product",
                source_systems=["NUPRC Upstream Reports"],
                quality_status="monitored" if (info.get("row_count") or 0) > 0 else "unknown",
                lifecycle_stage="active",
                latest_refresh_at=_parse_dt(info.get("last_updated")),
                tags=["gold", table_name],
            )
        )

    return products


def _entity_id(entity_type: str, key: str) -> str:
    safe = "".join(c if c.isalnum() else "-" for c in str(key).lower())[:80]
    return f"pc-ent-{entity_type}-{safe}"


def map_entities() -> list[ConnectorEntity]:
    entities: list[ConnectorEntity] = []
    seen_keys: set[str] = set()

    operator_tables = [
        ("gold", "gold_oil_dim_operator", "operator_name"),
        ("gold", "gold_gas_dim_operator", "operator_name"),
        ("gold", "gold_rig_dim_operator", "operator_name"),
    ]
    for schema, table, name_col in operator_tables:
        rows, _, _ = catalog_adapter.fetch_entity_rows(schema, table, 200, 0)
        for row in rows:
            name = row.get(name_col) or row.get("operator_name")
            if not name or name in seen_keys:
                continue
            seen_keys.add(name)
            eid = _entity_id("operator", name)
            entities.append(
                ConnectorEntity(
                    id=eid,
                    external_id=eid,
                    module_id=MODULE_ID,
                    entity_type="operator",
                    entity_name=str(name),
                    description="Upstream operator from PetroCore gold dimension",
                    domain="Oil & Gas",
                    attributes={k: v for k, v in row.items() if k != name_col},
                    source_data_product_id="pc-dp-oil-production",
                    tags=["operator"],
                )
            )

    rows, _, _ = catalog_adapter.fetch_entity_rows("gold", "gold_concession_dim_concession", 200, 0)
    for row in rows:
        name = row.get("concession_category_full") or row.get("concession_no") or row.get("company_operator_name")
        if not name:
            continue
        eid = _entity_id("concession", name)
        entities.append(
            ConnectorEntity(
                id=eid,
                external_id=eid,
                module_id=MODULE_ID,
                entity_type="concession",
                entity_name=str(name),
                description="Concession register entry",
                domain="Concessions",
                attributes={k: v for k, v in row.items()},
                source_data_product_id="pc-dp-concession-snapshot",
                tags=["concession"],
            )
        )

    rows, _, _ = catalog_adapter.fetch_entity_rows("gold", "gold_rig_dim_rig", 200, 0)
    for row in rows:
        name = row.get("rig_name")
        if not name:
            continue
        eid = _entity_id("rig", name)
        entities.append(
            ConnectorEntity(
                id=eid,
                external_id=eid,
                module_id=MODULE_ID,
                entity_type="rig",
                entity_name=str(name),
                description="Rig dimension from rig disposition mart",
                domain="Rigs",
                attributes={k: v for k, v in row.items()},
                source_data_product_id="pc-dp-rig-activity",
                tags=["rig"],
            )
        )

    try:
        from app.services.sources import get_all_sources
        for source in get_all_sources():
            eid = _entity_id("upstream_source", source.source_id)
            entities.append(
                ConnectorEntity(
                    id=eid,
                    external_id=eid,
                    module_id=MODULE_ID,
                    entity_type="upstream_source",
                    entity_name=source.name,
                    description=source.description,
                    domain="Regulatory Sources",
                    attributes={
                        "source_id": source.source_id,
                        "base_url": source.base_url,
                        "bronze_table": source.bronze_table,
                    },
                    tags=["source", source.source_id],
                )
            )
    except Exception:
        pass

    docs, _ = catalog_adapter.get_ingested_documents(50, 0)
    for row in docs:
        sha = row.get("file_sha256") or row.get("filename")
        if not sha:
            continue
        eid = _entity_id("ingested_document", str(sha)[:16])
        entities.append(
            ConnectorEntity(
                id=eid,
                external_id=eid,
                module_id=MODULE_ID,
                entity_type="ingested_document",
                entity_name=str(row.get("filename") or sha),
                description="Downloaded NUPRC source file tracked in data catalog",
                domain="Catalog",
                attributes={k: v for k, v in row.items()},
                tags=["catalog", str(row.get("source_id", ""))],
            )
        )

    count, _ = catalog_adapter.safe_count("warehouse", "dim_asset")
    if count is not None and count > 0:
        asset_rows, _, _ = catalog_adapter.fetch_entity_rows("warehouse", "dim_asset", 100, 0)
        for row in asset_rows:
            name = row.get("asset_name")
            if not name:
                continue
            eid = _entity_id("asset", name)
            entities.append(
                ConnectorEntity(
                    id=eid,
                    external_id=eid,
                    module_id=MODULE_ID,
                    entity_type="asset",
                    entity_name=str(name),
                    description="Asset from legacy warehouse dimension (where populated)",
                    domain="Assets",
                    attributes={k: v for k, v in row.items()},
                    tags=["asset", "warehouse"],
                    status="active",
                )
            )

    return entities


def map_relationships() -> list[ConnectorRelationship]:
    return [
        ConnectorRelationship(
            id="pc-rel-oil-operator",
            external_id="pc-rel-oil-operator",
            module_id=MODULE_ID,
            source_object_id="pc-dp-oil-production",
            source_object_type="data_product",
            relationship_type=RelationshipType.MEASURES.value,
            target_object_id="pc-ent-operator",
            target_object_type="operator",
            description="Oil production fact is measured by operator (gold_oil_fact_production FK)",
            confidence=0.95,
        ),
        ConnectorRelationship(
            id="pc-rel-gas-operator",
            external_id="pc-rel-gas-operator",
            module_id=MODULE_ID,
            source_object_id="pc-dp-gas-production",
            source_object_type="data_product",
            relationship_type=RelationshipType.MEASURES.value,
            target_object_id="pc-ent-operator",
            target_object_type="operator",
            description="Gas production fact is measured by operator",
            confidence=0.95,
        ),
        ConnectorRelationship(
            id="pc-rel-rig-operator",
            external_id="pc-rel-rig-operator",
            module_id=MODULE_ID,
            source_object_id="pc-dp-rig-activity",
            source_object_type="data_product",
            relationship_type=RelationshipType.MEASURES.value,
            target_object_id="pc-ent-operator",
            target_object_type="operator",
            description="Rig activity fact is measured by operator",
            confidence=0.95,
        ),
        ConnectorRelationship(
            id="pc-rel-concession-snapshot",
            external_id="pc-rel-concession-snapshot",
            module_id=MODULE_ID,
            source_object_id="pc-dp-concession-snapshot",
            source_object_type="data_product",
            relationship_type=RelationshipType.MEASURES.value,
            target_object_id="pc-ent-concession",
            target_object_type="concession",
            description="Concession snapshot describes concession register",
            confidence=0.95,
        ),
        ConnectorRelationship(
            id="pc-rel-doc-bronze",
            external_id="pc-rel-doc-bronze",
            module_id=MODULE_ID,
            source_object_id="pc-ent-ingested_document",
            source_object_type="ingested_document",
            relationship_type=RelationshipType.CONSUMES.value,
            target_object_id="pc-dp-oil-production",
            target_object_type="data_product",
            description="Ingested documents flow through bronze to gold marts via ETL",
            confidence=0.85,
        ),
    ]


def map_signals() -> list[ConnectorSignal]:
    raw_signals, _ = generate_signals()
    severity_map = {"info": SignalSeverity.LOW.value, "warning": SignalSeverity.HIGH.value, "critical": SignalSeverity.CRITICAL.value}
    mapped: list[ConnectorSignal] = []
    for sig in raw_signals:
        sid = f"pc-sig-{sig.signal_id.replace('sig-', '')}"
        mapped.append(
            ConnectorSignal(
                id=sid,
                external_id=sid,
                module_id=MODULE_ID,
                name=sig.title,
                description=sig.description,
                signal_type=sig.signal_type,
                severity=severity_map.get(sig.severity, SignalSeverity.MEDIUM.value),
                confidence=sig.confidence,
                detected_at=_parse_dt(sig.detected_at),
                related_data_products=[
                    meta["id"]
                    for meta in PRIMARY_DATA_PRODUCTS.values()
                    if meta["domain"].lower() in sig.description.lower()
                ][:1],
                status="active",
            )
        )
    return mapped


def map_patterns() -> list[ConnectorPattern]:
    """Analytical patterns are not implemented in PetroCore — return empty list."""
    return []


def map_illuminations() -> list[ConnectorIllumination]:
    items: list[ConnectorIllumination] = []
    latest, _ = pipeline_adapter.get_latest_run()
    freshness, _ = pipeline_adapter.get_gold_freshness()
    drift_count, _ = catalog_adapter.get_schema_drift_count()

    if latest and (latest.get("status") or "").lower() == "success":
        items.append(
            ConnectorIllumination(
                id="pc-ill-pipeline-success",
                external_id="pc-ill-pipeline-success",
                module_id=MODULE_ID,
                title="Latest pipeline run completed successfully",
                summary="The canonical v1 ETL run finished without failure.",
                interpretation="Bronze, silver, and gold layers were refreshed for the latest run.",
                business_implication="Downstream Tanna consumers can rely on recently refreshed gold marts.",
                recommended_attention="Monitor gold table row counts and freshness scores.",
                confidence=0.9,
                related_signals=[],
            )
        )
    elif latest and (latest.get("status") or "").lower() == "failed":
        items.append(
            ConnectorIllumination(
                id="pc-ill-pipeline-failed",
                external_id="pc-ill-pipeline-failed",
                module_id=MODULE_ID,
                title="Latest pipeline run failed",
                summary="The most recent ETL run did not complete successfully.",
                interpretation="Gold marts may be stale until the pipeline is re-run.",
                business_implication="Tanna synchronization should treat production data as potentially stale.",
                recommended_attention="Inspect admin.etl_run_steps for the failing step.",
                confidence=0.95,
            )
        )

    for src in freshness:
        if src.get("freshness_score", 100) < FRESHNESS_DEGRADED_THRESHOLD:
            sk = src.get("source_key", "source")
            items.append(
                ConnectorIllumination(
                    id=f"pc-ill-freshness-{sk}",
                    external_id=f"pc-ill-freshness-{sk}",
                    module_id=MODULE_ID,
                    title=f"{src.get('label', 'Source')} freshness is degraded",
                    summary=f"Freshness score {src.get('freshness_score')} (status={src.get('status')}).",
                    interpretation="Gold mart data for this domain may not reflect the latest reporting period.",
                    business_implication="Regulatory intelligence based on this source may be incomplete.",
                    recommended_attention="Verify source availability and re-run the pipeline.",
                    confidence=0.85,
                )
            )

    if drift_count is not None and drift_count > 0:
        items.append(
            ConnectorIllumination(
                id="pc-ill-schema-drift",
                external_id="pc-ill-schema-drift",
                module_id=MODULE_ID,
                title="Schema drift detected in recent loads",
                summary=f"{drift_count} event(s) recorded in silver.schema_drift.",
                interpretation="Source file column structures may have changed from canonical mappings.",
                business_implication="Data quality and conformance may be affected until drift is resolved.",
                recommended_attention="Review schema drift records and fuzzy matcher mappings.",
                confidence=0.85,
            )
        )

    return items


def map_decision_products() -> list[ConnectorDecisionProduct]:
    """Metadata-only placeholders — export bundles not implemented."""
    return [
        ConnectorDecisionProduct(
            id="pc-dcp-monthly-oil-gas-submission",
            external_id="pc-dcp-monthly-oil-gas-submission",
            module_id=MODULE_ID,
            name="Monthly Oil & Gas Regulatory Submission",
            description="[PLACEHOLDER] Metadata-only stub. Export bundle not implemented.",
            decision_type="regulatory",
            business_capability="Regulatory Reporting",
            supported_objective="Timely regulatory submission",
            related_intelligence_products=["pc-dp-oil-production", "pc-dp-gas-production"],
            owner=OWNER,
            status="draft",
        ),
        ConnectorDecisionProduct(
            id="pc-dcp-concession-compliance",
            external_id="pc-dcp-concession-compliance",
            module_id=MODULE_ID,
            name="Concession Compliance Snapshot",
            description="[PLACEHOLDER] Metadata-only stub. Snapshot export not implemented.",
            decision_type="compliance",
            business_capability="Concession Oversight",
            related_intelligence_products=["pc-dp-concession-snapshot"],
            owner=OWNER,
            status="draft",
        ),
        ConnectorDecisionProduct(
            id="pc-dcp-rig-oversight",
            external_id="pc-dcp-rig-oversight",
            module_id=MODULE_ID,
            name="Rig Activity Oversight Brief",
            description="[PLACEHOLDER] Metadata-only stub. Brief generation not implemented.",
            decision_type="operational",
            business_capability="Rig Oversight",
            related_intelligence_products=["pc-dp-rig-activity"],
            owner=OWNER,
            status="draft",
        ),
    ]


def map_knowledge_assets() -> list[ConnectorKnowledgeAsset]:
    assets: list[ConnectorKnowledgeAsset] = []

    docs, _ = docs_adapter.scan_markdown_docs()
    type_map = {
        "ETL_README": KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value,
        "PIPELINE_ETL_STEPS": KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value,
        "UNIFIED_CATALOG_AND_PIPELINE": KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value,
        "TROUBLESHOOTING": KnowledgeAssetType.SOP.value,
        "README": KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value,
        "ABOUT": KnowledgeAssetType.PRODUCT_REQUIREMENT.value,
    }
    for doc in docs:
        title_key = doc.get("title", "").upper().replace(" ", "_")
        asset_type = KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value
        for key, atype in type_map.items():
            if key in title_key or key in doc.get("asset_id", "").upper():
                asset_type = atype
                break
        assets.append(
            ConnectorKnowledgeAsset(
                id=doc["asset_id"],
                external_id=doc["asset_id"],
                module_id=MODULE_ID,
                title=doc["title"],
                asset_type=asset_type,
                description=doc.get("summary"),
                owner=OWNER,
                content_url=doc.get("path"),
            )
        )

    glossary, _ = docs_adapter.get_table_display_glossary()
    for g in glossary:
        assets.append(
            ConnectorKnowledgeAsset(
                id=g["asset_id"],
                external_id=g["asset_id"],
                module_id=MODULE_ID,
                title=g["title"],
                asset_type=KnowledgeAssetType.BUSINESS_GLOSSARY.value,
                description=g.get("summary"),
                owner=OWNER,
            )
        )

    columns, _ = docs_adapter.get_canonical_columns_glossary()
    for c in columns:
        assets.append(
            ConnectorKnowledgeAsset(
                id=c["asset_id"],
                external_id=c["asset_id"],
                module_id=MODULE_ID,
                title=c["title"],
                asset_type=KnowledgeAssetType.DATA_DICTIONARY.value,
                description=c.get("summary"),
                owner=OWNER,
            )
        )

    diagram, _ = diagrams_adapter.get_latest_diagram()
    if diagram:
        assets.append(
            ConnectorKnowledgeAsset(
                id="pc-ka-er-diagram",
                external_id="pc-ka-er-diagram",
                module_id=MODULE_ID,
                title="PetroCore Data Model ER Diagram",
                asset_type=KnowledgeAssetType.ARCHITECTURE_DOCUMENT.value,
                description="Latest Mermaid ER diagram from pipeline_diagrams",
                owner=OWNER,
            )
        )

    return assets
