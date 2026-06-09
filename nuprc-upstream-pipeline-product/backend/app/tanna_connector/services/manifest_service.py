"""Manifest service — connector module identity."""
from app.tanna_connector.adapters import catalog_adapter
from app.tanna_connector.config import (
    API_VERSION,
    CONNECTOR_VERSION,
    MODULE_CATEGORY,
    MODULE_DESCRIPTION,
    MODULE_ID,
    MODULE_NAME,
    OWNER,
    PRODUCT_LEGACY_NAME,
    SOURCE_SYSTEM,
    SUPPORTED_OBJECT_TYPES,
    SUPPORTED_TANNA_CORE_VERSION,
    TANNA_API_PREFIX,
)
from app.tanna_connector.envelope import build_envelope


def get_manifest() -> dict:
    canonical, warnings = catalog_adapter.get_canonical_tables()
    manifest_item = {
        "module_id": MODULE_ID,
        "module_name": MODULE_NAME,
        "module_description": MODULE_DESCRIPTION,
        "module_category": MODULE_CATEGORY,
        "owner": OWNER,
        "product_legacy_name": PRODUCT_LEGACY_NAME,
        "api_version": API_VERSION,
        "connector_version": CONNECTOR_VERSION,
        "supported_tanna_core_version": SUPPORTED_TANNA_CORE_VERSION,
        "source_system": SOURCE_SYSTEM,
        "supported_object_types": SUPPORTED_OBJECT_TYPES,
        "connector_endpoints": [
            f"{TANNA_API_PREFIX}/health",
            f"{TANNA_API_PREFIX}/status",
            f"{TANNA_API_PREFIX}/manifest",
            f"{TANNA_API_PREFIX}/data-products",
            f"{TANNA_API_PREFIX}/entities",
            f"{TANNA_API_PREFIX}/relationships",
            f"{TANNA_API_PREFIX}/signals",
            f"{TANNA_API_PREFIX}/patterns",
            f"{TANNA_API_PREFIX}/illuminations",
            f"{TANNA_API_PREFIX}/decision-products",
            f"{TANNA_API_PREFIX}/knowledge-assets",
        ],
        "canonical_layers": list(canonical.keys()) if canonical else ["bronze", "silver", "gold"],
        "status": "active",
    }
    return build_envelope(
        object_type="manifest",
        implementation_status="implemented",
        items=[manifest_item],
        source="petrocore.tanna_connector.manifest_service",
        notes="PetroCore naming applies at connector boundary only.",
        warnings=warnings,
    )
