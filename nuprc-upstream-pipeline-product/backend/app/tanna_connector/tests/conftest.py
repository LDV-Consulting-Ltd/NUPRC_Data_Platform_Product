"""Shared fixtures for PetroCore Tanna Connector v0.1 tests."""
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_backend = Path(__file__).resolve().parents[2]
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
sys.path[:] = [p for p in sys.path if "myto-platform" not in p.replace("\\", "/")]

os.environ.setdefault("TANNA_CONNECTOR_TOKEN", "test-token-for-ci")


@pytest.fixture
def tanna_client():
    from app.tanna_connector.router import router as tanna_router
    app = FastAPI()
    app.include_router(tanna_router)
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-for-ci"}
