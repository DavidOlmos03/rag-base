"""
Application startup and shutdown event handlers.
"""

from fastapi import FastAPI

from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def on_startup(app: FastAPI) -> None:
    """Execute tasks on application startup.

    Args:
        app: FastAPI application instance
    """
    # Configure logging
    configure_logging()
    logger.info("application_startup", message="Starting RAG Base Service")

    # Initialize database connection pool
    # This will be handled by the database session dependency

    # Initialize Redis connection
    # This will be handled by the cache service

    # Initialize Qdrant client
    # This will be handled by the vector store service

    # Load embedding model (lazy loading on first use)
    logger.info("startup_complete", message="Application started successfully")


async def on_shutdown(app: FastAPI) -> None:
    """Execute tasks on application shutdown.

    Args:
        app: FastAPI application instance
    """
    logger.info("application_shutdown", message="Shutting down RAG Base Service")

    # Close database connections
    # Handled automatically by SQLAlchemy

    # Close Redis connections
    # Handled automatically by Redis client

    # Close Qdrant connections
    # Handled automatically by Qdrant client

    logger.info("shutdown_complete", message="Application shut down successfully")
