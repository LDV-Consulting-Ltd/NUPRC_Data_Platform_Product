"""PetroCore Tanna connector configuration (connector boundary only)."""
from app.tanna_connector.external_ids import data_product_id, entity_id

MODULE_ID = "petrocore"
MODULE_NAME = "PetroCore"
MODULE_CATEGORY = "Upstream Petroleum Intelligence"
MODULE_DESCRIPTION = "Upstream petroleum data and production intelligence product"
PRODUCT_LEGACY_NAME = "NUPRC Upstream Pipeline"
OWNER = "LDV"
CONNECTOR_VERSION = "0.2.1"
API_VERSION = "v0.2.1"
SUPPORTED_TANNA_CORE_VERSION = "0.1.x"
SOURCE_SYSTEM = "nuprc-upstream-pipeline-product"

SUPPORTED_OBJECT_TYPES = [
    "manifest",
    "health",
    "status",
    "data_products",
    "entities",
    "relationships",
    "signals",
    "patterns",
    "illuminations",
    "decision_products",
    "knowledge_assets",
]

ENDPOINT_MATURITY_KEYS = [
    "manifest",
    "health",
    "data_products",
    "entities",
    "relationships",
    "signals",
    "patterns",
    "illuminations",
    "decision_products",
    "knowledge_assets",
]

FRESHNESS_DEGRADED_THRESHOLD = 70

PRIMARY_GOLD_TABLES = {
    "gold_oil_fact_production": {
        "id": data_product_id("gold_oil_fact_production"),
        "domain": "Oil",
        "source_key": "oil_production_status",
    },
    "gold_gas_fact_production": {
        "id": data_product_id("gold_gas_fact_production"),
        "domain": "Gas",
        "source_key": "gas_production_status",
    },
    "gold_rig_fact_activity": {
        "id": data_product_id("gold_rig_fact_activity"),
        "domain": "Rigs",
        "source_key": "rig_disposition",
    },
    "gold_concession_fact_snapshot": {
        "id": data_product_id("gold_concession_fact_snapshot"),
        "domain": "Concessions",
        "source_key": "concession_situation",
    },
}

SOURCE_KEY_TO_DATA_PRODUCT = {
    meta["source_key"]: meta["id"]
    for meta in PRIMARY_GOLD_TABLES.values()
}

SOURCE_KEY_TO_ENTITY = {
    "oil_production_status": entity_id("upstream_source", "oil_production_status"),
    "gas_production_status": entity_id("upstream_source", "gas_production_status"),
    "rig_disposition": entity_id("upstream_source", "rig_disposition"),
    "concession_situation": entity_id("upstream_source", "concession_situation"),
}

OPERATIONAL_SIGNAL_TYPES = frozenset({
    "PIPELINE_STEP_FAILED",
    "PIPELINE_RUN_FAILED",
    "PIPELINE_RUN_BLOCKED",
    "PIPELINE_RUN_RUNNING",
    "DATA_FRESHNESS_DEGRADED",
    "SOURCE_UNAVAILABLE",
    "SCHEMA_DRIFT_DETECTED",
    "CATALOG_FRESHNESS_ISSUE",
})

FORBIDDEN_ANALYTICAL_TERMS = frozenset({
    "production decline",
    "operator performance",
    "field performance",
    "asset utilization",
    "asset risk",
    "performance shift",
    "anomaly detected",
    "trend detected",
})

FORBIDDEN_INVENTED_ENTITIES = frozenset({
    "shell", "chevron", "bonga", "field", "terminal", "license", "operator group",
})

FORBIDDEN_INVENTED_PRODUCTS = frozenset({
    "field performance", "asset performance",
})

IMPLEMENTATION_MATURITY = {
    "manifest": {
        "status": "implemented",
        "notes": "Module identity and connector endpoint registry.",
    },
    "health": {
        "status": "partial",
        "notes": "Aggregates service, pipeline, source, freshness, catalog, and connector health.",
    },
    "status": {
        "status": "implemented",
        "notes": "Implementation maturity matrix for all connector object types.",
    },
    "data_products": {
        "status": "implemented",
        "notes": "Real gold marts backed by catalog registry and TABLE_DISPLAY.",
    },
    "entities": {
        "status": "partial",
        "notes": "Operators, concessions, rigs, upstream sources, ingested documents; limited instances.",
    },
    "relationships": {
        "status": "partial",
        "notes": "Structural FK and lineage relationships from existing metadata only.",
    },
    "signals": {
        "status": "partial",
        "notes": "Operational signals from ETL runs, freshness, sources, schema drift, and catalog.",
    },
    "patterns": {
        "status": "not_implemented",
        "notes": "Analytical pattern detection reserved for future release.",
    },
    "illuminations": {
        "status": "partial",
        "notes": "Rule-based operational illuminations derived from operational signals only.",
    },
    "decision_products": {
        "status": "placeholder",
        "notes": "Draft shells only; no export bundle or approval workflow.",
    },
    "knowledge_assets": {
        "status": "partial",
        "notes": "Read-only index of docs, glossaries, and ER diagram metadata.",
    },
}

TANNA_API_PREFIX = "/api/v1/tanna"
