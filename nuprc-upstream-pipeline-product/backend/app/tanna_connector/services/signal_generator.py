"""Generate operational signals on read from existing platform evidence."""
import hashlib
from datetime import datetime, timezone
from typing import Any

from app.tanna_connector.adapters import catalog_adapter, pipeline_adapter
from app.tanna_connector.config import (
    FRESHNESS_DEGRADED_THRESHOLD,
    SOURCE_KEY_TO_DATA_PRODUCT,
    SOURCE_KEY_TO_ENTITY,
)
from app.tanna_connector.schemas.signal import SignalItem


def _signal_id(signal_type: str, key: str) -> str:
    digest = hashlib.sha256(f"{signal_type}:{key}".encode()).hexdigest()[:12]
    return f"sig-{signal_type.lower()}-{digest}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_key_for_signal(sig: SignalItem) -> str:
    backing = sig.backing_data or {}
    if sig.signal_type in ("PIPELINE_RUN_FAILED", "PIPELINE_RUN_BLOCKED", "PIPELINE_RUN_RUNNING"):
        return str(backing.get("run_id", sig.signal_id))
    if sig.signal_type == "PIPELINE_STEP_FAILED":
        return str(backing.get("step_key", sig.signal_id))
    if sig.signal_type in ("DATA_FRESHNESS_DEGRADED", "SOURCE_UNAVAILABLE"):
        return str(backing.get("source_key", sig.signal_id))
    if sig.signal_type == "SCHEMA_DRIFT_DETECTED":
        return "silver_schema_drift"
    if sig.signal_type == "CATALOG_FRESHNESS_ISSUE":
        return str(backing.get("issue_key", sig.signal_id))
    return sig.signal_id.replace("sig-", "")


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _related_for_source(source_key: str | None) -> tuple[list[str], list[str]]:
    if not source_key:
        return [], []
    entities = [SOURCE_KEY_TO_ENTITY[source_key]] if source_key in SOURCE_KEY_TO_ENTITY else []
    products = [SOURCE_KEY_TO_DATA_PRODUCT[source_key]] if source_key in SOURCE_KEY_TO_DATA_PRODUCT else []
    return entities, products


def generate_signals() -> tuple[list[SignalItem], list[str]]:
    warnings: list[str] = []
    signals: list[SignalItem] = []

    latest, w = pipeline_adapter.get_latest_run()
    warnings.extend(w)
    if latest:
        run_status = (latest.get("status") or "").lower()
        run_id = latest.get("run_id", "")
        if run_status == "failed":
            signals.append(SignalItem(
                signal_id=_signal_id("PIPELINE_RUN_FAILED", run_id),
                signal_type="PIPELINE_RUN_FAILED",
                severity="critical",
                title="Latest ETL run failed",
                description=f"Run {run_id} ended with status failed.",
                source="admin.etl_runs",
                detected_at=_iso(latest.get("ended_at")) or _now_iso(),
                confidence=0.95,
                backing_data={"run_id": run_id, "mode": latest.get("mode")},
            ))
        elif run_status == "running":
            signals.append(SignalItem(
                signal_id=_signal_id("PIPELINE_RUN_RUNNING", run_id),
                signal_type="PIPELINE_RUN_RUNNING",
                severity="warning",
                title="Pipeline run in progress",
                description=f"Run {run_id} is currently running.",
                source="admin.etl_runs",
                detected_at=_iso(latest.get("started_at")) or _now_iso(),
                confidence=0.9,
                backing_data={"run_id": run_id, "mode": latest.get("mode")},
            ))

    failed_steps, w = pipeline_adapter.get_failed_steps_for_latest_run()
    warnings.extend(w)
    for step in failed_steps:
        step_key = step.get("step_key", "")
        signals.append(SignalItem(
            signal_id=_signal_id("PIPELINE_STEP_FAILED", step_key),
            signal_type="PIPELINE_STEP_FAILED",
            severity="critical",
            title=f"ETL step failed: {step_key}",
            description=f"Step {step_key} failed during latest run.",
            source="admin.etl_run_steps",
            detected_at=_iso(step.get("ended_at")) or _now_iso(),
            confidence=0.9,
            backing_data={"step_key": step_key, "error_json": step.get("error_json")},
        ))

    blocking, w = pipeline_adapter.get_blocking_runs()
    warnings.extend(w)
    for run in blocking:
        run_id = run.get("run_id", "")
        signals.append(SignalItem(
            signal_id=_signal_id("PIPELINE_RUN_BLOCKED", run_id),
            signal_type="PIPELINE_RUN_BLOCKED",
            severity="warning",
            title="Pipeline run is blocking",
            description=f"Run {run_id} is in running state and may block new runs.",
            source="admin.etl_runs",
            detected_at=_iso(run.get("started_at")) or _now_iso(),
            confidence=0.9,
            backing_data={"run_id": run_id, "mode": run.get("mode")},
        ))

    freshness, w = pipeline_adapter.get_gold_freshness()
    warnings.extend(w)
    for src in freshness:
        score = src.get("freshness_score", 100)
        status = src.get("status", "")
        source_key = src.get("source_key", "")
        if score < FRESHNESS_DEGRADED_THRESHOLD or status in ("degraded", "down"):
            severity = "critical" if status == "down" else "warning"
            entities, products = _related_for_source(source_key)
            signals.append(SignalItem(
                signal_id=_signal_id("DATA_FRESHNESS_DEGRADED", source_key),
                signal_type="DATA_FRESHNESS_DEGRADED",
                severity=severity,
                title=f"Freshness degraded: {src.get('label')}",
                description=(
                    f"{src.get('label')} freshness score is {score} (status={status})."
                ),
                source="gold_freshness",
                detected_at=src.get("last_updated") or _now_iso(),
                confidence=0.85,
                backing_data=src,
                related_entities=entities,
                related_data_products=products,
            ))

    sources, w = pipeline_adapter.get_sources_health()
    warnings.extend(w)
    for src in sources:
        if src.get("status") in ("down", "degraded"):
            source_key = src.get("source_key", "")
            entities, products = _related_for_source(source_key)
            signals.append(SignalItem(
                signal_id=_signal_id("SOURCE_UNAVAILABLE", source_key),
                signal_type="SOURCE_UNAVAILABLE",
                severity="critical" if src.get("status") == "down" else "warning",
                title=f"Source {src.get('status')}: {src.get('label')}",
                description=(
                    f"Bronze source health for {src.get('label')} is {src.get('status')}."
                ),
                source="sources_health",
                detected_at=_now_iso(),
                confidence=0.8,
                backing_data=src,
                related_entities=entities,
                related_data_products=products,
            ))

    drift_count, w = catalog_adapter.get_schema_drift_count()
    warnings.extend(w)
    if drift_count is not None and drift_count > 0:
        signals.append(SignalItem(
            signal_id=_signal_id("SCHEMA_DRIFT_DETECTED", "silver.schema_drift"),
            signal_type="SCHEMA_DRIFT_DETECTED",
            severity="warning",
            title="Schema drift detected",
            description=f"{drift_count} schema drift record(s) found in silver.schema_drift.",
            source="silver.schema_drift",
            detected_at=_now_iso(),
            confidence=0.85,
            backing_data={"count": drift_count},
        ))

    catalog_issues, w = catalog_adapter.get_catalog_freshness_issues()
    warnings.extend(w)
    for issue in catalog_issues:
        issue_key = issue.get("issue_key", "catalog")
        severity = issue.get("severity", "warning")
        signals.append(SignalItem(
            signal_id=_signal_id("CATALOG_FRESHNESS_ISSUE", issue_key),
            signal_type="CATALOG_FRESHNESS_ISSUE",
            severity="critical" if severity == "critical" else "warning",
            title=f"Catalog freshness issue: {issue_key.replace('_', ' ')}",
            description=issue.get("description", "Catalog freshness issue detected."),
            source="data_catalog",
            detected_at=_now_iso(),
            confidence=0.8,
            backing_data=issue,
        ))

    return signals, warnings
