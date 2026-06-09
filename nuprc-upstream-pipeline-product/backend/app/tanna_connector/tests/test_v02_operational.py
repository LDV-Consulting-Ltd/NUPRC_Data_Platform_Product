"""PetroCore Tanna Connector v0.2 operational intelligence tests."""
from unittest.mock import MagicMock

import pytest

from app.tanna_connector.config import FORBIDDEN_ANALYTICAL_TERMS, OPERATIONAL_SIGNAL_TYPES
from app.tanna_connector.schemas.signal import SignalItem
from app.tanna_connector.services.operational_rules import derive_illuminations


def _mock_signals(monkeypatch):
    signals = [
        SignalItem(
            signal_id="sig-pipeline_run_failed-abc",
            signal_type="PIPELINE_RUN_FAILED",
            severity="critical",
            title="Latest ETL run failed",
            description="Run run-1 ended with status failed.",
            source="admin.etl_runs",
            detected_at="2026-01-01T00:00:00+00:00",
            confidence=0.95,
        ),
        SignalItem(
            signal_id="sig-data_freshness_degraded-def",
            signal_type="DATA_FRESHNESS_DEGRADED",
            severity="warning",
            title="Freshness degraded: Oil Production",
            description="Oil Production freshness score is 55 (status=degraded).",
            source="gold_freshness",
            detected_at="2026-01-01T00:00:00+00:00",
            confidence=0.85,
            related_data_products=["petrocore:data_product:gold_oil_fact_production"],
        ),
        SignalItem(
            signal_id="sig-schema_drift_detected-ghi",
            signal_type="SCHEMA_DRIFT_DETECTED",
            severity="warning",
            title="Schema drift detected",
            description="3 schema drift record(s) found in silver.schema_drift.",
            source="silver.schema_drift",
            detected_at="2026-01-01T00:00:00+00:00",
            confidence=0.85,
        ),
    ]
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.generate_signals",
        lambda: (signals, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_service.generate_signals",
        lambda: (signals, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.illumination_service.generate_signals",
        lambda: (signals, []),
    )


def test_operational_signals_from_evidence_only(tanna_client, auth_headers, monkeypatch):
    _mock_signals(monkeypatch)
    data = tanna_client.get("/api/v1/tanna/signals", headers=auth_headers).json()
    assert data["object_type"] == "signals"
    assert data["implementation_status"] == "partial"
    for item in data["items"]:
        assert item["signal_type"] in OPERATIONAL_SIGNAL_TYPES
        combined = f"{item['name']} {item['description']}".lower()
        assert not any(term in combined for term in FORBIDDEN_ANALYTICAL_TERMS)


def test_illuminations_derived_from_signals_only(tanna_client, auth_headers, monkeypatch):
    _mock_signals(monkeypatch)
    signals_data = tanna_client.get("/api/v1/tanna/signals", headers=auth_headers).json()
    illum_data = tanna_client.get("/api/v1/tanna/illuminations", headers=auth_headers).json()
    assert illum_data["implementation_status"] == "partial"
    assert len(illum_data["items"]) > 0
    signal_ids = {s["id"] for s in signals_data["items"]}
    for illum in illum_data["items"]:
        assert illum["related_signals"]
        assert all(rid in signal_ids for rid in illum["related_signals"])
        combined = " ".join([
            illum.get("title", ""),
            illum.get("summary", ""),
            illum.get("interpretation", ""),
        ]).lower()
        assert "production decline" not in combined
        assert "operator performance" not in combined


def test_status_endpoint_returns_maturity_matrix(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/status", headers=auth_headers).json()
    assert data["object_type"] == "status"
    assert data["implementation_status"] == "implemented"
    matrix = data["items"][0]["endpoint_maturity_matrix"]
    types = {m["object_type"]: m["implementation_status"] for m in matrix}
    assert types["patterns"] == "not_implemented"
    assert types["decision_products"] == "placeholder"
    assert types["data_products"] == "implemented"
    assert types["signals"] == "partial"
    assert all("notes" in m for m in matrix)


def test_health_includes_connector_and_maturity_components(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/health", headers=auth_headers).json()
    names = {c["name"] for c in data["items"][0]["components"]}
    assert "connector_health" in names
    assert "implementation_maturity" in names
    assert "service_health" in names
    assert "catalog_health" in names


def test_patterns_remain_not_implemented(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/patterns", headers=auth_headers).json()
    assert data["implementation_status"] == "not_implemented"
    assert data["items"] == []


def test_decision_products_remain_placeholder(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/decision-products", headers=auth_headers).json()
    assert data["implementation_status"] == "placeholder"
    assert all(i.get("placeholder") is True for i in data["items"])
    assert all(i.get("status") == "draft" for i in data["items"])


def test_status_endpoint_requires_token(tanna_client):
    assert tanna_client.get("/api/v1/tanna/status").status_code == 401


def test_catalog_freshness_signal_generated(tanna_client, auth_headers, monkeypatch):
    issues = [{
        "issue_key": "failed_downloads",
        "severity": "warning",
        "count": 2,
        "description": "2 downloaded file(s) with failed status.",
    }]
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_catalog_freshness_issues",
        lambda: (issues, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.pipeline_adapter.get_latest_run",
        lambda: (None, []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.pipeline_adapter.get_failed_steps_for_latest_run",
        lambda: ([], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.pipeline_adapter.get_blocking_runs",
        lambda: ([], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.pipeline_adapter.get_gold_freshness",
        lambda: ([], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.services.signal_generator.pipeline_adapter.get_sources_health",
        lambda: ([], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_schema_drift_count",
        lambda: (0, []),
    )
    data = tanna_client.get("/api/v1/tanna/signals", headers=auth_headers).json()
    types = [i["signal_type"] for i in data["items"]]
    assert "CATALOG_FRESHNESS_ISSUE" in types


def test_no_analytical_signals_in_generator(monkeypatch):
    from app.tanna_connector.services import signal_generator as sg

    monkeypatch.setattr(sg.pipeline_adapter, "get_latest_run", lambda: (None, []))
    monkeypatch.setattr(sg.pipeline_adapter, "get_failed_steps_for_latest_run", lambda: ([], []))
    monkeypatch.setattr(sg.pipeline_adapter, "get_blocking_runs", lambda: ([], []))
    monkeypatch.setattr(sg.pipeline_adapter, "get_gold_freshness", lambda: ([], []))
    monkeypatch.setattr(sg.pipeline_adapter, "get_sources_health", lambda: ([], []))
    monkeypatch.setattr(sg.catalog_adapter, "get_schema_drift_count", lambda: (0, []))
    monkeypatch.setattr(sg.catalog_adapter, "get_catalog_freshness_issues", lambda: ([], []))
    signals, _ = sg.generate_signals()
    for sig in signals:
        combined = f"{sig.title} {sig.description}".lower()
        assert not any(term in combined for term in FORBIDDEN_ANALYTICAL_TERMS)


def test_derive_illuminations_unit():
    signals = [
        SignalItem(
            signal_id="sig-catalog_freshness_issue-x",
            signal_type="CATALOG_FRESHNESS_ISSUE",
            severity="warning",
            title="Catalog freshness issue: failed downloads",
            description="2 downloaded file(s) with failed status.",
            source="data_catalog",
            detected_at="2026-01-01T00:00:00+00:00",
            confidence=0.8,
        ),
    ]
    items = derive_illuminations(signals)
    assert len(items) == 1
    assert "Catalog refresh may be incomplete" in items[0]["title"]


def test_connector_endpoints_still_token_protected(tanna_client, auth_headers):
    for path in ["/api/v1/tanna/signals", "/api/v1/tanna/status", "/api/v1/tanna/illuminations"]:
        assert tanna_client.get(path).status_code == 401
        assert tanna_client.get(path, headers=auth_headers).status_code == 200


def test_existing_health_endpoint_untouched():
    from app.main import app
    from fastapi.testclient import TestClient
    assert TestClient(app).get("/health/summary").status_code == 200


def test_no_etl_side_effects(tanna_client, auth_headers, monkeypatch):
    mock_run_etl = MagicMock(side_effect=AssertionError("run_etl must not be called"))
    monkeypatch.setattr("etl.run.run_etl", mock_run_etl, raising=False)
    for path in ["/api/v1/tanna/signals", "/api/v1/tanna/status", "/api/v1/tanna/illuminations"]:
        tanna_client.get(path, headers=auth_headers)
    mock_run_etl.assert_not_called()
