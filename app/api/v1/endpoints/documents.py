"""
Document management endpoints.
"""

import os
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.dependencies import (
    get_cache_service,
    get_current_user,
    get_document_repository,
    get_embedding_provider_service,
    get_vector_store_service,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.services.document_service import DocumentService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.database.models import Tenant
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.rag.embeddings.batch_processor import EmbeddingBatchProcessor
from app.schemas.document import DocumentResponse, DocumentUploadResponse

logger = get_logger(__name__)

router = APIRouter()


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    vector_store=Depends(get_vector_store_service),
    cache_service: CacheService = Depends(get_cache_service),
    embedding_provider=Depends(get_embedding_provider_service),
) -> DocumentService:
    """Get document service with dependencies.

    Returns:
        DocumentService instance
    """
    embedding_processor = EmbeddingBatchProcessor(embedding_provider, cache_service)
    return DocumentService(document_repo, vector_store, embedding_processor)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document for processing.

    Args:
        file: Uploaded file
        current_user: Current authenticated user
        document_service: Document service

    Returns:
        Upload response with document info

    Raises:
        HTTPException: If upload or processing fails
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file_extension}",
        )

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    import uuid

    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}{file_extension}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(
            "file_uploaded",
            filename=file.filename,
            size=file.size,
            tenant_id=str(current_user.id),
        )

        # Process document
        document = await document_service.upload_document(
            file_path=str(file_path),
            filename=file.filename,
            tenant_id=current_user.id,
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            message="Document uploaded and processing started",
        )

    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.error("document_upload_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    current_user=Depends(get_current_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """List documents for current user.

    Args:
        limit: Maximum number of documents
        offset: Pagination offset
        current_user: Current authenticated user
        document_repo: Document repository

    Returns:
        List of documents
    """
    documents = await document_repo.get_by_tenant(
        tenant_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user=Depends(get_current_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """Get a specific document.

    Args:
        document_id: Document ID
        current_user: Current authenticated user
        document_repo: Document repository

    Returns:
        Document details

    Raises:
        HTTPException: If document not found or unauthorized
    """
    document = await document_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check ownership
    if document.tenant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user=Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """Delete a document.

    Args:
        document_id: Document ID
        current_user: Current authenticated user
        document_service: Document service
        document_repo: Document repository

    Raises:
        HTTPException: If document not found or unauthorized
    """
    # Check if document exists and user owns it
    document = await document_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.tenant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document",
        )

    # Delete document
    await document_service.delete_document(document_id, current_user.id)

    logger.info("document_deleted_via_api", document_id=str(document_id))
