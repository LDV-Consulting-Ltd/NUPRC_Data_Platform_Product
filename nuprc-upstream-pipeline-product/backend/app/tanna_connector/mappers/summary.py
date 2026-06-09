from datetime import datetime, timezone

from app.tanna_connector.config import CONNECTOR_VERSION, PRODUCT_ID, PRODUCT_NAME
from app.tanna_connector.mappers.data_products import build_data_products
from app.tanna_connector.mappers.decision_products import build_decision_products
from app.tanna_connector.mappers.entities import build_entities
from app.tanna_connector.mappers.health import build_health
from app.tanna_connector.mappers.manifest import build_manifest
from app.tanna_connector.mappers.patterns import build_patterns
from app.tanna_connector.mappers.relationships import build_relationships
from app.tanna_connector.mappers.signals import build_signals
from app.tanna_connector.schemas.summary import ConnectorSummaryResponse


def build_summary() -> ConnectorSummaryResponse:
    warnings: list[str] = []
    manifest = build_manifest()
    health = build_health()
    data_products = build_data_products()
    entities = build_entities()
    relationships = build_relationships()
    signals = build_signals()
    patterns = build_patterns()
    decision_products = build_decision_products()

    gaps = [
        "Pattern detection not implemented",
        "Decision product exports not implemented",
        "Quality API is placeholder (/quality/summary returns empty KPIs)",
        "Lineage graph API not implemented",
        "Signals are generated on read without persistence",
    ]
    if patterns.status == "not_implemented":
        gaps.append("Analytical patterns unavailable (honest not_implemented response)")
    if decision_products.status == "stub":
        gaps.append("Decision products are metadata-only stubs")

    readiness = "ready_read_only"
    if health.status == "down":
        readiness = "degraded_read_only"
    elif health.status == "degraded":
        readiness = "partial_read_only"

    warnings.extend(manifest.warnings)
    warnings.extend(health.warnings)
    warnings.extend(data_products.warnings)

    return ConnectorSummaryResponse(
        product_id=PRODUCT_ID,
        product_name=PRODUCT_NAME,
        connector_version=CONNECTOR_VERSION,
        health_status=health.status,
        health_score=health.score,
        data_product_count=len(data_products.items),
        entity_type_count=len(entities.items),
        relationship_count=len(relationships.items),
        active_signal_count=len(signals.items),
        implementation_gaps=gaps,
        connector_readiness=readiness,
        manifest_summary={
            "domains": manifest.domains,
            "capabilities": manifest.capabilities,
            "canonical_layers": manifest.canonical_layers,
            "canonical_pipeline": manifest.canonical_pipeline,
        },
        warnings=warnings,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
