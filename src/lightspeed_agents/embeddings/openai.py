import os
from typing import Any

from openai import OpenAI

from lightspeed_agents.embeddings.base import EmbeddingProvider
from lightspeed_agents.embeddings.config import EmbeddingConfig, OpenAIModel


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider supporting text-embedding-3-small, text-embedding-3-large, and text-embedding-ada-002."""

    _MODEL_DIMENSIONS = {
        OpenAIModel.TEXT_EMBEDDING_3_SMALL: 1536,
        OpenAIModel.TEXT_EMBEDDING_3_LARGE: 3072,
        OpenAIModel.TEXT_EMBEDDING_ADA_002: 1536,
    }

    def __init__(self, config: EmbeddingConfig | None = None):
        self._config = config or EmbeddingConfig()
        self._client = self._create_client()
        self._model = self._config.openai_model
        self._dimensions = self._config.dimensions or self._MODEL_DIMENSIONS.get(self._model, 1536)

    def _create_client(self) -> OpenAI:
        api_key = self._config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or provide in config.")

        return OpenAI(
            api_key=api_key,
            base_url=self._config.base_url,
        )

    @property
    def model_name(self) -> str:
        return self._model.value if isinstance(self._model, OpenAIModel) else str(self._model)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        return self._embed_batch(texts)

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text."""
        return self.embed([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of document texts."""
        return self.embed(texts)

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        batch_size = self._config.batch_size
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._call_api(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        params = {
            "model": self.model_name,
            "input": texts,
        }

        if self._dimensions and self._model in (OpenAIModel.TEXT_EMBEDDING_3_SMALL, OpenAIModel.TEXT_EMBEDDING_3_LARGE):
            params["dimensions"] = self._dimensions

        response = self._client.embeddings.create(**params)
        return [data.embedding for data in response.data]

    def get_config(self) -> dict[str, Any]:
        config = super().get_config()
        config.update(
            {
                "provider_type": "openai",
                "model": self.model_name,
                "dimensions": self.dimensions,
                "batch_size": self._config.batch_size,
            }
        )
        return config