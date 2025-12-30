"""
Pydantic schemas for RAG Query operations.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for RAG query request."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_hybrid_search: bool = False
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4000)
    stream: bool = False
    filters: dict[str, Any] | None = None


class QueryContext(BaseModel):
    """Schema for retrieved context."""

    content: str
    score: float
    document_id: UUID
    chunk_id: str
    metadata: dict[str, Any] = {}


class QueryResponse(BaseModel):
    """Schema for RAG query response."""

    query_id: UUID
    query: str
    answer: str
    contexts: list[QueryContext]
    model_used: str
    tokens_used: int
    processing_time: float  # seconds
    created_at: datetime


class QueryStreamChunk(BaseModel):
    """Schema for streaming query response chunk."""

    chunk: str
    is_final: bool = False


class QueryHistoryItem(BaseModel):
    """Schema for query history item."""

    id: UUID
    query: str
    answer: str
    model_used: str
    tokens_used: int
    processing_time: float
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    """Schema for query history response."""

    total: int
    items: list[QueryHistoryItem]
    page: int
    page_size: int
