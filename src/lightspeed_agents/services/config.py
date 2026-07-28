from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API-specific configuration settings."""

    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")
    API_KEY: str = Field(default="", description="API key for authentication")
    API_KEYS: list[str] = Field(
        default=[], description="List of valid API keys for authentication"
    )
    AUTH_REQUIRED: bool = Field(
        default=True,
        description="Whether authentication is required for write endpoints",
    )
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")

    model_config = {"env_prefix": "", "case_sensitive": True}


settings = APISettings()
