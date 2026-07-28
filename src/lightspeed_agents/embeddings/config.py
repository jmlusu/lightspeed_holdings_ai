from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class EmbeddingProviderType(str, Enum):
    OPENAI = "openai"
    LOCAL = "local"


class OpenAIModel(str, Enum):
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class LocalModel(str, Enum):
    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"
    E5_SMALL_V2 = "intfloat/e5-small-v2"
    E5_BASE_V2 = "intfloat/e5-base-v2"
    BGE_SMALL_EN_V1_5 = "BAAI/bge-small-en-v1.5"
    BGE_BASE_EN_V1_5 = "BAAI/bge-base-en-v1.5"


class EmbeddingConfig(BaseModel):
    provider: EmbeddingProviderType = EmbeddingProviderType.LOCAL
    openai_model: OpenAIModel = OpenAIModel.TEXT_EMBEDDING_3_SMALL
    local_model: LocalModel = LocalModel.ALL_MINILM_L6_V2
    api_key: str | None = None
    base_url: str | None = None
    dimensions: int | None = None
    batch_size: int = 32
    normalize_embeddings: bool = True

    model_config = ConfigDict(use_enum_values=True)


class EmbeddingProviderConfig(BaseModel):
    type: EmbeddingProviderType
    config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    model_config = ConfigDict(use_enum_values=True)


class OpenAIEmbeddingConfig(EmbeddingConfig):
    provider: EmbeddingProviderType = EmbeddingProviderType.OPENAI
    openai_model: OpenAIModel = OpenAIModel.TEXT_EMBEDDING_3_SMALL


class LocalEmbeddingConfig(EmbeddingConfig):
    provider: EmbeddingProviderType = EmbeddingProviderType.LOCAL
    local_model: LocalModel = LocalModel.ALL_MINILM_L6_V2