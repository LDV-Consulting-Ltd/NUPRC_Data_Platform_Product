"""PetroCore Tanna Connector v0.2.1 contract validation & sync readiness tests."""
from unittest.mock import MagicMock

import pytest

from app.tanna_connector.config import (
    ENDPOINT_MATURITY_KEYS,
    FORBIDDEN_ANALYTICAL_TERMS,
    FORBIDDEN_INVENTED_ENTITIES,
    FORBIDDEN_INVENTED_PRODUCTS,
    IMPLEMENTATION_MATURITY,
)
from app.tanna_connector.contract_schemas import ENDPOINT_OBJECT_TYPES
from app.tanna_connector.contract_validation import validate_envelope, validate_full_response
from app.tanna_connector.external_ids import MODULE_PREFIX

CONNECTOR_ENDPOINTS = [
    "/api/v1/tanna/manifest",
    "/api/v1/tanna/health",
    "/api/v1/tanna/status",
    "/api/v1/tanna/data-products",
    "/api/v1/tanna/entities",
    "/api/v1/tanna/relationships",
    "/api/v1/tanna/signals",
    "/api/v1/tanna/patterns",
    "/api/v1/tanna/illuminations",
    "/api/v1/tanna/decision-products",
    "/api/v1/tanna/knowledge-assets",
]

ENVELOPE_ENDPOINTS = [e for e in CONNECTOR_ENDPOINTS if e != "/api/v1/tanna/status"]


def _assert_standard_envelope(data: dict):
    assert data["module_id"] == "petrocore"
    assert data["module_name"] == "PetroCore"
    assert data["object_type"]
    assert data["implementation_status"] in {
        "implemented", "partial", "placeholder", "not_implemented",
    }
    assert "items" in data
    assert "metadata" in data
    meta = data["metadata"]
    assert "source" in meta
    assert "notes" in meta
    assert "generated_at" in meta
    assert "sync_ready" in meta
    assert "sync_notes" in meta
    assert "external_id_strategy" in meta
    assert "duplicate_handling_notes" in meta


@pytest.mark.parametrize("path", CONNECTOR_ENDPOINTS)
def test_every_endpoint_requires_token(tanna_client, path):
    assert tanna_client.get(path).status_code == 401


@pytest.mark.parametrize("path", CONNECTOR_ENDPOINTS)
def test_every_endpoint_returns_standard_envelope(tanna_client, auth_headers, path):
    data = tanna_client.get(path, headers=auth_headers).json()
    _assert_standard_envelope(data)
    assert validate_full_response(data) == []


@pytest.mark.parametrize("path", CONNECTOR_ENDPOINTS)
def test_module_identity_always_petrocore(tanna_client, auth_headers, path):
    data = tanna_client.get(path, headers=auth_headers).json()
    assert data["module_id"] == "petrocore"
    assert data["module_name"] == "PetroCore"


def test_patterns_not_implemented_empty(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/patterns", headers=auth_headers).json()
    assert data["implementation_status"] == "not_implemented"
    assert data["items"] == []
    assert data["metadata"]["sync_ready"] is False


def test_decision_products_placeholder_contract(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/decision-products", headers=auth_headers).json()
    assert data["implementation_status"] == "placeholder"
    assert data["metadata"]["sync_ready"] is False
    for item in data["items"]:
        assert item["placeholder"] is True
        assert item["status"] == "draft"
        assert "note" in item
        assert item["external_id"].startswith(f"{MODULE_PREFIX}:")


def test_status_endpoint_maturity_matrix(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/status", headers=auth_headers).json()
    item = data["items"][0]
    assert item["connector_version"] == "0.2.1"
    assert item["module_id"] == "petrocore"
    assert item["overall_status"] in {"partial", "implemented"}
    assert "last_generated_at" in item
    matrix = {m["object_type"]: m["implementation_status"] for m in item["endpoint_maturity_matrix"]}
    for key in ENDPOINT_MATURITY_KEYS:
        assert key in matrix
        assert matrix[key] == IMPLEMENTATION_MATURITY[key]["status"]
    assert set(item["implemented_objects"]) == {
        k for k, v in IMPLEMENTATION_MATURITY.items()
        if v["status"] == "implemented" and k in ENDPOINT_MATURITY_KEYS
    }


def test_no_invented_data_products(tanna_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_gold_tables",
        lambda: ([
            {
                "physical_name": "gold_oil_fact_production",
                "display_name": "Oil Production",
                "row_count": 10,
                "last_updated": None,
            }
        ], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_table_display",
        lambda: ({}, []),
    )
    data = tanna_client.get("/api/v1/tanna/data-products", headers=auth_headers).json()
    names = " ".join(i.get("name", "") for i in data["items"]).lower()
    for forbidden in FORBIDDEN_INVENTED_PRODUCTS:
        assert forbidden not in names
    for item in data["items"]:
        assert item["external_id"].startswith(f"{MODULE_PREFIX}:data_product:")


def test_no_invented_entities(tanna_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.fetch_entity_rows",
        lambda *a, **k: ([], 0, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_ingested_documents",
        lambda *a, **k: ([], 0, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.safe_count",
        lambda *a, **k: (0, []),
    )
    data = tanna_client.get("/api/v1/tanna/entities", headers=auth_headers).json()
    text = str(data["items"]).lower()
    for forbidden in FORBIDDEN_INVENTED_ENTITIES:
        assert forbidden not in text or forbidden == "field"


def test_no_analytical_signals(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/signals", headers=auth_headers).json()
    for item in data["items"]:
        combined = f"{item.get('name', '')} {item.get('description', '')}".lower()
        for term in FORBIDDEN_ANALYTICAL_TERMS:
            assert term not in combined
        assert item["external_id"].startswith(f"{MODULE_PREFIX}:signal:")


def test_sync_readiness_metadata_rules(tanna_client, auth_headers):
    implemented = tanna_client.get("/api/v1/tanna/data-products", headers=auth_headers).json()
    assert implemented["metadata"]["sync_ready"] is True

    placeholder = tanna_client.get("/api/v1/tanna/decision-products", headers=auth_headers).json()
    assert placeholder["metadata"]["sync_ready"] is False

    not_impl = tanna_client.get("/api/v1/tanna/patterns", headers=auth_headers).json()
    assert not_impl["metadata"]["sync_ready"] is False

    partial = tanna_client.get("/api/v1/tanna/signals", headers=auth_headers).json()
    assert partial["metadata"]["sync_ready"] is True


def test_external_id_prefix_on_items_with_ids(tanna_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_gold_tables",
        lambda: ([{"physical_name": "gold_oil_fact_production", "row_count": 1}], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_table_display",
        lambda: ({}, []),
    )
    for path in [
        "/api/v1/tanna/data-products",
        "/api/v1/tanna/relationships",
        "/api/v1/tanna/decision-products",
        "/api/v1/tanna/knowledge-assets",
    ]:
        for item in tanna_client.get(path, headers=auth_headers).json()["items"]:
            assert item["external_id"].startswith(f"{MODULE_PREFIX}:")
            assert item["id"] == item["external_id"]


def test_schema_validation_unit():
    payload = {
        "module_id": "petrocore",
        "module_name": "PetroCore",
        "object_type": "patterns",
        "implementation_status": "not_implemented",
        "items": [],
        "metadata": {
            "source": "test",
            "notes": "test",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "warnings": [],
            "sync_ready": False,
            "sync_notes": "n/a",
            "external_id_strategy": "n/a",
            "duplicate_handling_notes": "n/a",
        },
    }
    envelope = validate_envelope(payload)
    assert envelope.object_type == "patterns"
    assert validate_full_response(payload) == []


def test_existing_health_endpoint_untouched():
    from app.main import app
    from fastapi.testclient import TestClient
    assert TestClient(app).get("/health/summary").status_code == 200


def test_no_etl_side_effects(tanna_client, auth_headers, monkeypatch):
    mock_run_etl = MagicMock(side_effect=AssertionError("run_etl must not be called"))
    monkeypatch.setattr("etl.run.run_etl", mock_run_etl, raising=False)
    for path in CONNECTOR_ENDPOINTS:
        tanna_client.get(path, headers=auth_headers)
    mock_run_etl.assert_not_called()
