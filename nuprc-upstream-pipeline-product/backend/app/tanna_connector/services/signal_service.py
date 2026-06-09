"""Signal service — operational signals only (v0.2.1)."""
from app.tanna_connector.config import FORBIDDEN_ANALYTICAL_TERMS, MODULE_ID, OPERATIONAL_SIGNAL_TYPES
from app.tanna_connector.envelope import build_envelope
from app.tanna_connector.external_ids import signal_id as make_signal_external_id
from app.tanna_connector.schemas.signal import SignalItem
from app.tanna_connector.services.signal_generator import generate_signals, stable_key_for_signal


def _is_analytical(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in FORBIDDEN_ANALYTICAL_TERMS)


def get_signals() -> dict:
    raw_signals, warnings = generate_signals()
    items: list[dict] = []
    for sig in raw_signals:
        if sig.signal_type not in OPERATIONAL_SIGNAL_TYPES:
            warnings.append(f"Skipped non-operational signal type: {sig.signal_type}")
            continue
        combined = f"{sig.title} {sig.description}"
        if _is_analytical(combined):
            warnings.append(f"Skipped analytical signal: {sig.title}")
            continue
        eid = make_signal_external_id(sig.signal_type, stable_key_for_signal(sig))
        items.append({
            "id": eid,
            "external_id": eid,
            "module_id": MODULE_ID,
            "name": sig.title,
            "description": sig.description,
            "signal_type": sig.signal_type,
            "severity": sig.severity,
            "confidence": sig.confidence,
            "detected_at": sig.detected_at,
            "related_entities": sig.related_entities,
            "related_data_products": sig.related_data_products,
            "status": "active",
            "source": sig.source,
            "backing_data": sig.backing_data,
        })

    return build_envelope(
        object_type="signals",
        implementation_status="partial",
        items=items,
        source="admin.etl_runs, admin.etl_run_steps, freshness, sources_health, schema_drift, data_catalog",
        notes=(
            "Operational signals only from failed runs, freshness, sources, schema drift, "
            "and catalog issues. No analytical production-decline signals."
        ),
        warnings=warnings,
    )
