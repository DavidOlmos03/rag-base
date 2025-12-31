"""
FastAPI application entry point for RAG Base Service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware.auth import AuthMiddleware
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
    swagger_ui_parameters={
        "persistAuthorization": True,  # Remember authorization between page refreshes
    },
)

# Configure OpenAPI security scheme for Bearer token
def custom_openapi():
    """Customize OpenAPI schema to include security definitions."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="0.1.0",
        description="RAG as a Service - Multi-tenant, multi-LLM base platform",
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from /api/v1/auth/login",
        }
    }

    # Apply security to all endpoints except public ones
    public_paths = [
        "/",
        f"/api/{settings.API_VERSION}/health",
        f"/api/{settings.API_VERSION}/status",
        f"/api/{settings.API_VERSION}/docs",
        f"/api/{settings.API_VERSION}/redoc",
        f"/api/{settings.API_VERSION}/openapi.json",
        f"/api/{settings.API_VERSION}/auth/register",
        f"/api/{settings.API_VERSION}/auth/login",
    ]

    # HTTP methods to apply security to
    http_methods = ["get", "post", "put", "delete", "patch", "options", "head"]

    for path, path_item in openapi_schema["paths"].items():
        # Check if this path requires authentication
        is_public = any(path == pub or path.startswith(pub + "/") for pub in public_paths)

        if not is_public:
            # Apply security to each HTTP method in this path
            for method in http_methods:
                if method in path_item:
                    path_item[method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Authentication middleware
app.add_middleware(AuthMiddleware)


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
