import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eyos.commands.cli import cli_app
from eyos.config import get_settings
from eyos.exceptions import exception_handlers
from eyos.routers import hail_mock, newstore
from eyos.services.hail_client import HailClient
from eyos.services.queue_processor import InMemoryQueue, QueueProcessor
from eyos.utils.helpers import set_log_level

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle manager.

    This context manager handles startup and shutdown events.
    """
    # Initialize services on startup
    settings = get_settings()
    hail_client = HailClient(settings)

    # Create queue and queue processor
    queue = InMemoryQueue()
    queue_processor = QueueProcessor(queue, settings)

    # Start the queue processor if enabled
    if settings.queue_enabled:
        logger.info("Starting queue processor...")
        async with queue_processor.lifespan():
            logger.info("Queue processor started")
            yield
            logger.info("Shutting down queue processor...")
        logger.info("Queue processor stopped")
    else:
        logger.info("Queue processor disabled")
        yield


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    # Set log level from settings
    set_log_level(settings.log_level)

    # Initialize FastAPI application
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    exception_handlers(app)

    # Include routers
    app.include_router(newstore.router)

    # Include mock routers only in development mode
    if settings.hail_api_base_url == "mock":
        app.include_router(hail_mock.router)

    @app.get(
        "/",
        summary="Status",
        responses={200: {"content": {"application/json": {"example": {"status": "OK"}}}}},
    )
    async def index() -> Dict[str, Any]:
        """
        Show application status and version information.
        """
        return {
            "status": "OK",
            "git_hash": "unknown",
            "image_build_date": "unknown",
            "version": settings.api_version
        }

    return app


# Create the default application instance
app = create_app()

if __name__ == "__main__":
    cli_app()
