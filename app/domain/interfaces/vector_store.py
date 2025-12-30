"""
Abstract interface for vector stores.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class VectorSearchResult(BaseModel):
    """Vector search result."""

    id: str
    score: float
    payload: dict[str, Any]
    vector: list[float] | None = None


class VectorStore(ABC):
    """Abstract interface for vector databases."""

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "cosine",
    ) -> bool:
        """Create a new collection.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (cosine, euclidean, dot)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def upsert_vectors(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> bool:
        """Insert or update vectors.

        Args:
            collection_name: Name of the collection
            ids: List of vector IDs
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter: Metadata filter conditions

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def delete_vectors(
        self,
        collection_name: str,
        ids: list[str],
    ) -> bool:
        """Delete vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of vector IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get collection information.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection metadata and stats
        """
        pass
