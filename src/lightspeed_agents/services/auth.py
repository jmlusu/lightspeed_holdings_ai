"""API key authentication for protected endpoints.

Provides FastAPI dependencies for verifying API keys via the X-API-Key header.
Write endpoints (POST, PATCH, DELETE) require a valid API key when
``AUTH_REQUIRED`` is ``True``; read endpoints (GET) remain public.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from lightspeed_agents.services.config import APISettings, settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_settings() -> APISettings:
    """Return the current application settings singleton."""
    return settings


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
    app_settings: APISettings = Depends(_get_settings),  # noqa: B008
) -> str:
    """Verify the ``X-API-Key`` header against configured keys.

    Returns:
        The validated API key string, or ``"anonymous"`` when auth is disabled.

    Raises:
        HTTPException: 401 if the key is missing or not in the configured list.
    """
    if not app_settings.AUTH_REQUIRED:
        return "anonymous"

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if api_key not in app_settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key
