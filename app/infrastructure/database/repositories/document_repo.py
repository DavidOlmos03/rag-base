"""
Document repository for database operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.infrastructure.database.models import Document

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for Document database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, document: Document) -> Document:
        """Create a new document.

        Args:
            document: Document model instance

        Returns:
            Created document
        """
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)

        logger.info(
            "document_created",
            document_id=str(document.id),
            tenant_id=str(document.tenant_id),
            filename=document.filename,
        )
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document or None if not found
        """
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Get documents for a tenant.

        Args:
            tenant_id: Tenant ID
            limit: Maximum number of documents
            offset: Offset for pagination

        Returns:
            List of documents
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, document: Document) -> Document:
        """Update a document.

        Args:
            document: Document model instance with updates

        Returns:
            Updated document
        """
        await self.session.flush()
        await self.session.refresh(document)

        logger.info("document_updated", document_id=str(document.id))
        return document

    async def update_status(
        self,
        document_id: UUID,
        status: str,
        num_chunks: int | None = None,
        error_message: str | None = None,
    ) -> Document:
        """Update document status.

        Args:
            document_id: Document ID
            status: New status
            num_chunks: Number of chunks (optional)
            error_message: Error message (optional)

        Returns:
            Updated document

        Raises:
            ResourceNotFoundError: If document not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            raise ResourceNotFoundError(f"Document {document_id} not found")

        document.status = status
        if num_chunks is not None:
            document.num_chunks = num_chunks
        if error_message is not None:
            document.error_message = error_message

        return await self.update(document)

    async def delete(self, document_id: UUID) -> bool:
        """Delete a document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundError: If document not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            raise ResourceNotFoundError(f"Document {document_id} not found")

        await self.session.delete(document)
        await self.session.flush()

        logger.info("document_deleted", document_id=str(document_id))
        return True

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count documents for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Document count
        """
        result = await self.session.execute(
            select(Document).where(Document.tenant_id == tenant_id)
        )
        return len(list(result.scalars().all()))
