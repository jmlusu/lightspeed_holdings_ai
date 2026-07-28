import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from lightspeed_agents.services.config import settings
from lightspeed_agents.services.dependencies import reset_dependencies
from lightspeed_agents.services.exceptions import configure_exception_handlers
from lightspeed_agents.services.middleware import configure_cors, configure_middleware
from lightspeed_agents.services.routers import (
    agents_router,
    health_router,
    memory_router,
    tasks_router,
    workflows_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle events."""
    logger.info("Starting Light Speed Agents API v%s", app.version)
    yield
    logger.info("Shutting down Light Speed Agents API")
    reset_dependencies()


def create_app() -> FastAPI:
    """Create and configure a FastAPI application instance."""
    app = FastAPI(
        title="Light Speed Agents API",
        description="AI agent orchestration framework API",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    configure_cors(app)
    configure_middleware(app)
    configure_exception_handlers(app)

    app.include_router(health_router, prefix=settings.API_V1_PREFIX)
    app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
    app.include_router(memory_router, prefix=settings.API_V1_PREFIX)
    app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
    app.include_router(workflows_router, prefix=settings.API_V1_PREFIX)

    return app
