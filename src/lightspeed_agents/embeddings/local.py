import os
from typing import Any

from lightspeed_agents.embeddings.base import EmbeddingProvider
from lightspeed_agents.embeddings.config import EmbeddingConfig, LocalModel


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    _MODEL_DIMENSIONS = {
        LocalModel.ALL_MINILM_L6_V2: 384,
        LocalModel.ALL_MPNET_BASE_V2: 768,
        LocalModel.E5_SMALL_V2: 384,
        LocalModel.E5_BASE_V2: 768,
        LocalModel.BGE_SMALL_EN_V1_5: 384,
        LocalModel.BGE_BASE_EN_V1_5: 768,
    }

    def __init__(self, config: EmbeddingConfig | None = None):
        self._config = config or EmbeddingConfig()
        self._model = self._config.local_model
        self._dimensions = self._MODEL_DIMENSIONS.get(self._model, 384)
        self._model_instance = self._load_model()
        self._normalize = self._config.normalize_embeddings

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            ) from e

        model_name = self._model.value if isinstance(self._model, LocalModel) else str(self._model)
        cache_dir = os.getenv("SENTENCE_TRANSFORMERS_HOME")

        return SentenceTransformer(model_name, cache_folder=cache_dir)

    @property
    def model_name(self) -> str:
        return self._model.value if isinstance(self._model, LocalModel) else str(self._model)

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
            embeddings = self._model_instance.encode(
                batch,
                batch_size=batch_size,
                normalize_embeddings=self._normalize,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            all_embeddings.extend(embeddings.tolist())

        return all_embeddings

    def get_config(self) -> dict[str, Any]:
        config = super().get_config()
        config.update(
            {
                "provider_type": "local",
                "model": self.model_name,
                "dimensions": self.dimensions,
                "batch_size": self._config.batch_size,
                "normalize_embeddings": self._normalize,
            }
        )
        return config