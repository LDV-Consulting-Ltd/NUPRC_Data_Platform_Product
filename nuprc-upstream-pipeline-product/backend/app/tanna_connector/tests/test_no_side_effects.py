"""Ensure connector does not trigger ETL execution."""
from unittest.mock import MagicMock


def test_tanna_endpoints_do_not_call_run_etl(tanna_client, auth_headers, monkeypatch):
    mock_run_etl = MagicMock(side_effect=AssertionError("run_etl must not be called"))
    monkeypatch.setattr("etl.run.run_etl", mock_run_etl, raising=False)

    for path in [
        "/api/v1/tanna/manifest",
        "/api/v1/tanna/health",
        "/api/v1/tanna/data-products",
        "/api/v1/tanna/signals",
        "/api/v1/tanna/patterns",
    ]:
        assert tanna_client.get(path, headers=auth_headers).status_code == 200
    mock_run_etl.assert_not_called()


def test_patterns_not_implemented(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/patterns", headers=auth_headers).json()
    assert data["implementation_status"] == "not_implemented"
    assert data["items"] == []


def test_decision_products_are_stubs(tanna_client, auth_headers):
    data = tanna_client.get("/api/v1/tanna/decision-products", headers=auth_headers).json()
    assert data["implementation_status"] == "placeholder"
    assert all(i.get("placeholder") for i in data["items"])
