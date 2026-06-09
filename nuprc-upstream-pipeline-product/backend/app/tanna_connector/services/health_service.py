"""Health service — read-only aggregation with connector maturity (v0.2)."""
from app.tanna_connector.adapters import catalog_adapter, health_adapter
from app.tanna_connector.config import (
    CONNECTOR_VERSION,
    FRESHNESS_DEGRADED_THRESHOLD,
    IMPLEMENTATION_MATURITY,
)
from app.tanna_connector.envelope import build_envelope


def _component(name: str, status: str, details: dict | None = None, note: str = "") -> dict:
    comp = {"name": name, "status": status, "details": details or {}}
    if note:
        comp["note"] = note
    return comp


def _overall_from_components(components: list[dict], db_ok: bool) -> str:
    statuses = [c["status"] for c in components]
    if any(s == "degraded" for s in statuses):
        return "degraded"
    unavailable = sum(1 for s in statuses if s == "unavailable")
    if unavailable == len(statuses):
        return "unavailable"
    if unavailable > 0 or not db_ok:
        return "degraded"
    return "healthy"


def get_health() -> dict:
    warnings: list[str] = []
    raw, w = health_adapter.collect_health_raw()
    warnings.extend(w)

    db_ok = raw.get("database", {}).get("connected", False)
    service_health = _component(
        "service_health",
        "healthy",
        {"liveness": raw.get("liveness", {})},
    )

    pipeline_health = _component(
        "pipeline_health",
        "unavailable",
        {"reason": "no ETL runs"},
        note="Latest pipeline run could not be determined.",
    )
    latest = raw.get("latest_run")
    if latest:
        run_status = (latest.get("status") or "unknown").lower()
        if run_status == "success":
            pipeline_health = _component("pipeline_health", "healthy", {"latest_run": latest})
        elif run_status == "running":
            pipeline_health = _component(
                "pipeline_health",
                "degraded",
                {"latest_run": latest},
                note="Pipeline run is currently in progress.",
            )
        else:
            pipeline_health = _component(
                "pipeline_health",
                "degraded",
                {"latest_run": latest},
                note=f"Latest run status is {run_status}.",
            )
    else:
        warnings.append("Latest pipeline run unavailable")

    blocking = raw.get("blocking_runs") or []
    if blocking:
        pipeline_health["status"] = "degraded"
        pipeline_health["details"]["blocking_runs"] = len(blocking)

    sources = raw.get("sources_health") or []
    degraded_sources = [s for s in sources if s.get("status") in ("degraded", "down")]
    if sources:
        source_health = _component(
            "source_health",
            "degraded" if degraded_sources else "healthy",
            {"sources": sources, "degraded_count": len(degraded_sources)},
        )
    else:
        source_health = _component(
            "source_health",
            "unavailable",
            {"reason": "sources_health probe returned no data"},
            note="Source health unavailable; internal probe did not return results.",
        )
        warnings.append("Source health unavailable")

    freshness = raw.get("gold_freshness") or []
    degraded_fresh = [
        f for f in freshness
        if f.get("freshness_score", 100) < FRESHNESS_DEGRADED_THRESHOLD
        or f.get("status") in ("degraded", "down")
    ]
    if freshness:
        freshness_health = _component(
            "freshness_health",
            "degraded" if degraded_fresh else "healthy",
            {"sources": freshness, "degraded_count": len(degraded_fresh)},
        )
    else:
        freshness_health = _component(
            "freshness_health",
            "unavailable",
            {"reason": "gold freshness probe returned no data"},
            note="Gold freshness unavailable.",
        )
        warnings.append("Gold freshness unavailable")

    catalog_summary = raw.get("catalog_summary") or {}
    catalog_issues, w = catalog_adapter.get_catalog_freshness_issues()
    warnings.extend(w)
    if catalog_summary or catalog_issues:
        catalog_status = "degraded" if catalog_issues else "healthy"
        catalog_health = _component(
            "catalog_health",
            catalog_status,
            {"summary": catalog_summary, "freshness_issues": catalog_issues},
        )
    else:
        catalog_health = _component(
            "catalog_health",
            "unavailable",
            {"reason": "catalog summary unavailable"},
            note="Catalog diagnostics could not be collected.",
        )

    connector_health = _component(
        "connector_health",
        "healthy",
        {
            "connector_version": CONNECTOR_VERSION,
            "authenticated_surface": True,
            "read_only": True,
        },
        note="Tanna connector surface is operational and read-only.",
    )

    partial_count = sum(
        1 for m in IMPLEMENTATION_MATURITY.values() if m["status"] == "partial"
    )
    not_impl_count = sum(
        1 for m in IMPLEMENTATION_MATURITY.values() if m["status"] == "not_implemented"
    )
    implementation_maturity = _component(
        "implementation_maturity",
        "partial" if partial_count or not_impl_count else "implemented",
        {
            "connector_version": CONNECTOR_VERSION,
            "object_maturity": {
                k: v["status"] for k, v in IMPLEMENTATION_MATURITY.items()
            },
            "partial_objects": partial_count,
            "not_implemented_objects": not_impl_count,
        },
        note="See GET /api/v1/tanna/status for full maturity matrix.",
    )

    components = [
        service_health,
        pipeline_health,
        source_health,
        freshness_health,
        catalog_health,
        connector_health,
        implementation_maturity,
    ]
    overall = _overall_from_components(
        [service_health, pipeline_health, source_health, freshness_health, catalog_health],
        db_ok,
    )

    health_item = {
        "status": overall,
        "database_connected": db_ok,
        "components": components,
    }

    impl_status = "partial"
    if partial_count == 0 and not_impl_count == 0:
        impl_status = "implemented"

    return build_envelope(
        object_type="health",
        implementation_status=impl_status,
        items=[health_item],
        source="petrocore.tanna_connector.health_service",
        notes=(
            "Aggregated read-only from existing /health, /v1/pipeline/*, catalog, "
            "and connector maturity. Unavailable components are labeled, not fatal."
        ),
        warnings=warnings,
    )
