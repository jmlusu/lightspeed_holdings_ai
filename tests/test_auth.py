"""Tests for API Key Authentication (D5-050).

Validates that:
- Missing API key returns 401
- Invalid API key returns 401
- Valid API key allows access
- AUTH_REQUIRED=False allows anonymous access
- Health check remains public regardless of auth settings
- Write endpoints are protected
"""

import pytest
from fastapi.testclient import TestClient

from lightspeed_agents.services import create_app
from lightspeed_agents.services.config import settings
from lightspeed_agents.services.dependencies import reset_dependencies

# Keys used across tests
VALID_KEY = "test-valid-key-001"
ANOTHER_VALID_KEY = "test-valid-key-002"


@pytest.fixture(autouse=True)
def _reset():
    """Reset dependencies before every test."""
    reset_dependencies()
    yield
    reset_dependencies()


def _make_client(
    auth_required: bool = True,
    api_keys: list[str] | None = None,
) -> TestClient:
    """Create a TestClient with overridden settings for isolation."""
    settings.AUTH_REQUIRED = auth_required
    settings.API_KEYS = (
        api_keys if api_keys is not None else [VALID_KEY, ANOTHER_VALID_KEY]
    )
    return TestClient(create_app())


# ── Missing / Invalid key ──────────────────────────────────────────


class TestMissingApiKey:
    """Requests without an X-API-Key header must be rejected when auth is required."""

    def test_get_tasks_without_key_returns_401(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/")
        assert r.status_code == 401

    def test_post_tasks_without_key_returns_401(self):
        client = _make_client()
        r = client.post("/api/v1/tasks/")
        assert r.status_code == 401

    def test_patch_task_without_key_returns_401(self):
        client = _make_client()
        r = client.patch("/api/v1/tasks/abc")
        assert r.status_code == 401

    def test_delete_task_without_key_returns_401(self):
        client = _make_client()
        r = client.delete("/api/v1/tasks/abc")
        assert r.status_code == 401


class TestInvalidApiKey:
    """Requests with an API key not in the configured list must be rejected."""

    def test_invalid_key_returns_401(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": "wrong-key"})
        assert r.status_code == 401

    def test_empty_string_key_returns_401(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": ""})
        assert r.status_code == 401

    def test_invalid_key_detail_message(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": "wrong-key"})
        body = r.json()
        assert body["error"]["message"] == "Invalid API key"


class TestMissingKeyDetailMessage:
    """Verify the error body for missing keys."""

    def test_missing_key_detail_message(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/")
        body = r.json()
        assert body["error"]["message"] == "Missing API key"


# ── Valid key ──────────────────────────────────────────────────────


class TestValidApiKey:
    """Requests with a valid API key must succeed."""

    def test_valid_key_allows_get(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200
        assert r.json()["auth"] == VALID_KEY

    def test_valid_key_allows_post(self):
        client = _make_client()
        r = client.post("/api/v1/tasks/", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_valid_key_allows_patch(self):
        client = _make_client()
        r = client.patch("/api/v1/tasks/abc", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_valid_key_allows_delete(self):
        client = _make_client()
        r = client.delete("/api/v1/tasks/abc", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_second_valid_key_also_works(self):
        client = _make_client()
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": ANOTHER_VALID_KEY})
        assert r.status_code == 200
        assert r.json()["auth"] == ANOTHER_VALID_KEY


# ── AUTH_REQUIRED=False ────────────────────────────────────────────


class TestAuthDisabled:
    """When AUTH_REQUIRED is False all endpoints must be accessible without a key."""

    def test_get_without_key_when_auth_disabled(self):
        client = _make_client(auth_required=False)
        r = client.get("/api/v1/tasks/")
        assert r.status_code == 200
        assert r.json()["auth"] == "anonymous"

    def test_post_without_key_when_auth_disabled(self):
        client = _make_client(auth_required=False)
        r = client.post("/api/v1/tasks/")
        assert r.status_code == 200

    def test_patch_without_key_when_auth_disabled(self):
        client = _make_client(auth_required=False)
        r = client.patch("/api/v1/tasks/abc")
        assert r.status_code == 200

    def test_delete_without_key_when_auth_disabled(self):
        client = _make_client(auth_required=False)
        r = client.delete("/api/v1/tasks/abc")
        assert r.status_code == 200


# ── Health check remains public ────────────────────────────────────


class TestHealthCheckPublic:
    """Health check must always be reachable without authentication."""

    def test_health_check_public_with_auth_enabled(self):
        client = _make_client(auth_required=True)
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_health_check_public_with_auth_disabled(self):
        client = _make_client(auth_required=False)
        r = client.get("/api/v1/health")
        assert r.status_code == 200


# ── Config integration ─────────────────────────────────────────────


class TestConfigIntegration:
    """Verify config settings are respected."""

    def test_empty_api_keys_list_rejects_everything(self):
        client = _make_client(api_keys=[])
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 401

    def test_single_api_key_works(self):
        client = _make_client(api_keys=["single-key"])
        r = client.get("/api/v1/tasks/", headers={"X-API-Key": "single-key"})
        assert r.status_code == 200
