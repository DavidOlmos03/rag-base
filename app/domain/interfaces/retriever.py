"""
Abstract interface for retrieval strategies.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    """Retrieved document chunk."""

    content: str
    score: float
    metadata: dict[str, Any]
    document_id: str
    chunk_id: str


class Retriever(ABC):
    """Abstract interface for retrieval strategies."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant chunks using vector search.

        Args:
            query: Search query
            tenant_id: Tenant identifier
            top_k: Number of chunks to retrieve
            score_threshold: Minimum similarity score
            filters: Additional metadata filters

        Returns:
            List of retrieved chunks
        """
        pass

    @abstractmethod
    async def hybrid_retrieve(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        alpha: float = 0.5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve using hybrid search (vector + keyword).

        Args:
            query: Search query
            tenant_id: Tenant identifier
            top_k: Number of chunks to retrieve
            alpha: Balance between vector (1.0) and keyword (0.0)
            filters: Additional metadata filters

        Returns:
            List of retrieved chunks
        """
        pass
