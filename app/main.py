"""
FastAPI application entry point for RAG Base Service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.events import on_shutdown, on_startup
from app.core.exceptions import RAGBaseException
from app.core.logging import configure_logging, get_logger

# Configure logging at module level
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application instance
    """
    # Startup
    await on_startup(app)
    yield
    # Shutdown
    await on_shutdown(app)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="RAG as a Service - Multi-tenant, multi-LLM base platform",
    version="0.1.0",
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Global exception handler
@app.exception_handler(RAGBaseException)
async def rag_exception_handler(request, exc: RAGBaseException):
    """Handle RAG base exceptions.

    Args:
        request: Request object
        exc: Exception instance

    Returns:
        JSON error response
    """
    logger.error(
        "rag_exception",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )

    # Map exception types to status codes
    status_code_map = {
        "AuthenticationError": 401,
        "AuthorizationError": 403,
        "ResourceNotFoundError": 404,
        "ResourceAlreadyExistsError": 409,
        "ValidationError": 422,
        "RateLimitExceededError": 429,
        "FileTooLargeError": 413,
        "UnsupportedFileFormatError": 415,
    }

    status_code = status_code_map.get(exc.__class__.__name__, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


# Include API router
app.include_router(
    api_router,
    prefix=f"/api/{settings.API_VERSION}",
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": f"/api/{settings.API_VERSION}/docs",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
