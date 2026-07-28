import pytest
from unittest.mock import patch, MagicMock

from lightspeed_agents.embeddings import (
    get_provider,
    list_providers,
    register_provider,
    EmbeddingProviderType,
    EmbeddingConfig,
    LocalEmbeddingConfig,
    OpenAIEmbeddingConfig,
    EmbeddingProvider,
)
from lightspeed_agents.embeddings.local import LocalEmbeddingProvider
from lightspeed_agents.embeddings.openai import OpenAIEmbeddingProvider
from lightspeed_agents.embeddings.registry import reset_providers


@pytest.fixture(autouse=True)
def reset_provider_registry():
    """Reset provider registry between tests to ensure isolation."""
    reset_providers()
    yield
    reset_providers()


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config=None):
        self._config = config
        self._model_name = "fake-model"
        self._dimensions = 128

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._dimensions for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * self._dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._dimensions for _ in texts]


def _make_mock_sentence_transformer():
    """Create a mock SentenceTransformer that returns fake embeddings."""
    mock_model = MagicMock()
    import numpy as np

    def fake_encode(texts, **kwargs):
        n = len(texts)
        return np.random.default_rng(42).random((n, 384), dtype=np.float32)

    mock_model.encode.side_effect = fake_encode
    return mock_model


@pytest.fixture(autouse=True)
def mock_sentence_transformer():
    """Mock SentenceTransformer to prevent model downloads in all tests."""
    mock_st = MagicMock()
    mock_st.return_value = _make_mock_sentence_transformer()
    with patch.dict("sys.modules", {"sentence_transformers": mock_st}):
        with patch(
            "lightspeed_agents.embeddings.local.LocalEmbeddingProvider._load_model",
            return_value=_make_mock_sentence_transformer(),
        ):
            yield


def test_register_and_get_provider():
    register_provider(EmbeddingProviderType.LOCAL, FakeEmbeddingProvider)
    provider = get_provider(EmbeddingProviderType.LOCAL)
    assert isinstance(provider, FakeEmbeddingProvider)


def test_get_provider_returns_new_instance():
    register_provider(EmbeddingProviderType.LOCAL, FakeEmbeddingProvider)
    p1 = get_provider(EmbeddingProviderType.LOCAL)
    p2 = get_provider(EmbeddingProviderType.LOCAL)
    assert p1 is not p2


def test_get_provider_unknown():
    with pytest.raises(ValueError):
        get_provider("nonexistent")


def test_list_providers():
    providers = list_providers()
    assert EmbeddingProviderType.OPENAI in providers
    assert EmbeddingProviderType.LOCAL in providers


def test_embedding_config_defaults():
    config = EmbeddingConfig()
    assert config.provider == EmbeddingProviderType.LOCAL
    assert config.batch_size == 32
    assert config.normalize_embeddings is True


def test_openai_embedding_config():
    config = OpenAIEmbeddingConfig(api_key="test-key", openai_model="text-embedding-3-large")
    assert config.provider == EmbeddingProviderType.OPENAI
    assert config.openai_model == "text-embedding-3-large"


def test_local_embedding_config():
    config = LocalEmbeddingConfig(local_model="all-mpnet-base-v2")
    assert config.provider == EmbeddingProviderType.LOCAL
    assert config.local_model == "all-mpnet-base-v2"


def test_local_embedding_provider():
    config = LocalEmbeddingConfig()
    provider = LocalEmbeddingProvider(config)
    assert provider.model_name == "all-MiniLM-L6-v2"
    assert provider.dimensions == 384


def test_openai_embedding_provider():
    config = OpenAIEmbeddingConfig(api_key="test-key")
    provider = OpenAIEmbeddingProvider(config)
    assert provider.model_name == "text-embedding-3-small"
    assert provider.dimensions == 1536


@patch("lightspeed_agents.embeddings.openai.OpenAI")
def test_openai_embed(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1, 0.2, 0.3]
    mock_data = [mock_embedding]
    mock_response = MagicMock()
    mock_response.data = mock_data
    mock_client.embeddings.create.return_value = mock_response

    config = OpenAIEmbeddingConfig(api_key="test-key")
    provider = OpenAIEmbeddingProvider(config)

    result = provider.embed(["test text"])

    assert len(result) == 1
    assert result[0] == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_called_once()


def test_embed_query():
    config = LocalEmbeddingConfig()
    provider = LocalEmbeddingProvider(config)
    embedding = provider.embed_query("test query")
    assert isinstance(embedding, list)
    assert len(embedding) == provider.dimensions


def test_embed_documents():
    config = LocalEmbeddingConfig()
    provider = LocalEmbeddingProvider(config)
    embeddings = provider.embed_documents(["doc 1", "doc 2", "doc 3"])
    assert len(embeddings) == 3
    assert all(len(e) == provider.dimensions for e in embeddings)


def test_embed_batch():
    config = LocalEmbeddingConfig()
    provider = LocalEmbeddingProvider(config)
    embeddings = provider.embed(["batch 1", "batch 2"])
    assert len(embeddings) == 2
    assert all(len(e) == provider.dimensions for e in embeddings)


def test_get_default_provider():
    config = LocalEmbeddingConfig()
    provider = get_provider(EmbeddingProviderType.LOCAL, config)
    assert isinstance(provider, LocalEmbeddingProvider)


def test_get_default_provider_with_openai():
    config = EmbeddingConfig(provider=EmbeddingProviderType.OPENAI, api_key="test-key")
    provider = get_provider(EmbeddingProviderType.OPENAI, config)
    assert isinstance(provider, OpenAIEmbeddingProvider)
