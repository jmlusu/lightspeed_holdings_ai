"""Tests for Memory Search API endpoint (D5-027)."""

import tempfile

from fastapi.testclient import TestClient

from lightspeed_agents.services import create_app
from lightspeed_agents.services.dependencies import (
    reset_dependencies,
)
from lightspeed_agents.memory.engine import MemoryEngine


def _seed_engine(engine: MemoryEngine) -> None:
    """Seed the memory engine with test data across multiple types."""
    engine.record_task_outcome(
        task_id="t1",
        agent_id="agent-alpha",
        content="Deployed the authentication service to production",
        status="completed",
        department="engineering",
        tags=["deployment", "auth"],
    )
    engine.record_knowledge(
        content="The CI pipeline in engineering uses GitHub Actions for continuous integration",
        agent_id="agent-beta",
        tags=["ci", "devops"],
    )
    engine.record_procedure(
        content="Run pytest before pushing to main branch",
        tags=["testing", "process"],
    )
    engine.record_relationship(
        content="Agent alpha reports to lead engineer in engineering department",
        agent_id="agent-alpha",
        tags=["hierarchy"],
    )
    engine.record_temporal(
        content="Sprint 5 ends on August 8 2026",
        tags=["sprint", "deadline"],
    )
    engine.record_task_outcome(
        task_id="t2",
        agent_id="agent-alpha",
        content="Fixed the database connection pooling issue",
        status="completed",
        department="engineering",
        tags=["bugfix", "database"],
    )


class TestMemorySearchEndpoint:
    """Test the GET /api/v1/memory/search endpoint."""

    def setup_method(self):
        reset_dependencies()
        # Create a temporary directory for the memory store
        self._tmpdir = tempfile.TemporaryDirectory()
        self.engine = MemoryEngine(memory_dir=self._tmpdir.name)
        # Patch the singleton to use our seeded engine
        import lightspeed_agents.services.dependencies as deps

        deps._memory_engine_instance = self.engine
        _seed_engine(self.engine)

        self.app = create_app()
        self.client = TestClient(self.app)

    def teardown_method(self):
        reset_dependencies()
        self._tmpdir.cleanup()

    # --- Basic search ---

    def test_search_returns_200(self):
        r = self.client.get("/api/v1/memory/search?q=deploy")
        assert r.status_code == 200

    def test_search_response_structure(self):
        r = self.client.get("/api/v1/memory/search?q=deploy")
        data = r.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert "search_time_ms" in data
        assert data["query"] == "deploy"

    def test_search_returns_ranked_results(self):
        r = self.client.get("/api/v1/memory/search?q=deploy")
        data = r.json()
        assert data["total"] >= 1
        first = data["results"][0]
        assert first["content"] == "Deployed the authentication service to production"
        assert first["memory_type"] == "episodic"
        assert first["relevance_score"] is not None
        assert first["relevance_score"] > 0

    def test_search_relevance_scores_are_ranked(self):
        """Results returned earlier should have higher relevance scores."""
        r = self.client.get("/api/v1/memory/search?q=engineering")
        data = r.json()
        if data["total"] >= 2:
            scores = [res["relevance_score"] for res in data["results"]]
            # Each score should be >= the next (non-strict, ties allowed)
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]

    def test_search_result_has_expected_fields(self):
        r = self.client.get("/api/v1/memory/search?q=deploy")
        data = r.json()
        first = data["results"][0]
        assert "id" in first
        assert "content" in first
        assert "memory_type" in first
        assert "tags" in first
        assert "agent_id" in first
        assert "relevance_score" in first
        assert "created_at" in first

    def test_search_search_time_is_non_negative(self):
        r = self.client.get("/api/v1/memory/search?q=deploy")
        assert r.json()["search_time_ms"] >= 0

    # --- No results ---

    def test_search_no_results_returns_empty(self):
        r = self.client.get("/api/v1/memory/search?q=xyznonexistent")
        data = r.json()
        assert data["total"] == 0
        assert data["results"] == []

    # --- Query validation ---

    def test_search_empty_query_returns_422(self):
        r = self.client.get("/api/v1/memory/search?q=")
        assert r.status_code == 422

    def test_search_missing_query_returns_422(self):
        r = self.client.get("/api/v1/memory/search")
        assert r.status_code == 422

    # --- Type filter ---

    def test_search_type_filter_episodic(self):
        r = self.client.get("/api/v1/memory/search?q=completed&type=episodic")
        data = r.json()
        for result in data["results"]:
            assert result["memory_type"] == "episodic"

    def test_search_type_filter_semantic(self):
        r = self.client.get("/api/v1/memory/search?q=CI&type=semantic")
        data = r.json()
        for result in data["results"]:
            assert result["memory_type"] == "semantic"

    def test_search_type_filter_procedural(self):
        r = self.client.get("/api/v1/memory/search?q=pytest&type=procedural")
        data = r.json()
        for result in data["results"]:
            assert result["memory_type"] == "procedural"

    def test_search_invalid_type_returns_empty(self):
        """Invalid memory types return an empty result set gracefully."""
        r = self.client.get("/api/v1/memory/search?q=test&type=invalid_type")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["results"] == []

    # --- Limit parameter ---

    def test_search_limit_reduces_results(self):
        r_all = self.client.get("/api/v1/memory/search?q=engineering&limit=100")
        r_limited = self.client.get("/api/v1/memory/search?q=engineering&limit=1")
        assert r_limited.json()["total"] <= 1
        assert r_limited.json()["total"] <= r_all.json()["total"]

    def test_search_limit_max_bound(self):
        """Limit > 100 should be rejected."""
        r = self.client.get("/api/v1/memory/search?q=test&limit=101")
        assert r.status_code == 422

    def test_search_limit_min_bound(self):
        """Limit < 1 should be rejected."""
        r = self.client.get("/api/v1/memory/search?q=test&limit=0")
        assert r.status_code == 422

    # --- Cross-type search (no type filter) ---

    def test_search_cross_type_returns_multiple_types(self):
        """Without type filter, results can come from any memory type."""
        r = self.client.get(
            "/api/v1/memory/search?q=engineering&limit=100"
        )
        data = r.json()
        types_seen = {res["memory_type"] for res in data["results"]}
        assert len(types_seen) > 1  # Should find episodic + relational at minimum
