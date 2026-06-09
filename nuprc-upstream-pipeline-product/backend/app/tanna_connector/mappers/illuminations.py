import hashlib
from datetime import datetime, timezone

from app.tanna_connector.adapters import catalog_adapter, pipeline_adapter
from app.tanna_connector.config import FRESHNESS_DEGRADED_THRESHOLD
from app.tanna_connector.mappers.signals import build_signals
from app.tanna_connector.schemas.illumination import IlluminationItem, IlluminationsResponse


def _illum_id(title: str) -> str:
    return "illum-" + hashlib.sha256(title.encode()).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_illuminations() -> IlluminationsResponse:
    warnings: list[str] = []
    items: list[IlluminationItem] = []
    generated_from: list[str] = []

    latest, w = pipeline_adapter.get_latest_run()
    warnings.extend(w)
    gold_tables, w2 = catalog_adapter.get_gold_tables()
    warnings.extend(w2)
    catalog_summary, w3 = catalog_adapter.get_catalog_summary()
    warnings.extend(w3)
    freshness, w4 = pipeline_adapter.get_gold_freshness()
    warnings.extend(w4)
    drift_count, w5 = catalog_adapter.get_schema_drift_count()
    warnings.extend(w5)

    signals_resp = build_signals()
    generated_from.append("signals")

    if latest and (latest.get("status") or "").lower() == "success":
        empty_gold = [t for t in gold_tables if (t.get("row_count") or 0) == 0]
        if not empty_gold:
            items.append(IlluminationItem(
                illumination_id=_illum_id("run-success-gold-available"),
                title="Pipeline run succeeded; gold marts available",
                narrative=(
                    f"Latest pipeline run ({latest.get('run_id')}) completed successfully "
                    "and canonical gold marts are present with data."
                ),
                category="pipeline",
                confidence=0.9,
                generated_from=["admin.etl_runs", "catalog_registry"],
                generated_at=_now_iso(),
            ))
        else:
            items.append(IlluminationItem(
                illumination_id=_illum_id("run-success-gold-empty"),
                title="Pipeline succeeded but some gold tables are empty",
                narrative=(
                    f"Latest run ({latest.get('run_id')}) succeeded, but "
                    f"{len(empty_gold)} gold table(s) have zero rows: "
                    f"{', '.join(t.get('physical_name', '') for t in empty_gold[:5])}."
                ),
                category="catalog",
                confidence=0.85,
                generated_from=["admin.etl_runs", "catalog_registry"],
                generated_at=_now_iso(),
            ))
    elif latest and (latest.get("status") or "").lower() == "failed":
        items.append(IlluminationItem(
            illumination_id=_illum_id("run-failed"),
            title="Latest pipeline run failed",
            narrative=f"Run {latest.get('run_id')} failed. Check /v1/pipeline/runs/{{run_id}}/diagnostics.",
            category="pipeline",
            confidence=0.95,
            generated_from=["admin.etl_runs"],
            generated_at=_now_iso(),
        ))

    degraded_freshness = [
        f for f in freshness
        if f.get("freshness_score", 100) < FRESHNESS_DEGRADED_THRESHOLD
        or f.get("status") in ("degraded", "down")
    ]
    for src in degraded_freshness:
        items.append(IlluminationItem(
            illumination_id=_illum_id(f"freshness-{src.get('source_key')}"),
            title=f"{src.get('label')} freshness is degraded",
            narrative=(
                f"{src.get('label')} has freshness score {src.get('freshness_score')} "
                f"and status '{src.get('status')}'."
            ),
            category="freshness",
            confidence=0.85,
            generated_from=["gold_freshness"],
            generated_at=_now_iso(),
        ))

    if drift_count is not None and drift_count > 0:
        items.append(IlluminationItem(
            illumination_id=_illum_id("schema-drift"),
            title="Schema drift detected in recent loads",
            narrative=f"{drift_count} schema drift event(s) recorded in silver.schema_drift.",
            category="data_quality",
            confidence=0.85,
            generated_from=["silver.schema_drift"],
            generated_at=_now_iso(),
        ))

    if catalog_summary.get("file_statistics") or catalog_summary.get("table_statistics"):
        file_groups = len(catalog_summary.get("file_statistics", []))
        items.append(IlluminationItem(
            illumination_id=_illum_id("catalog-available"),
            title="Data catalog is available",
            narrative=f"Catalog summary reachable with {file_groups} download status group(s).",
            category="catalog",
            confidence=0.8,
            generated_from=["data_catalog"],
            generated_at=_now_iso(),
        ))
    else:
        items.append(IlluminationItem(
            illumination_id=_illum_id("catalog-limited"),
            title="Catalog availability is limited",
            narrative="Catalog summary could not be fully loaded; connector is operating in degraded mode.",
            category="catalog",
            confidence=0.7,
            generated_from=["data_catalog"],
            generated_at=_now_iso(),
        ))

    for sig in signals_resp.items[:3]:
        items.append(IlluminationItem(
            illumination_id=_illum_id(f"signal-{sig.signal_id}"),
            title=sig.title,
            narrative=sig.description,
            category="operational",
            confidence=sig.confidence,
            generated_from=["signals", sig.source],
            generated_at=sig.detected_at,
        ))

    return IlluminationsResponse(status="available", items=items, warnings=warnings)
