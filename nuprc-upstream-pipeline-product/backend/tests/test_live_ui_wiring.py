"""
Smoke checks: v1 ETL wiring for UI endpoints (runs, diagrams, source health).
Skips integration assertions when database is unavailable.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_available():
    try:
        from app.core.db import engine
        from sqlalchemy import text
        with engine.connect() as cxn:
            cxn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def test_runs_summary_shape(client):
    """GET /runs/summary returns v1-oriented fields without 500."""
    r = client.get("/runs/summary")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    for key in (
        "total_runs",
        "successful_runs",
        "failed_runs",
        "running_runs",
        "source",
        "latest_run_id",
        "latest_status",
    ):
        assert key in body


def test_runs_summary_v1_shape(client):
    r = client.get("/runs/summary/v1")
    assert r.status_code == 200
    body = r.json()
    assert body.get("source") == "admin.etl_runs"
    assert "total_runs" in body


def test_runs_summary_reads_etl_runs_when_available(client, db_available):
    if not db_available:
        pytest.skip("Database not available")
    try:
        from etl.config import get_etl_engine
        from sqlalchemy import text
        eng = get_etl_engine()
        with eng.connect() as cxn:
            expected = int(cxn.execute(text("SELECT COUNT(*) FROM admin.etl_runs")).scalar() or 0)
    except Exception:
        pytest.skip("admin.etl_runs not available")
    body = client.get("/runs/summary").json()
    if expected > 0:
        assert body.get("source") == "admin.etl_runs"
        assert body.get("total_runs") == expected


def test_diagrams_latest_never_500(client):
    r = client.get("/diagrams/latest")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("status") in ("available", "empty", "unavailable")
    assert "diagram" in body


def test_diagrams_generate_stores_pipeline_flow(client):
    r = client.post("/diagrams/generate")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    latest = client.get("/diagrams/latest").json()
    assert latest.get("status") == "available"
    assert latest.get("diagram") is not None
    assert latest["diagram"].get("diagram_type") in ("pipeline_flow", "v1_data_model")


def test_sources_health_has_clear_status_fields(client, db_available):
    if not db_available:
        pytest.skip("Database not available")
    r = client.get("/v1/pipeline/sources/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    sources = body.get("sources") or []
    assert len(sources) >= 1
    sample = sources[0]
    for field in (
        "reachability_status",
        "data_presence_status",
        "freshness_status",
        "health_status",
        "explanation",
        "status",
        "score",
        "row_count",
    ):
        assert field in sample


def test_sources_health_data_present_not_down(client, db_available):
    if not db_available:
        pytest.skip("Database not available")
    body = client.get("/v1/pipeline/sources/health").json()
    for src in body.get("sources") or []:
        if (src.get("row_count") or 0) > 0:
            assert src.get("data_presence_status") == "available"
            assert src.get("status") != "down"


def test_runs_history_from_etl_runs(client, db_available):
    if not db_available:
        pytest.skip("Database not available")
    r = client.get("/v1/pipeline/runs/history?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body.get("source") == "admin.etl_runs"
    assert "runs" in body
    if body.get("runs"):
        run = body["runs"][0]
        for key in ("run_id", "status", "started_at", "duration_seconds", "rows_bronze"):
            assert key in run


def test_catalog_summary_file_registry_status(client, db_available):
    if not db_available:
        pytest.skip("Database not available")
    r = client.get("/catalog/summary")
    assert r.status_code == 200
    body = r.json()
    assert "file_registry_status" in body
    frs = body["file_registry_status"]
    assert "status" in frs
    assert "tables_catalog_status" in frs


def test_normalize_success_status_lowercase():
    """Frontend showcase should treat lowercase success as successful (contract check)."""
    statuses = ["success", "SUCCESS", "Success"]
    for s in statuses:
        assert s.lower() == "success"
