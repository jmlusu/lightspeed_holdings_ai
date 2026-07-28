"""Tests for FastAPI Application Factory (D5-001)."""
from fastapi.testclient import TestClient
from lightspeed_agents.services import create_app
from lightspeed_agents.services.dependencies import reset_dependencies


def setup_module():
    reset_dependencies()


class TestHealthCheck:
    def setup_method(self):
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_returns_200(self):
        r = self.client.get("/api/v1/health")
        assert r.status_code == 200

    def test_health_status_healthy(self):
        r = self.client.get("/api/v1/health")
        data = r.json()
        assert data["status"] == "healthy"

    def test_health_has_version(self):
        r = self.client.get("/api/v1/health")
        data = r.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_has_timestamp(self):
        r = self.client.get("/api/v1/health")
        data = r.json()
        assert "timestamp" in data


class TestMiddleware:
    def setup_method(self):
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_request_id_header_added(self):
        r = self.client.get("/api/v1/health")
        assert "X-Request-ID" in r.headers

    def test_custom_request_id_forwarded(self):
        r = self.client.get(
            "/api/v1/health", headers={"X-Request-ID": "test-123"}
        )
        assert r.headers.get("X-Request-ID") == "test-123"


class TestErrorHandlers:
    def setup_method(self):
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_404_returns_json(self):
        r = self.client.get("/api/v1/nonexistent")
        assert r.status_code == 404
        data = r.json()
        assert "error" in data
        assert data["error"]["code"] == 404

    def test_404_error_has_type(self):
        r = self.client.get("/api/v1/nonexistent")
        data = r.json()
        assert data["error"]["type"] == "http_error"


class TestAppFactory:
    def setup_method(self):
        reset_dependencies()

    def test_app_title(self):
        app = create_app()
        assert app.title == "Light Speed Agents API"

    def test_app_version(self):
        app = create_app()
        assert app.version == "0.1.0"

    def test_app_description(self):
        app = create_app()
        assert "AI agent orchestration" in app.description

    def test_cors_configured(self):
        app = create_app()
        middleware_classes = [
            m.cls.__name__
            for m in app.user_middleware
            if hasattr(m, "cls")
        ]
        assert "CORSMiddleware" in middleware_classes

    def test_request_id_middleware_configured(self):
        app = create_app()
        middleware_classes = [
            m.cls.__name__
            for m in app.user_middleware
            if hasattr(m, "cls")
        ]
        assert "RequestIDMiddleware" in middleware_classes

    def test_request_logging_middleware_configured(self):
        app = create_app()
        middleware_classes = [
            m.cls.__name__
            for m in app.user_middleware
            if hasattr(m, "cls")
        ]
        assert "RequestLoggingMiddleware" in middleware_classes


class TestDependencies:
    def setup_method(self):
        reset_dependencies()

    def test_singleton_message_bus(self):
        from lightspeed_agents.services.dependencies import get_message_bus

        bus1 = get_message_bus()
        bus2 = get_message_bus()
        assert bus1 is bus2

    def test_singleton_cost_tracker(self):
        from lightspeed_agents.services.dependencies import get_cost_tracker

        ct1 = get_cost_tracker()
        ct2 = get_cost_tracker()
        assert ct1 is ct2

    def test_singleton_memory_engine(self):
        from lightspeed_agents.services.dependencies import get_memory_engine

        me1 = get_memory_engine()
        me2 = get_memory_engine()
        assert me1 is me2

    def test_reset_clears_singletons(self):
        from lightspeed_agents.services.dependencies import get_message_bus

        bus1 = get_message_bus()
        reset_dependencies()
        bus2 = get_message_bus()
        assert bus1 is not bus2
