"""PetroCore Tanna Connector v0.1 surface tests."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_backend = Path(__file__).resolve().parents[2]
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
sys.path[:] = [p for p in sys.path if "myto-platform" not in p.replace("\\", "/")]

os.environ["TANNA_CONNECTOR_TOKEN"] = "test-token-for-ci"


@pytest.fixture
def client():
    from app.tanna_connector.router import router as tanna_router
    app = FastAPI()
    app.include_router(tanna_router)
    return TestClient(app)


@pytest.fixture
def headers():
    return {"Authorization": "Bearer test-token-for-ci"}


def _assert_envelope(data: dict, object_type: str):
    assert data["module_id"] == "petrocore"
    assert data["module_name"] == "PetroCore"
    assert data["object_type"] == object_type
    assert "implementation_status" in data
    assert "items" in data
    assert "metadata" in data
    assert "generated_at" in data["metadata"]


def test_missing_token_returns_401(client):
    assert client.get("/api/v1/tanna/manifest").status_code == 401


def test_invalid_token_returns_403(client):
    response = client.get(
        "/api/v1/tanna/manifest",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 403


def test_manifest_returns_petrocore(client, headers):
    response = client.get("/api/v1/tanna/manifest", headers=headers)
    assert response.status_code == 200
    data = response.json()
    _assert_envelope(data, "manifest")
    assert data["implementation_status"] == "implemented"
    assert data["items"][0]["module_id"] == "petrocore"
    assert data["items"][0]["module_name"] == "PetroCore"
    assert data["items"][0]["owner"] == "LDV"


def test_patterns_not_implemented_empty(client, headers):
    response = client.get("/api/v1/tanna/patterns", headers=headers)
    data = response.json()
    _assert_envelope(data, "patterns")
    assert data["implementation_status"] == "not_implemented"
    assert data["items"] == []
    assert "pattern detection" in data["metadata"]["notes"].lower()


def test_decision_products_are_placeholders(client, headers):
    response = client.get("/api/v1/tanna/decision-products", headers=headers)
    data = response.json()
    _assert_envelope(data, "decision_products")
    assert data["implementation_status"] == "placeholder"
    assert all(i.get("placeholder") is True for i in data["items"])
    assert all(i.get("status") == "draft" for i in data["items"])


def test_data_products_no_invented_products(client, headers, monkeypatch):
    def _gold_only_real():
        return [
            {
                "physical_name": "gold_oil_fact_production",
                "display_name": "Oil — Production (Fact)",
                "description": "test",
                "row_count": 10,
                "last_updated": None,
                "subject_area": "Oil",
                "grain": "Date × Operator",
            }
        ], []

    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_gold_tables",
        _gold_only_real,
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_table_display",
        lambda: ({}, []),
    )
    response = client.get("/api/v1/tanna/data-products", headers=headers)
    data = response.json()
    _assert_envelope(data, "data_products")
    names = " ".join(i.get("name", "") for i in data["items"]).lower()
    assert "field performance" not in names
    assert "asset performance" not in names
    ids = [i["id"] for i in data["items"]]
    assert "petrocore:data_product:gold_oil_fact_production" in ids


def test_health_partial_envelope(client, headers):
    response = client.get("/api/v1/tanna/health", headers=headers)
    data = response.json()
    _assert_envelope(data, "health")
    assert data["implementation_status"] == "partial"
    components = data["items"][0]["components"]
    names = {c["name"] for c in components}
    assert "service_health" in names
    assert "pipeline_health" in names


def test_connector_does_not_call_run_etl(client, headers, monkeypatch):
    mock_run_etl = MagicMock(side_effect=AssertionError("run_etl must not be called"))
    monkeypatch.setattr("etl.run.run_etl", mock_run_etl, raising=False)

    endpoints = [
        "/api/v1/tanna/health",
        "/api/v1/tanna/manifest",
        "/api/v1/tanna/data-products",
        "/api/v1/tanna/entities",
        "/api/v1/tanna/relationships",
        "/api/v1/tanna/signals",
        "/api/v1/tanna/patterns",
        "/api/v1/tanna/illuminations",
        "/api/v1/tanna/decision-products",
        "/api/v1/tanna/knowledge-assets",
    ]
    for path in endpoints:
        assert client.get(path, headers=headers).status_code == 200
    mock_run_etl.assert_not_called()


def test_existing_health_endpoint_untouched(client):
    """Existing /health/summary remains available on main app."""
    from app.main import app
    main_client = TestClient(app)
    response = main_client.get("/health/summary")
    assert response.status_code == 200
    assert response.json().get("ok") is True
