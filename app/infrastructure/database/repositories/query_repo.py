"""
Query history repository for database operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.database.models import Query

logger = get_logger(__name__)


class QueryRepository:
    """Repository for Query history database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, query: Query) -> Query:
        """Create a new query record.

        Args:
            query: Query model instance

        Returns:
            Created query
        """
        self.session.add(query)
        await self.session.flush()
        await self.session.refresh(query)

        logger.info(
            "query_saved",
            query_id=str(query.id),
            tenant_id=str(query.tenant_id),
            tokens_used=query.tokens_used,
        )
        return query

    async def get_by_id(self, query_id: UUID) -> Query | None:
        """Get query by ID.

        Args:
            query_id: Query ID

        Returns:
            Query or None if not found
        """
        result = await self.session.execute(select(Query).where(Query.id == query_id))
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Query]:
        """Get query history for a tenant.

        Args:
            tenant_id: Tenant ID
            limit: Maximum number of queries
            offset: Offset for pagination

        Returns:
            List of queries
        """
        result = await self.session.execute(
            select(Query)
            .where(Query.tenant_id == tenant_id)
            .order_by(Query.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count queries for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Query count
        """
        result = await self.session.execute(select(Query).where(Query.tenant_id == tenant_id))
        return len(list(result.scalars().all()))

    async def get_total_tokens_by_tenant(self, tenant_id: UUID) -> int:
        """Get total tokens used by a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Total tokens used
        """
        queries = await self.get_by_tenant(tenant_id, limit=10000)
        return sum(q.tokens_used for q in queries)
