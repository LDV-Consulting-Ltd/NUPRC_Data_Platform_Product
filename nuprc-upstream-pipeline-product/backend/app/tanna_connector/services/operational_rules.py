"""Rule-based operational illumination templates derived from signals."""
from app.tanna_connector.config import MODULE_ID
from app.tanna_connector.external_ids import illumination_id, signal_id as make_signal_external_id
from app.tanna_connector.schemas.signal import SignalItem
from app.tanna_connector.services.signal_generator import stable_key_for_signal


def _external_signal_id(signal: SignalItem) -> str:
    return make_signal_external_id(signal.signal_type, stable_key_for_signal(signal))


def illumination_from_signal(signal: SignalItem) -> dict | None:
    """Map one operational signal to a rule-based illumination, or None if unsupported."""
    sid = _external_signal_id(signal)
    templates: dict[str, dict] = {
        "PIPELINE_RUN_FAILED": {
            "title": "Pipeline execution health requires review",
            "summary": signal.description,
            "interpretation": "The latest canonical ETL run did not complete successfully.",
            "business_implication": "Gold marts may be stale until the pipeline is re-run.",
            "recommended_attention": "Inspect admin.etl_run_steps for the failing step and re-run ETL.",
            "confidence": signal.confidence,
        },
        "PIPELINE_STEP_FAILED": {
            "title": "Pipeline execution health requires review",
            "summary": signal.description,
            "interpretation": "A specific ETL step failed during the latest pipeline run.",
            "business_implication": "Downstream data products may be incomplete or stale.",
            "recommended_attention": "Review the failing step error_json and remediate before re-run.",
            "confidence": signal.confidence,
        },
        "PIPELINE_RUN_BLOCKED": {
            "title": "Pipeline execution health requires review",
            "summary": signal.description,
            "interpretation": "A running pipeline may block new ETL executions.",
            "business_implication": "Scheduled refreshes may be delayed.",
            "recommended_attention": "Verify run state in admin.etl_runs and clear stuck runs if needed.",
            "confidence": signal.confidence,
        },
        "PIPELINE_RUN_RUNNING": {
            "title": "Pipeline execution in progress",
            "summary": signal.description,
            "interpretation": "An ETL run is currently executing.",
            "business_implication": "Freshness and availability may change when the run completes.",
            "recommended_attention": "Monitor run progress; review if run duration is unusually long.",
            "confidence": signal.confidence,
        },
        "DATA_FRESHNESS_DEGRADED": {
            "title": "Source freshness degradation may affect reporting confidence",
            "summary": signal.description,
            "interpretation": "A gold mart freshness score is below the operational threshold.",
            "business_implication": "Regulatory and operational views may not reflect the latest period.",
            "recommended_attention": "Verify source availability and re-run the pipeline.",
            "confidence": signal.confidence,
        },
        "SOURCE_UNAVAILABLE": {
            "title": "Upstream source availability requires attention",
            "summary": signal.description,
            "interpretation": "Bronze source health indicates degraded or down status.",
            "business_implication": "Ingestion and gold mart refresh may be impacted.",
            "recommended_attention": "Check source ingestion status and bronze table row counts.",
            "confidence": signal.confidence,
        },
        "SCHEMA_DRIFT_DETECTED": {
            "title": "Schema drift may require mapping review",
            "summary": signal.description,
            "interpretation": "Source column structures may have changed since last conformance.",
            "business_implication": "Silver/gold mapping quality may be affected.",
            "recommended_attention": "Review silver.schema_drift records and column mappings.",
            "confidence": signal.confidence,
        },
        "CATALOG_FRESHNESS_ISSUE": {
            "title": "Catalog refresh may be incomplete",
            "summary": signal.description,
            "interpretation": "The data catalog shows operational freshness gaps.",
            "business_implication": "Catalog-driven lineage and file tracking may be incomplete.",
            "recommended_attention": "Review data_catalog.downloaded_files and available_tables.",
            "confidence": signal.confidence,
        },
    }
    template = templates.get(signal.signal_type)
    if not template:
        return None
    iid = illumination_id(sid)
    return {
        "id": iid,
        "external_id": iid,
        "module_id": MODULE_ID,
        "title": template["title"],
        "summary": template["summary"],
        "interpretation": template["interpretation"],
        "business_implication": template["business_implication"],
        "recommended_attention": template["recommended_attention"],
        "confidence": template["confidence"],
        "related_signals": [sid],
        "status": "active",
        "signal_type": signal.signal_type,
    }


def derive_illuminations(signals: list[SignalItem]) -> list[dict]:
    """Derive rule-based illuminations from operational signals only."""
    seen_titles: set[str] = set()
    items: list[dict] = []
    for signal in signals:
        illum = illumination_from_signal(signal)
        if not illum:
            continue
        dedupe_key = f"{illum['title']}:{signal.signal_type}"
        if dedupe_key in seen_titles:
            continue
        seen_titles.add(dedupe_key)
        items.append(illum)
    return items
