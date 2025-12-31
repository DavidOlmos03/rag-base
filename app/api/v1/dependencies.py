"""
Dependency injection for API endpoints.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.llm_config_repo import LLMConfigRepository
from app.infrastructure.database.repositories.query_repo import QueryRepository
from app.infrastructure.database.repositories.tenant_repo import TenantRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Tenant
from typing import Annotated


# Database session dependency
async def get_session() -> AsyncSession:
    """Get database session.

    Yields:
        Database session
    """
    async for session in get_db():
        yield session


# Current user dependency
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get current authenticated user.

    Args:
        request: FastAPI request with auth info
        session: Database session

    Returns:
        Current tenant/user

    Raises:
        HTTPException: If user not found or not authenticated
    """
    # Get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Fetch user from database
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(UUID(user_id))

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return tenant


# Repository dependencies
def get_tenant_repository(
    session: AsyncSession = Depends(get_session),
) -> TenantRepository:
    """Get tenant repository.

    Args:
        session: Database session

    Returns:
        TenantRepository instance
    """
    return TenantRepository(session)


def get_document_repository(
    session: AsyncSession = Depends(get_session),
) -> DocumentRepository:
    """Get document repository.

    Args:
        session: Database session

    Returns:
        DocumentRepository instance
    """
    return DocumentRepository(session)


def get_llm_config_repository(
    session: AsyncSession = Depends(get_session),
) -> LLMConfigRepository:
    """Get LLM config repository.

    Args:
        session: Database session

    Returns:
        LLMConfigRepository instance
    """
    return LLMConfigRepository(session)


def get_query_repository(
    session: AsyncSession = Depends(get_session),
) -> QueryRepository:
    """Get query repository.

    Args:
        session: Database session

    Returns:
        QueryRepository instance
    """
    return QueryRepository(session)


# Cache dependency
async def get_cache_service():
    """Get cache service.

    Returns:
        CacheService instance
    """
    from app.infrastructure.cache.cache_service import CacheService

    redis = await get_redis()
    return CacheService(redis)


# Vector store dependency
async def get_vector_store_service():
    """Get vector store service.

    Returns:
        VectorStore instance
    """
    from app.infrastructure.vectorstore.qdrant_client import get_vector_store

    return await get_vector_store()


# Embedding provider dependency
def get_embedding_provider_service():
    """Get embedding provider service.

    Returns:
        EmbeddingProvider instance
    """
    from app.rag.embeddings.sentence_transformers_provider import get_embedding_provider

    return get_embedding_provider()
