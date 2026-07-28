from lightspeed_agents.embeddings.base import EmbeddingProvider
from lightspeed_agents.embeddings.config import EmbeddingConfig, EmbeddingProviderType
from lightspeed_agents.embeddings.local import LocalEmbeddingProvider
from lightspeed_agents.embeddings.openai import OpenAIEmbeddingProvider

_PROVIDERS: dict[EmbeddingProviderType, type[EmbeddingProvider]] = {
    EmbeddingProviderType.OPENAI: OpenAIEmbeddingProvider,
    EmbeddingProviderType.LOCAL: LocalEmbeddingProvider,
}


def get_provider(
    provider_type: EmbeddingProviderType | str,
    config: EmbeddingConfig | None = None,
) -> EmbeddingProvider:
    """Get an embedding provider instance by type.

    Args:
        provider_type: Type of embedding provider (openai or local).
        config: Optional configuration for the provider.

    Returns:
        EmbeddingProvider instance.

    Raises:
        ValueError: If provider type is unknown.
    """
    if isinstance(provider_type, str):
        provider_type = EmbeddingProviderType(provider_type)

    if provider_type not in _PROVIDERS:
        raise ValueError(
            f"Unknown embedding provider: {provider_type}. "
            f"Available: {list(_PROVIDERS.keys())}"
        )

    provider_class = _PROVIDERS[provider_type]
    return provider_class(config)


def register_provider(provider_type: EmbeddingProviderType, provider_class: type[EmbeddingProvider]) -> None:
    """Register a custom embedding provider.

    Args:
        provider_type: Type identifier for the provider.
        provider_class: Provider class implementing EmbeddingProvider.
    """
    _PROVIDERS[provider_type] = provider_class


def list_providers() -> list[EmbeddingProviderType]:
    """List available embedding provider types."""
    return list(_PROVIDERS.keys())


def get_default_provider(config: EmbeddingConfig | None = None) -> EmbeddingProvider:
    """Get the default embedding provider based on configuration.

    Args:
        config: Configuration containing provider type.

    Returns:
        Default EmbeddingProvider instance.
    """
    provider_type = config.provider if config else EmbeddingProviderType.LOCAL
    return get_provider(provider_type, config)


def reset_providers() -> None:
    """Reset the provider registry to default providers.
    
    This is useful for testing to ensure clean state between tests.
    """
    from lightspeed_agents.embeddings.local import LocalEmbeddingProvider
    from lightspeed_agents.embeddings.openai import OpenAIEmbeddingProvider
    global _PROVIDERS
    _PROVIDERS = {
        EmbeddingProviderType.OPENAI: OpenAIEmbeddingProvider,
        EmbeddingProviderType.LOCAL: LocalEmbeddingProvider,
    }