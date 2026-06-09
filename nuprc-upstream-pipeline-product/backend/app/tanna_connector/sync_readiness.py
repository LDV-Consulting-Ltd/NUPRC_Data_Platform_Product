"""Sync readiness metadata per connector object type (v0.2.1)."""
from typing import TypedDict


class SyncReadinessMeta(TypedDict):
    sync_ready: bool
    sync_notes: str
    external_id_strategy: str
    duplicate_handling_notes: str


SYNC_READINESS: dict[str, SyncReadinessMeta] = {
    "manifest": {
        "sync_ready": True,
        "sync_notes": "Module identity is stable; safe for Tanna Core module registration.",
        "external_id_strategy": "petrocore:manifest:module",
        "duplicate_handling_notes": "Single manifest per module_id; upsert by module_id.",
    },
    "health": {
        "sync_ready": True,
        "sync_notes": "Health snapshot is read-only aggregate; sync as point-in-time observability.",
        "external_id_strategy": "petrocore:health:component:{component_name}",
        "duplicate_handling_notes": "Replace prior health snapshot per sync cycle; not append-only.",
    },
    "status": {
        "sync_ready": True,
        "sync_notes": "Maturity matrix is stable contract metadata for Tanna Core planning.",
        "external_id_strategy": "petrocore:status:maturity_matrix",
        "duplicate_handling_notes": "Upsert single status document per connector_version.",
    },
    "data_products": {
        "sync_ready": True,
        "sync_notes": "Gold mart products have stable table-backed external_ids.",
        "external_id_strategy": "petrocore:data_product:{gold_table_name}",
        "duplicate_handling_notes": "Upsert by external_id; one record per gold mart table.",
    },
    "entities": {
        "sync_ready": True,
        "sync_notes": "Partial coverage with stable name/table-backed external_ids; instance sampling limited.",
        "external_id_strategy": "petrocore:entity:{entity_type}:{stable_name_or_key}",
        "duplicate_handling_notes": "Upsert by external_id; sampled instances may change between syncs.",
    },
    "relationships": {
        "sync_ready": True,
        "sync_notes": "Structural relationships only; stable source/type/target external_ids.",
        "external_id_strategy": "petrocore:relationship:{source}:{relationship_type}:{target}",
        "duplicate_handling_notes": "Upsert by external_id; dedupe on structural tuple.",
    },
    "signals": {
        "sync_ready": True,
        "sync_notes": "Operational signals use deterministic external_ids from evidence keys.",
        "external_id_strategy": "petrocore:signal:{signal_type}:{stable_evidence_key}",
        "duplicate_handling_notes": "Upsert by external_id; same evidence updates detected_at.",
    },
    "patterns": {
        "sync_ready": False,
        "sync_notes": "Not implemented; endpoint returns empty items.",
        "external_id_strategy": "n/a",
        "duplicate_handling_notes": "Do not sync until analytical patterns are implemented.",
    },
    "illuminations": {
        "sync_ready": True,
        "sync_notes": "Rule-based operational illuminations derived from signals; partial but schema-valid.",
        "external_id_strategy": "petrocore:illumination:{related_signal_key}",
        "duplicate_handling_notes": "Upsert by external_id; tied to originating signal evidence.",
    },
    "decision_products": {
        "sync_ready": False,
        "sync_notes": "Placeholder shells only; no export bundle or workflow.",
        "external_id_strategy": "petrocore:decision_product:{slug}",
        "duplicate_handling_notes": "Do not sync as production decision products until v0.4+.",
    },
    "knowledge_assets": {
        "sync_ready": True,
        "sync_notes": "Read-only doc/glossary index with stable path-backed external_ids.",
        "external_id_strategy": "petrocore:knowledge_asset:{category}:{name}",
        "duplicate_handling_notes": "Upsert by external_id; content_text is excerpt only.",
    },
}


def get_sync_readiness(object_type: str) -> SyncReadinessMeta:
    return SYNC_READINESS.get(
        object_type,
        {
            "sync_ready": False,
            "sync_notes": "Unknown object type; not sync-ready.",
            "external_id_strategy": "n/a",
            "duplicate_handling_notes": "Do not sync.",
        },
    )
