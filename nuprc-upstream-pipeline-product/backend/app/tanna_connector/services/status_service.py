"""Implementation status / maturity matrix service (v0.2.1)."""
from datetime import datetime, timezone

from app.tanna_connector.config import (
    CONNECTOR_VERSION,
    ENDPOINT_MATURITY_KEYS,
    IMPLEMENTATION_MATURITY,
    MODULE_ID,
    MODULE_NAME,
)
from app.tanna_connector.envelope import build_envelope


def _overall_status(matrix: list[dict]) -> str:
    statuses = {m["implementation_status"] for m in matrix}
    if "not_implemented" in statuses or "placeholder" in statuses:
        return "partial"
    if statuses == {"implemented"}:
        return "implemented"
    return "partial"


def get_status() -> dict:
    matrix = []
    for object_type in ENDPOINT_MATURITY_KEYS:
        meta = IMPLEMENTATION_MATURITY[object_type]
        matrix.append({
            "object_type": object_type,
            "implementation_status": meta["status"],
            "notes": meta["notes"],
        })

    implemented = [m["object_type"] for m in matrix if m["implementation_status"] == "implemented"]
    partial = [m["object_type"] for m in matrix if m["implementation_status"] == "partial"]
    placeholder = [m["object_type"] for m in matrix if m["implementation_status"] == "placeholder"]
    not_implemented = [
        m["object_type"] for m in matrix if m["implementation_status"] == "not_implemented"
    ]

    last_generated_at = datetime.now(timezone.utc).isoformat()
    status_item = {
        "connector_version": CONNECTOR_VERSION,
        "module_id": MODULE_ID,
        "module_name": MODULE_NAME,
        "overall_status": _overall_status(matrix),
        "endpoint_maturity_matrix": matrix,
        "implemented_objects": implemented,
        "partial_objects": partial,
        "placeholder_objects": placeholder,
        "not_implemented_objects": not_implemented,
        "last_generated_at": last_generated_at,
    }

    return build_envelope(
        object_type="status",
        implementation_status="implemented",
        items=[status_item],
        source="petrocore.tanna_connector.status_service",
        notes="Implementation maturity matrix for Tanna Core sync readiness planning.",
    )
