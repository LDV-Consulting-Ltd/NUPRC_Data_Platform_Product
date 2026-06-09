from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import (
    API_VERSION,
    CANONICAL_LAYERS,
    CANONICAL_PIPELINE,
    CAPABILITIES,
    CONNECTOR_ID,
    CONNECTOR_VERSION,
    DOMAINS,
    PRODUCT_ID,
    PRODUCT_NAME,
    SOURCE_SYSTEM,
    TANNA_ENDPOINTS,
)
from app.tanna_connector.schemas.manifest import ManifestResponse


def build_manifest() -> ManifestResponse:
    warnings: list[str] = []
    canonical_tables, w1 = catalog_adapter.get_canonical_tables()
    warnings.extend(w1)
    table_display, w2 = catalog_adapter.get_table_display()
    warnings.extend(w2)

    limitations = [
        "Connector is read-only; no ingestion or mutation endpoints.",
        "Pattern detection and decision product exports are not implemented.",
        "Signals and illuminations are operational proxies, not persisted analytics.",
        "PetroCore naming applies only at the /tanna connector boundary.",
        "Legacy and v1 ETL paths coexist; connector prefers canonical gold marts.",
    ]

    backing_assets = {
        "canonical_tables": canonical_tables,
        "table_display_count": len(table_display),
        "catalog_api": "/catalog/*",
        "pipeline_api": "/v1/pipeline/*",
        "gold_marts": canonical_tables.get("gold", []),
    }

    return ManifestResponse(
        product_id=PRODUCT_ID,
        name=PRODUCT_NAME,
        connector_id=CONNECTOR_ID,
        connector_version=CONNECTOR_VERSION,
        source_system=SOURCE_SYSTEM,
        api_version=API_VERSION,
        domains=DOMAINS,
        capabilities=CAPABILITIES,
        canonical_layers=CANONICAL_LAYERS,
        canonical_pipeline=CANONICAL_PIPELINE,
        endpoints=TANNA_ENDPOINTS,
        backing_assets=backing_assets,
        limitations=limitations,
        warnings=warnings,
    )
