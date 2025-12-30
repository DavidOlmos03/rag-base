"""
Initialize database with tables and seed data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import get_password_hash
from app.infrastructure.database.models import Base, Tenant

configure_logging()
logger = get_logger(__name__)


async def create_tables():
    """Create all database tables."""
    logger.info("creating_tables", message="Creating database tables...")

    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    logger.info("tables_created", message="Database tables created successfully")


async def seed_test_data():
    """Seed database with test data."""
    logger.info("seeding_data", message="Seeding test data...")

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create test tenant
        test_tenant = Tenant(
            name="Test Tenant",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
        )

        session.add(test_tenant)
        await session.commit()

        logger.info(
            "test_tenant_created",
            tenant_id=str(test_tenant.id),
            email=test_tenant.email,
        )

    await engine.dispose()
    logger.info("seed_complete", message="Test data seeded successfully")


async def main():
    """Main initialization function."""
    try:
        logger.info("init_start", message="Starting database initialization...")

        # Create tables
        await create_tables()

        # Seed test data (optional)
        if settings.ENVIRONMENT == "development":
            await seed_test_data()

        logger.info("init_complete", message="Database initialization complete!")

        if settings.ENVIRONMENT == "development":
            print("\n" + "=" * 60)
            print("Test credentials:")
            print("  Email: test@example.com")
            print("  Password: testpassword123")
            print("=" * 60 + "\n")

    except Exception as e:
        logger.error("init_failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
