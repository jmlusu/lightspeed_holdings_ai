"""Abstract base class for vector store providers."""

from abc import ABC, abstractmethod
from typing import Optional

from lightspeed_agents.vectorstore.models import SearchResult, VectorRecord


class VectorStore(ABC):
    """Abstract base class for all vector store implementations.

    All vector store providers must implement this interface to be
    compatible with the Light Speed Agents memory and retrieval systems.
    """

    @abstractmethod
    def add(
        self,
        embeddings: list[list[float]],
        metadata: list[dict],
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add vectors to the store.

        Args:
            embeddings: List of embedding vectors.
            metadata: List of metadata dicts (one per embedding).
            ids: Optional list of IDs. Auto-generated if not provided.

        Returns:
            List of IDs for the added records.
        """
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector.
            k: Number of results to return.
            filter: Optional metadata filter dict.

        Returns:
            List of SearchResult objects sorted by score descending.
        """
        ...

    @abstractmethod
    def delete(self, ids: list[str]) -> int:
        """Delete vectors by IDs.

        Args:
            ids: List of IDs to delete.

        Returns:
            Count of deleted records.
        """
        ...

    @abstractmethod
    def get(self, ids: list[str]) -> list[VectorRecord]:
        """Get vectors by IDs.

        Args:
            ids: List of IDs to retrieve.

        Returns:
            List of VectorRecord objects.
        """
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of vectors in the store."""
        ...

    @abstractmethod
    def persist(self) -> None:
        """Persist the index to disk."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Load the index from disk."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of vectors in this store."""
        ...

    @property
    @abstractmethod
    def index_type(self) -> str:
        """Return the index type string (e.g. 'flat', 'ivf', 'hnsw')."""
        ...
