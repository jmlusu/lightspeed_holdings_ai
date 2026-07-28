"""Configuration for vector store providers."""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class VectorStoreType(str, Enum):
    """Supported vector store backend types."""

    FAISS = "faiss"
    CHROMA = "chroma"


class VectorStoreConfig(BaseModel):
    """Base vector store configuration."""

    store_type: VectorStoreType = VectorStoreType.FAISS
    persist_dir: str | None = None
    index_type: str = "flat"
    dimensions: int | None = None

    model_config = ConfigDict(use_enum_values=True)


class FaissConfig(VectorStoreConfig):
    """FAISS-specific configuration."""

    store_type: VectorStoreType = VectorStoreType.FAISS
    index_type: str = "flat"  # flat, ivf, hnsw
    nlist: int | None = None  # Number of centroids for IVF
    ef_search: int | None = None  # HNSW search parameter
    ef_construction: int | None = None  # HNSW build parameter
    use_gpu: bool = False


class ChromaConfig(VectorStoreConfig):
    """ChromaDB-specific configuration."""

    store_type: VectorStoreType = VectorStoreType.CHROMA
    collection_name: str = "default"
    distance_fn: str = "cosine"  # cosine, l2, ip
    anonymized_telemetry: bool = False
