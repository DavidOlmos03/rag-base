"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, llm_config, query

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(llm_config.router, prefix="/llm", tags=["LLM Configuration"])


# Health check endpoint
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Base Service",
        "version": "0.1.0",
    }


@api_router.get("/status", tags=["Health"])
async def system_status():
    """Get system status and info."""
    return {
        "status": "operational",
        "version": "0.1.0",
        "components": {
            "api": "operational",
            "database": "operational",
            "vector_store": "operational",
            "cache": "operational",
        },
    }
