"""Tests for VectorStore interface using in-memory mock implementation."""

import math
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from lightspeed_agents.vectorstore import (
    ChromaConfig,
    FaissConfig,
    SearchResult,
    VectorRecord,
    VectorStore,
    VectorStoreConfig,
    VectorStoreType,
    get_vectorstore,
    list_vectorstores,
    register_vectorstore,
    reset_vectorstores,
)
from lightspeed_agents.vectorstore.base import VectorStore as VectorStoreABC


# ============================================================
# In-Memory Mock VectorStore for Testing
# ============================================================


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for testing the interface."""

    def __init__(self, config: VectorStoreConfig | None = None):
        self._config = config or VectorStoreConfig()
        self._records: dict[str, VectorRecord] = {}
        self._dimensions: int = 0
        self._persist_dir: str | None = self._config.persist_dir

    def add(
        self,
        embeddings: list[list[float]],
        metadata: list[dict],
        ids: list[str] | None = None,
    ) -> list[str]:
        from uuid import uuid4

        if ids is None:
            ids = [uuid4().hex[:12] for _ in embeddings]

        if len(embeddings) != len(metadata) or len(embeddings) != len(ids):
            raise ValueError("embeddings, metadata, and ids must have the same length")

        for emb, meta, id_ in zip(embeddings, metadata, ids):
            record = VectorRecord(id=id_, embedding=emb, metadata=meta)
            self._records[id_] = record
            if self._dimensions == 0 and emb:
                self._dimensions = len(emb)

        return ids

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        results = []
        for record in self._records.values():
            if filter:
                if not all(record.metadata.get(key) == val for key, val in filter.items()):
                    continue
            score = self._cosine_similarity(query_embedding, record.embedding)
            results.append((record, score))

        results.sort(key=lambda x: x[1], reverse=True)

        return [
            SearchResult(record=r, score=s, rank=i + 1)
            for i, (r, s) in enumerate(results[:k])
        ]

    def delete(self, ids: list[str]) -> int:
        count = 0
        for id_ in ids:
            if id_ in self._records:
                del self._records[id_]
                count += 1
        return count

    def get(self, ids: list[str]) -> list[VectorRecord]:
        return [self._records[id_] for id_ in ids if id_ in self._records]

    def count(self) -> int:
        return len(self._records)

    def persist(self) -> None:
        pass  # No-op for in-memory

    def load(self) -> None:
        pass  # No-op for in-memory

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def index_type(self) -> str:
        return "in-memory"

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ============================================================
# VectorRecord Tests
# ============================================================


class TestVectorRecord:
    """Tests for VectorRecord model."""

    def test_create_record(self):
        record = VectorRecord(
            embedding=[0.1, 0.2, 0.3],
            metadata={"source": "test"},
        )
        assert record.id is not None
        assert len(record.id) == 12
        assert record.embedding == [0.1, 0.2, 0.3]
        assert record.metadata == {"source": "test"}
        assert record.created_at is not None

    def test_create_record_with_id(self):
        record = VectorRecord(
            id="custom-id",
            embedding=[0.1, 0.2],
            metadata={},
        )
        assert record.id == "custom-id"

    def test_record_defaults(self):
        record = VectorRecord(embedding=[1.0])
        assert record.id is not None
        assert record.metadata == {}
        assert record.created_at is not None

    def test_record_json_roundtrip(self):
        record = VectorRecord(
            id="test-123",
            embedding=[0.1, 0.2, 0.3],
            metadata={"key": "value"},
        )
        json_str = record.model_dump_json()
        restored = VectorRecord.model_validate_json(json_str)
        assert restored.id == record.id
        assert restored.embedding == record.embedding
        assert restored.metadata == record.metadata


# ============================================================
# SearchResult Tests
# ============================================================


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_create_result(self):
        record = VectorRecord(embedding=[1.0], metadata={})
        result = SearchResult(record=record, score=0.95, rank=1)
        assert result.record == record
        assert result.score == 0.95
        assert result.rank == 1

    def test_result_sorting(self):
        records = [VectorRecord(embedding=[float(i)], metadata={}) for i in range(3)]
        results = [
            SearchResult(record=r, score=s, rank=0)
            for r, s in zip(records, [0.5, 0.9, 0.3])
        ]
        results.sort(key=lambda x: x.score, reverse=True)
        assert results[0].score == 0.9
        assert results[1].score == 0.5
        assert results[2].score == 0.3


# ============================================================
# VectorStoreConfig Tests
# ============================================================


class TestVectorStoreConfig:
    """Tests for VectorStoreConfig."""

    def test_default_config(self):
        config = VectorStoreConfig()
        assert config.persist_dir is None
        assert config.index_type == "flat"

    def test_faiss_config(self):
        config = FaissConfig(persist_dir="/tmp/faiss")
        assert config.store_type == "faiss"
        assert config.persist_dir == "/tmp/faiss"
        assert config.index_type == "flat"

    def test_faiss_ivf_config(self):
        config = FaissConfig(index_type="ivf", nlist=100)
        assert config.index_type == "ivf"
        assert config.nlist == 100

    def test_chroma_config(self):
        config = ChromaConfig(persist_dir="/tmp/chroma", collection_name="docs")
        assert config.store_type == "chroma"
        assert config.persist_dir == "/tmp/chroma"
        assert config.collection_name == "docs"
        assert config.distance_fn == "cosine"

    def test_config_json_roundtrip(self):
        config = FaissConfig(persist_dir="/tmp/test", index_type="ivf", nlist=50)
        json_str = config.model_dump_json()
        restored = VectorStoreConfig.model_validate_json(json_str)
        assert restored.persist_dir == "/tmp/test"


# ============================================================
# VectorStore Interface Tests (using InMemoryVectorStore)
# ============================================================


class TestVectorStoreInterface:
    """Tests for the VectorStore abstract interface."""

    @pytest.fixture
    def store(self):
        """Create an in-memory vector store for testing."""
        return InMemoryVectorStore(VectorStoreConfig())

    @pytest.fixture
    def populated_store(self, store):
        """Create a store with test data."""
        ids = store.add(
            embeddings=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.707, 0.707, 0.0],
            ],
            metadata=[
                {"label": "vector-a", "category": "test"},
                {"label": "vector-b", "category": "test"},
                {"label": "vector-c", "category": "other"},
                {"label": "vector-d", "category": "test"},
            ],
            ids=["v1", "v2", "v3", "v4"],
        )
        return store

    def test_add_vectors(self, store):
        """Test adding vectors."""
        ids = store.add(
            embeddings=[[1.0, 2.0], [3.0, 4.0]],
            metadata=[{"a": 1}, {"a": 2}],
        )
        assert len(ids) == 2
        assert store.count() == 2

    def test_add_with_custom_ids(self, store):
        """Test adding vectors with custom IDs."""
        ids = store.add(
            embeddings=[[1.0, 2.0]],
            metadata=[{}],
            ids=["custom-id"],
        )
        assert ids == ["custom-id"]
        records = store.get(["custom-id"])
        assert len(records) == 1

    def test_add_auto_generates_ids(self, store):
        """Test that IDs are auto-generated when not provided."""
        ids = store.add(
            embeddings=[[1.0, 2.0], [3.0, 4.0]],
            metadata=[{}, {}],
        )
        assert len(ids) == 2
        assert all(isinstance(id_, str) for id_ in ids)
        assert ids[0] != ids[1]

    def test_add_mismatched_lengths_raises(self, store):
        """Test that mismatched input lengths raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            store.add(
                embeddings=[[1.0], [2.0]],
                metadata=[{}],
            )

    def test_search_basic(self, populated_store):
        """Test basic search returns results sorted by score."""
        results = populated_store.search(
            query_embedding=[1.0, 0.0, 0.0],
            k=3,
        )
        assert len(results) == 3
        assert results[0].rank == 1
        # v1 is exact match
        assert results[0].record.id == "v1"
        assert results[0].score == pytest.approx(1.0, abs=1e-5)

    def test_search_returns_all_if_k_exceeds_count(self, populated_store):
        """Test search returns all results when k > count."""
        results = populated_store.search([1.0, 0.0, 0.0], k=100)
        assert len(results) == 4

    def test_search_with_filter(self, populated_store):
        """Test search with metadata filter."""
        results = populated_store.search(
            query_embedding=[1.0, 0.0, 0.0],
            k=10,
            filter={"category": "other"},
        )
        assert len(results) == 1
        assert results[0].record.metadata["category"] == "other"

    def test_search_with_filter_no_match(self, populated_store):
        """Test search with filter that matches nothing."""
        results = populated_store.search(
            query_embedding=[1.0, 0.0, 0.0],
            k=10,
            filter={"category": "nonexistent"},
        )
        assert len(results) == 0

    def test_delete(self, populated_store):
        """Test deleting vectors by ID."""
        count = populated_store.delete(["v1", "v2"])
        assert count == 2
        assert populated_store.count() == 2

    def test_delete_nonexistent(self, populated_store):
        """Test deleting nonexistent IDs returns 0."""
        count = populated_store.delete(["nonexistent"])
        assert count == 0
        assert populated_store.count() == 4

    def test_get(self, populated_store):
        """Test getting vectors by ID."""
        records = populated_store.get(["v1", "v3"])
        assert len(records) == 2
        assert records[0].id == "v1"
        assert records[1].id == "v3"

    def test_get_nonexistent(self, populated_store):
        """Test getting nonexistent IDs returns empty."""
        records = populated_store.get(["nonexistent"])
        assert len(records) == 0

    def test_get_mixed(self, populated_store):
        """Test getting mix of existing and nonexistent IDs."""
        records = populated_store.get(["v1", "nonexistent"])
        assert len(records) == 1
        assert records[0].id == "v1"

    def test_count(self, store):
        """Test count on empty and populated store."""
        assert store.count() == 0
        store.add(embeddings=[[1.0]], metadata=[{}])
        assert store.count() == 1
        store.add(embeddings=[[2.0], [3.0]], metadata=[{}, {}])
        assert store.count() == 3

    def test_persist_load(self, store):
        """Test persist/load are callable without error."""
        store.add(embeddings=[[1.0, 2.0]], metadata=[{}])
        store.persist()
        store.load()

    def test_dimensions(self, store):
        """Test dimensions property."""
        assert store.dimensions == 0
        store.add(embeddings=[[1.0, 2.0, 3.0]], metadata=[{}])
        assert store.dimensions == 3

    def test_index_type(self, store):
        """Test index_type property."""
        assert store.index_type == "in-memory"

    def test_cosine_similarity(self):
        """Test internal cosine similarity calculation."""
        sim = InMemoryVectorStore._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert sim == pytest.approx(1.0)

        sim = InMemoryVectorStore._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert sim == pytest.approx(0.0)

        sim = InMemoryVectorStore._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert sim == pytest.approx(-1.0)

    def test_zero_vector_similarity(self):
        """Test similarity with zero vector returns 0."""
        sim = InMemoryVectorStore._cosine_similarity([0.0, 0.0], [1.0, 1.0])
        assert sim == 0.0

    def test_interface_completeness(self, store):
        """Test all required interface methods/properties exist."""
        # Methods
        assert hasattr(store, "add")
        assert callable(store.add)
        assert hasattr(store, "search")
        assert callable(store.search)
        assert hasattr(store, "delete")
        assert callable(store.delete)
        assert hasattr(store, "get")
        assert callable(store.get)
        assert hasattr(store, "count")
        assert callable(store.count)
        assert hasattr(store, "persist")
        assert callable(store.persist)
        assert hasattr(store, "load")
        assert callable(store.load)

        # Properties
        assert hasattr(type(store), "dimensions")
        assert hasattr(type(store), "index_type")


# ============================================================
# Registry Tests
# ============================================================


class TestVectorStoreRegistry:
    """Tests for vector store provider registry."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Reset registry between tests."""
        reset_vectorstores()
        yield
        reset_vectorstores()

    def test_register_and_get(self):
        """Test registering and retrieving a vector store."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        store = get_vectorstore(VectorStoreType.FAISS)
        assert isinstance(store, InMemoryVectorStore)

    def test_get_with_string(self):
        """Test getting store by string type."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        store = get_vectorstore("faiss")
        assert isinstance(store, InMemoryVectorStore)

    def test_get_default_faiss(self):
        """Test default store type is FAISS (when registered)."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        store = get_vectorstore()
        assert isinstance(store, InMemoryVectorStore)

    def test_get_unknown_raises(self):
        """Test getting unknown store type raises ValueError."""
        with pytest.raises(ValueError):
            get_vectorstore("nonexistent")

    def test_get_unregistered_type_raises(self):
        """Test getting unregistered type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown vector store type"):
            get_vectorstore(VectorStoreType.CHROMA)

    def test_list_vectorstores(self):
        """Test listing registered store types."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        register_vectorstore(VectorStoreType.CHROMA, InMemoryVectorStore)
        stores = list_vectorstores()
        assert VectorStoreType.FAISS in stores
        assert VectorStoreType.CHROMA in stores

    def test_register_replaces_existing(self):
        """Test re-registering replaces existing store class."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        store = get_vectorstore(VectorStoreType.FAISS)
        assert isinstance(store, InMemoryVectorStore)

    def test_reset_clears_registry(self):
        """Test reset clears all registrations."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        assert len(list_vectorstores()) == 1
        reset_vectorstores()
        assert len(list_vectorstores()) == 0

    def test_get_returns_new_instance(self):
        """Test each call returns a new instance."""
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        s1 = get_vectorstore(VectorStoreType.FAISS)
        s2 = get_vectorstore(VectorStoreType.FAISS)
        assert s1 is not s2

    def test_register_custom_subclass(self):
        """Test registering a custom VectorStore subclass."""
        class CustomStore(InMemoryVectorStore):
            @property
            def index_type(self) -> str:
                return "custom"

        register_vectorstore(VectorStoreType.FAISS, CustomStore)
        store = get_vectorstore(VectorStoreType.FAISS)
        assert store.index_type == "custom"


# ============================================================
# Integration-style Tests
# ============================================================


class TestVectorStoreIntegration:
    """Higher-level integration tests for the VectorStore interface."""

    @pytest.fixture
    def store(self):
        register_vectorstore(VectorStoreType.FAISS, InMemoryVectorStore)
        yield get_vectorstore(VectorStoreType.FAISS)
        reset_vectorstores()

    def test_full_lifecycle(self, store):
        """Test a complete add-search-delete lifecycle."""
        # Add
        ids = store.add(
            embeddings=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            metadata=[
                {"content": "alpha", "source": "doc-a"},
                {"content": "beta", "source": "doc-b"},
                {"content": "gamma", "source": "doc-c"},
            ],
        )
        assert store.count() == 3

        # Search
        results = store.search([1.0, 0.0, 0.0], k=2)
        assert len(results) == 2
        assert results[0].record.id == ids[0]

        # Get
        records = store.get([ids[0]])
        assert records[0].metadata["content"] == "alpha"

        # Delete
        deleted = store.delete([ids[2]])
        assert deleted == 1
        assert store.count() == 2

        # Verify deletion
        remaining = store.get([ids[2]])
        assert len(remaining) == 0

    def test_add_then_search_similar(self, store):
        """Test that similar vectors rank higher."""
        store.add(
            embeddings=[
                [1.0, 0.0, 0.0],
                [0.9, 0.44, 0.0],
                [0.0, 0.0, 1.0],
            ],
            metadata=[
                {"label": "exact-match"},
                {"label": "close-match"},
                {"label": "no-match"},
            ],
            ids=["exact", "close", "none"],
        )

        results = store.search([1.0, 0.0, 0.0], k=3)
        assert results[0].record.id == "exact"
        assert results[1].record.id == "close"
        assert results[2].record.id == "none"
        assert results[0].score > results[1].score > results[2].score

    def test_empty_store_operations(self, store):
        """Test operations on empty store."""
        assert store.count() == 0
        assert store.search([1.0], k=5) == []
        assert store.get(["nonexistent"]) == []
        assert store.delete(["nonexistent"]) == 0

    def test_large_batch_add(self, store):
        """Test adding a large batch of vectors."""
        n = 500
        embeddings = [[float(i), float(i + 1)] for i in range(n)]
        metadata = [{"index": i} for i in range(n)]
        ids = store.add(embeddings, metadata)
        assert store.count() == n
        assert len(ids) == n
