"""VectorStore interface for semantic search and retrieval."""

from lightspeed_agents.vectorstore.base import VectorStore
from lightspeed_agents.vectorstore.config import (
    ChromaConfig,
    FaissConfig,
    VectorStoreConfig,
    VectorStoreType,
)
from lightspeed_agents.vectorstore.models import (
    SearchResult,
    VectorRecord,
)
from lightspeed_agents.vectorstore.registry import (
    get_vectorstore,
    list_vectorstores,
    register_vectorstore,
    reset_vectorstores,
)

__all__ = [
    "VectorStore",
    "VectorStoreType",
    "VectorStoreConfig",
    "FaissConfig",
    "ChromaConfig",
    "VectorRecord",
    "SearchResult",
    "get_vectorstore",
    "register_vectorstore",
    "list_vectorstores",
    "reset_vectorstores",
]
