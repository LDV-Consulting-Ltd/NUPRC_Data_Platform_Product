from datetime import datetime, timezone

from app.tanna_connector.adapters import health_adapter
from app.tanna_connector.config import FRESHNESS_DEGRADED_THRESHOLD
from app.tanna_connector.schemas.health import HealthComponent, HealthResponse
from app.tanna_connector.services.aggregator import score_to_status


def build_health() -> HealthResponse:
    raw, warnings = health_adapter.collect_health_raw()
    components: list[HealthComponent] = []

    components.append(HealthComponent(
        name="service_liveness",
        status="healthy",
        score=100,
        message="FastAPI service is running",
        details=raw.get("liveness", {}),
    ))

    db = raw.get("database", {})
    if db.get("connected"):
        components.append(HealthComponent(
            name="database",
            status="healthy",
            score=100,
            message="Database connectivity OK",
        ))
    else:
        components.append(HealthComponent(
            name="database",
            status="down",
            score=0,
            message=db.get("error") or "Database unavailable",
        ))

    latest = raw.get("latest_run")
    if latest:
        run_status = (latest.get("status") or "unknown").lower()
        if run_status == "success":
            rs, rscore = "healthy", 95
        elif run_status == "running":
            rs, rscore = "degraded", 70
        elif run_status == "failed":
            rs, rscore = "down", 30
        else:
            rs, rscore = "degraded", 60
        components.append(HealthComponent(
            name="latest_pipeline_run",
            status=rs,
            score=rscore,
            message=f"Latest run status: {run_status}",
            details={"run_id": latest.get("run_id"), "mode": latest.get("mode")},
        ))
    else:
        components.append(HealthComponent(
            name="latest_pipeline_run",
            status="unknown",
            score=50,
            message="No ETL runs found",
        ))
        warnings.append("Latest pipeline run unavailable")

    blocking = raw.get("blocking_runs") or []
    if blocking:
        components.append(HealthComponent(
            name="blocking_runs",
            status="degraded",
            score=55,
            message=f"{len(blocking)} run(s) currently blocking",
            details={"count": len(blocking)},
        ))
    else:
        components.append(HealthComponent(
            name="blocking_runs",
            status="healthy",
            score=100,
            message="No blocking runs",
        ))

    freshness_items = raw.get("gold_freshness") or []
    if freshness_items:
        scores = [f.get("freshness_score", 50) for f in freshness_items]
        avg = sum(scores) // len(scores)
        degraded = [f for f in freshness_items if f.get("freshness_score", 0) < FRESHNESS_DEGRADED_THRESHOLD]
        fs = "healthy" if not degraded else "degraded" if avg >= 50 else "down"
        components.append(HealthComponent(
            name="gold_freshness",
            status=fs,
            score=avg,
            message=f"{len(degraded)} source(s) below freshness threshold",
            details={"degraded_sources": [d.get("source_key") for d in degraded]},
        ))
    else:
        components.append(HealthComponent(
            name="gold_freshness",
            status="unknown",
            score=50,
            message="Gold freshness data unavailable",
        ))
        warnings.append("Gold freshness unavailable")

    gold_tables = raw.get("gold_tables") or []
    if gold_tables:
        empty = [t for t in gold_tables if (t.get("row_count") or 0) == 0]
        gs = "healthy" if not empty else "degraded"
        gscore = 90 if not empty else max(40, 90 - len(empty) * 10)
        components.append(HealthComponent(
            name="gold_tables",
            status=gs,
            score=gscore,
            message=f"{len(gold_tables)} gold table(s); {len(empty)} empty",
            details={"empty_tables": [t.get("physical_name") for t in empty]},
        ))
    else:
        components.append(HealthComponent(
            name="gold_tables",
            status="unknown",
            score=50,
            message="Gold tables unavailable",
        ))

    catalog = raw.get("catalog_summary") or {}
    if catalog.get("file_statistics") or catalog.get("table_statistics"):
        components.append(HealthComponent(
            name="catalog",
            status="healthy",
            score=90,
            message="Catalog tables reachable",
            details={
                "file_stat_groups": len(catalog.get("file_statistics", [])),
                "table_stat_groups": len(catalog.get("table_statistics", [])),
            },
        ))
    else:
        components.append(HealthComponent(
            name="catalog",
            status="degraded",
            score=50,
            message="Catalog summary empty or unavailable",
        ))

    scores = [c.score for c in components if c.score is not None]
    overall_score = sum(scores) // len(scores) if scores else 50
    overall_status = score_to_status(overall_score)

    return HealthResponse(
        status=overall_status,
        score=overall_score,
        components=components,
        warnings=warnings,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
