"""Health endpoint tests (v0.1 envelope)."""


def test_health_returns_envelope_when_db_unavailable(tanna_client, auth_headers, monkeypatch):
    def _fail_connectivity():
        return False, "connection refused", ["Database connectivity check failed"]

    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.test_database_connectivity",
        _fail_connectivity,
    )
    response = tanna_client.get("/api/v1/tanna/health", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["object_type"] == "health"
    assert data["implementation_status"] == "partial"
    assert "components" in data["items"][0]


def test_health_has_service_component(tanna_client, auth_headers):
    response = tanna_client.get("/api/v1/tanna/health", headers=auth_headers)
    names = [c["name"] for c in response.json()["items"][0]["components"]]
    assert "service_health" in names
