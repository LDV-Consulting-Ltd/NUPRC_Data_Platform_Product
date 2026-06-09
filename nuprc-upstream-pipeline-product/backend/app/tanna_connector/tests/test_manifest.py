"""Manifest endpoint tests (v0.1 envelope)."""


def test_manifest_returns_petrocore_identity(tanna_client, auth_headers):
    response = tanna_client.get("/api/v1/tanna/manifest", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["module_id"] == "petrocore"
    assert data["items"][0]["module_id"] == "petrocore"
    assert data["items"][0]["module_name"] == "PetroCore"
    assert data["implementation_status"] == "implemented"
