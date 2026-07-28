"""Provider registry for vector store backends."""

from lightspeed_agents.vectorstore.base import VectorStore
from lightspeed_agents.vectorstore.config import VectorStoreConfig, VectorStoreType

_STORES: dict[VectorStoreType, type[VectorStore]] = {}


def get_vectorstore(
    store_type: VectorStoreType | str | None = None,
    config: VectorStoreConfig | None = None,
) -> VectorStore:
    """Get a vector store instance by type.

    Args:
        store_type: Type of vector store backend. Defaults to FAISS.
        config: Optional configuration for the store.

    Returns:
        VectorStore instance.

    Raises:
        ValueError: If store type is unknown or not registered.
    """
    if store_type is None:
        store_type = VectorStoreType.FAISS

    if isinstance(store_type, str):
        store_type = VectorStoreType(store_type)

    if store_type not in _STORES:
        raise ValueError(
            f"Unknown vector store type: {store_type}. "
            f"Available: {list(_STORES.keys())}"
        )

    store_class = _STORES[store_type]
    return store_class(config)


def register_vectorstore(
    store_type: VectorStoreType,
    store_class: type[VectorStore],
) -> None:
    """Register a vector store provider class.

    Args:
        store_type: Type identifier for the store.
        store_class: Class implementing VectorStore.
    """
    _STORES[store_type] = store_class


def list_vectorstores() -> list[VectorStoreType]:
    """List registered vector store types."""
    return list(_STORES.keys())


def reset_vectorstores() -> None:
    """Reset the store registry to empty state.

    Useful for testing to ensure clean state between tests.
    """
    global _STORES
    _STORES = {}
