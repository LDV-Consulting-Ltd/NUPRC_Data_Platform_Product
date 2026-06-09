"""Health-related read-only probes (service + DB + catalog availability)."""
from typing import Any

from app.tanna_connector.adapters import catalog_adapter, pipeline_adapter


def get_service_liveness() -> dict[str, Any]:
    return {"ok": True, "service": "nuprc-upstream-pipeline-api", "connector": "petrocore-tanna-connector"}


def collect_health_raw() -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    raw: dict[str, Any] = {"liveness": get_service_liveness()}

    db_ok, db_err, w = catalog_adapter.test_database_connectivity()
    warnings.extend(w)
    raw["database"] = {"connected": db_ok, "error": db_err}

    latest, w = pipeline_adapter.get_latest_run()
    warnings.extend(w)
    raw["latest_run"] = latest

    blocking, w = pipeline_adapter.get_blocking_runs()
    warnings.extend(w)
    raw["blocking_runs"] = blocking

    sources, w = pipeline_adapter.get_sources_health()
    warnings.extend(w)
    raw["sources_health"] = sources

    freshness, w = pipeline_adapter.get_gold_freshness()
    warnings.extend(w)
    raw["gold_freshness"] = freshness

    gold_tables, w = catalog_adapter.get_gold_tables()
    warnings.extend(w)
    raw["gold_tables"] = gold_tables

    catalog_summary, w = catalog_adapter.get_catalog_summary()
    warnings.extend(w)
    raw["catalog_summary"] = catalog_summary

    return raw, warnings
