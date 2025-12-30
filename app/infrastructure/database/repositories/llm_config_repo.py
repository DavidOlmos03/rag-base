"""
LLM Configuration repository for database operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.infrastructure.database.models import LLMConfig

logger = get_logger(__name__)


class LLMConfigRepository:
    """Repository for LLM Configuration database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, llm_config: LLMConfig) -> LLMConfig:
        """Create a new LLM configuration.

        Args:
            llm_config: LLMConfig model instance

        Returns:
            Created LLM config
        """
        # Deactivate other configs for this tenant
        await self.deactivate_all_for_tenant(llm_config.tenant_id)

        self.session.add(llm_config)
        await self.session.flush()
        await self.session.refresh(llm_config)

        logger.info(
            "llm_config_created",
            config_id=str(llm_config.id),
            tenant_id=str(llm_config.tenant_id),
            provider=llm_config.provider,
        )
        return llm_config

    async def get_by_id(self, config_id: UUID) -> LLMConfig | None:
        """Get LLM config by ID.

        Args:
            config_id: Config ID

        Returns:
            LLMConfig or None if not found
        """
        result = await self.session.execute(select(LLMConfig).where(LLMConfig.id == config_id))
        return result.scalar_one_or_none()

    async def get_active_by_tenant(self, tenant_id: UUID) -> LLMConfig | None:
        """Get active LLM config for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Active LLMConfig or None if not found
        """
        result = await self.session.execute(
            select(LLMConfig).where(
                LLMConfig.tenant_id == tenant_id, LLMConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_tenant(self, tenant_id: UUID) -> list[LLMConfig]:
        """Get all LLM configs for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of LLM configs
        """
        result = await self.session.execute(
            select(LLMConfig)
            .where(LLMConfig.tenant_id == tenant_id)
            .order_by(LLMConfig.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, llm_config: LLMConfig) -> LLMConfig:
        """Update an LLM configuration.

        Args:
            llm_config: LLMConfig model instance with updates

        Returns:
            Updated LLM config
        """
        await self.session.flush()
        await self.session.refresh(llm_config)

        logger.info("llm_config_updated", config_id=str(llm_config.id))
        return llm_config

    async def activate(self, config_id: UUID) -> LLMConfig:
        """Activate an LLM config and deactivate others.

        Args:
            config_id: Config ID to activate

        Returns:
            Activated config

        Raises:
            ResourceNotFoundError: If config not found
        """
        config = await self.get_by_id(config_id)
        if not config:
            raise ResourceNotFoundError(f"LLM config {config_id} not found")

        # Deactivate all others for this tenant
        await self.deactivate_all_for_tenant(config.tenant_id)

        # Activate this one
        config.is_active = True
        return await self.update(config)

    async def deactivate_all_for_tenant(self, tenant_id: UUID) -> None:
        """Deactivate all LLM configs for a tenant.

        Args:
            tenant_id: Tenant ID
        """
        configs = await self.get_all_by_tenant(tenant_id)
        for config in configs:
            if config.is_active:
                config.is_active = False

        await self.session.flush()

    async def delete(self, config_id: UUID) -> bool:
        """Delete an LLM config.

        Args:
            config_id: Config ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundError: If config not found
        """
        config = await self.get_by_id(config_id)
        if not config:
            raise ResourceNotFoundError(f"LLM config {config_id} not found")

        await self.session.delete(config)
        await self.session.flush()

        logger.info("llm_config_deleted", config_id=str(config_id))
        return True
