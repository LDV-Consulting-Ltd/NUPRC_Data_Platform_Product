"""Bearer token validation for /api/v1/tanna/*."""
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_manifest_accepts_token_with_whitespace_padding(client, monkeypatch):
    monkeypatch.setenv("TANNA_CONNECTOR_TOKEN", "  A9kLx2Pq7RmN4Wz8Yt  ")
    response = client.get(
        "/api/v1/tanna/manifest",
        headers={"Authorization": "Bearer  A9kLx2Pq7RmN4Wz8Yt "},
    )
    assert response.status_code == 200
    assert response.json()["object_type"] == "manifest"


def test_manifest_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv("TANNA_CONNECTOR_TOKEN", "expected-token")
    response = client.get(
        "/api/v1/tanna/manifest",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid connector service token"


def test_manifest_returns_503_when_token_unconfigured(client, monkeypatch):
    monkeypatch.delenv("TANNA_CONNECTOR_TOKEN", raising=False)
    response = client.get(
        "/api/v1/tanna/manifest",
        headers={"Authorization": "Bearer any-token"},
    )
    assert response.status_code == 503
