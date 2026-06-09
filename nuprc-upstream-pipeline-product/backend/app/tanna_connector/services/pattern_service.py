"""Pattern service — not implemented in PetroCore v0.1."""
from app.tanna_connector.envelope import build_envelope

PATTERNS_NOTE = (
    "PetroCore does not currently implement analytical pattern detection. "
    "This endpoint is reserved for future production trend, recurrence, and anomaly pattern outputs."
)


def get_patterns() -> dict:
    return build_envelope(
        object_type="patterns",
        implementation_status="not_implemented",
        items=[],
        source="petrocore.tanna_connector.pattern_service",
        notes=PATTERNS_NOTE,
        sync_ready=False,
    )
