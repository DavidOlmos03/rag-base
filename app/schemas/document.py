"""
Pydantic schemas for Document resources.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema."""

    filename: str
    file_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    tenant_id: UUID


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    filename: str | None = None


class DocumentInDB(DocumentBase):
    """Schema for document in database."""

    id: UUID
    tenant_id: UUID
    status: str  # pending, processing, completed, failed
    num_chunks: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: UUID
    status: str
    num_chunks: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    document_id: UUID
    filename: str
    status: str
    message: str
