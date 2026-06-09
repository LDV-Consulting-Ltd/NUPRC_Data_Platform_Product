"""Illumination service — rule-based operational illuminations from signals only (v0.2)."""
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.services.operational_rules import derive_illuminations
from app.tanna_connector.services.signal_generator import generate_signals


def get_illuminations() -> dict:
    raw_signals, warnings = generate_signals()
    items = derive_illuminations(raw_signals)
    for item in items:
        item.pop("signal_type", None)

    return build_envelope(
        object_type="illuminations",
        implementation_status="partial",
        items=items,
        source="operational signals (rule-based derivation)",
        notes=(
            "Rule-based operational illuminations derived from operational signals only. "
            "No LLM narratives or upstream production insights."
        ),
        warnings=warnings,
    )
