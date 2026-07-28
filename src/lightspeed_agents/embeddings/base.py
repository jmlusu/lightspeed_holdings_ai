from abc import ABC, abstractmethod
from typing import Any


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name used by this provider."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector (list of floats).
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of document texts.

        Args:
            texts: List of document texts to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        pass

    def get_config(self) -> dict[str, Any]:
        """Return provider configuration as a dictionary."""
        return {
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "provider_type": self.__class__.__name__,
        }