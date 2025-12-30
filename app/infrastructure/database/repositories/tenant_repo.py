"""
Tenant repository for database operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError
from app.core.logging import get_logger
from app.infrastructure.database.models import Tenant

logger = get_logger(__name__)


class TenantRepository:
    """Repository for Tenant database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant.

        Args:
            tenant: Tenant model instance

        Returns:
            Created tenant

        Raises:
            ResourceAlreadyExistsError: If email already exists
        """
        # Check if email exists
        existing = await self.get_by_email(tenant.email)
        if existing:
            raise ResourceAlreadyExistsError(f"Tenant with email {tenant.email} already exists")

        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)

        logger.info("tenant_created", tenant_id=str(tenant.id), email=tenant.email)
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant or None if not found
        """
        result = await self.session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Tenant | None:
        """Get tenant by email.

        Args:
            email: Tenant email

        Returns:
            Tenant or None if not found
        """
        result = await self.session.execute(select(Tenant).where(Tenant.email == email))
        return result.scalar_one_or_none()

    async def update(self, tenant: Tenant) -> Tenant:
        """Update a tenant.

        Args:
            tenant: Tenant model instance with updates

        Returns:
            Updated tenant
        """
        await self.session.flush()
        await self.session.refresh(tenant)

        logger.info("tenant_updated", tenant_id=str(tenant.id))
        return tenant

    async def delete(self, tenant_id: UUID) -> bool:
        """Delete a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundError: If tenant not found
        """
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            raise ResourceNotFoundError(f"Tenant {tenant_id} not found")

        await self.session.delete(tenant)
        await self.session.flush()

        logger.info("tenant_deleted", tenant_id=str(tenant_id))
        return True
