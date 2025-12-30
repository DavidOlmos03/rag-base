"""
Document service for business logic.
"""

import os
import uuid
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, FileTooLargeError
from app.core.logging import get_logger
from app.infrastructure.database.models import Document
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.vectorstore.qdrant_client import QdrantVectorStore
from app.rag.embeddings.batch_processor import EmbeddingBatchProcessor
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.loader import DocumentLoader

logger = get_logger(__name__)


class DocumentService:
    """Service for document processing and management."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        vector_store: QdrantVectorStore,
        embedding_processor: EmbeddingBatchProcessor,
    ):
        """Initialize document service.

        Args:
            document_repo: Document repository
            vector_store: Vector store
            embedding_processor: Embedding batch processor
        """
        self.document_repo = document_repo
        self.vector_store = vector_store
        self.embedding_processor = embedding_processor
        self.document_loader = DocumentLoader()
        self.chunker = TextChunker()

    async def upload_document(
        self,
        file_path: str,
        filename: str,
        tenant_id: UUID,
    ) -> Document:
        """Upload and process a document.

        Args:
            file_path: Path to uploaded file
            filename: Original filename
            tenant_id: Tenant ID

        Returns:
            Created document record

        Raises:
            FileTooLargeError: If file is too large
            DocumentProcessingError: If processing fails
        """
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise FileTooLargeError(
                f"File too large: {file_size} bytes. Max: {settings.MAX_UPLOAD_SIZE}"
            )

        # Get file extension
        file_extension = Path(filename).suffix.lower()

        # Create document record
        document = Document(
            tenant_id=tenant_id,
            filename=filename,
            file_type=file_extension.lstrip("."),
            file_size=file_size,
            file_path=file_path,
            status="pending",
        )

        created_doc = await self.document_repo.create(document)

        # Process document asynchronously (in background in production)
        try:
            await self._process_document(created_doc)
        except Exception as e:
            logger.error(
                "document_processing_failed",
                document_id=str(created_doc.id),
                error=str(e),
            )
            await self.document_repo.update_status(
                document_id=created_doc.id,
                status="failed",
                error_message=str(e),
            )
            raise DocumentProcessingError(f"Failed to process document: {str(e)}") from e

        return created_doc

    async def _process_document(self, document: Document) -> None:
        """Process document: parse, chunk, embed, and index.

        Args:
            document: Document to process
        """
        logger.info("processing_document", document_id=str(document.id))

        # Update status
        await self.document_repo.update_status(document.id, "processing")

        # Step 1: Parse document
        parsed_doc = await self.document_loader.load(document.file_path)

        # Step 2: Chunk text
        chunks = self.chunker.chunk_text(
            text=parsed_doc.content,
            metadata={
                "document_id": str(document.id),
                "filename": document.filename,
                "file_type": document.file_type,
                **parsed_doc.metadata,
            },
        )

        logger.info(
            "document_chunked",
            document_id=str(document.id),
            num_chunks=len(chunks),
        )

        # Step 3: Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await self.embedding_processor.embed_with_cache(chunk_texts)

        logger.info(
            "embeddings_generated",
            document_id=str(document.id),
            num_embeddings=len(embeddings),
        )

        # Step 4: Prepare for vector store
        collection_name = f"tenant_{document.tenant_id}"

        # Create collection if it doesn't exist
        if not await self.vector_store.collection_exists(collection_name):
            await self.vector_store.create_collection(
                collection_name=collection_name,
                vector_size=len(embeddings[0]),
                distance="cosine",
            )

        # Step 5: Index in vector store
        ids = [f"{document.id}_{i}" for i in range(len(chunks))]
        payloads = [
            {
                "content": chunk["content"],
                "document_id": str(document.id),
                "chunk_index": chunk["chunk_index"],
                "tenant_id": str(document.tenant_id),
                "metadata": chunk["metadata"],
            }
            for chunk in chunks
        ]

        await self.vector_store.upsert_vectors(
            collection_name=collection_name,
            ids=ids,
            vectors=embeddings,
            payloads=payloads,
        )

        logger.info(
            "document_indexed",
            document_id=str(document.id),
            collection=collection_name,
        )

        # Step 6: Update document status
        await self.document_repo.update_status(
            document_id=document.id,
            status="completed",
            num_chunks=len(chunks),
        )

        logger.info("document_processing_complete", document_id=str(document.id))

    async def delete_document(self, document_id: UUID, tenant_id: UUID) -> bool:
        """Delete a document and its vectors.

        Args:
            document_id: Document ID
            tenant_id: Tenant ID

        Returns:
            True if deleted
        """
        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return False

        # Delete vectors from vector store
        collection_name = f"tenant_{tenant_id}"
        if await self.vector_store.collection_exists(collection_name):
            # Get all chunk IDs for this document
            chunk_ids = [f"{document_id}_{i}" for i in range(document.num_chunks)]

            try:
                await self.vector_store.delete_vectors(
                    collection_name=collection_name,
                    ids=chunk_ids,
                )
            except Exception as e:
                logger.warning(
                    "vector_deletion_failed",
                    document_id=str(document_id),
                    error=str(e),
                )

        # Delete file from storage
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning("file_deletion_failed", file_path=document.file_path, error=str(e))

        # Delete database record
        await self.document_repo.delete(document_id)

        logger.info("document_deleted", document_id=str(document_id))
        return True
