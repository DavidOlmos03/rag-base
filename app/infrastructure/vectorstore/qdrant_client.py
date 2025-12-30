"""
Qdrant vector store client implementation.
"""

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
from app.core.exceptions import CollectionNotFoundError, VectorStoreError
from app.core.logging import get_logger
from app.domain.interfaces.vector_store import VectorSearchResult, VectorStore

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of vector store interface."""

    def __init__(self) -> None:
        """Initialize Qdrant client."""
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=settings.QDRANT_TIMEOUT,
            prefer_grpc=settings.QDRANT_PREFER_GRPC,
        )

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
        try:
            distance_map = {
                "cosine": qdrant_models.Distance.COSINE,
                "euclidean": qdrant_models.Distance.EUCLID,
                "dot": qdrant_models.Distance.DOT,
            }

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, qdrant_models.Distance.COSINE),
                ),
            )

            logger.info(
                "collection_created",
                collection=collection_name,
                vector_size=vector_size,
                distance=distance,
            )
            return True
        except Exception as e:
            logger.error("collection_creation_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to create collection: {str(e)}") from e

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists
        """
        try:
            collections = await self.client.get_collections()
            return any(col.name == collection_name for col in collections.collections)
        except Exception as e:
            logger.error("collection_check_failed", collection=collection_name, error=str(e))
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful
        """
        try:
            await self.client.delete_collection(collection_name=collection_name)
            logger.info("collection_deleted", collection=collection_name)
            return True
        except Exception as e:
            logger.error("collection_deletion_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to delete collection: {str(e)}") from e

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
        try:
            if not await self.collection_exists(collection_name):
                raise CollectionNotFoundError(f"Collection {collection_name} not found")

            points = [
                qdrant_models.PointStruct(id=id_, vector=vector, payload=payload)
                for id_, vector, payload in zip(ids, vectors, payloads)
            ]

            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(
                "vectors_upserted",
                collection=collection_name,
                count=len(ids),
            )
            return True
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error("vector_upsert_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to upsert vectors: {str(e)}") from e

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
        try:
            if not await self.collection_exists(collection_name):
                raise CollectionNotFoundError(f"Collection {collection_name} not found")

            # Convert filter to Qdrant format if provided
            qdrant_filter = None
            if filter:
                must_conditions = [
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                    for key, value in filter.items()
                ]
                qdrant_filter = qdrant_models.Filter(must=must_conditions)

            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=qdrant_filter,
            )

            search_results = [
                VectorSearchResult(
                    id=str(result.id),
                    score=result.score,
                    payload=result.payload or {},
                    vector=result.vector,
                )
                for result in results
            ]

            logger.debug(
                "vector_search_completed",
                collection=collection_name,
                results_count=len(search_results),
            )

            return search_results
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error("vector_search_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to search vectors: {str(e)}") from e

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
        try:
            if not await self.collection_exists(collection_name):
                raise CollectionNotFoundError(f"Collection {collection_name} not found")

            await self.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.PointIdsList(points=ids),
            )

            logger.info(
                "vectors_deleted",
                collection=collection_name,
                count=len(ids),
            )
            return True
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error("vector_deletion_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to delete vectors: {str(e)}") from e

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get collection information.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection metadata and stats
        """
        try:
            if not await self.collection_exists(collection_name):
                raise CollectionNotFoundError(f"Collection {collection_name} not found")

            info = await self.client.get_collection(collection_name=collection_name)

            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.value,
                },
            }
        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error("get_collection_info_failed", collection=collection_name, error=str(e))
            raise VectorStoreError(f"Failed to get collection info: {str(e)}") from e


# Global instance
_vector_store: QdrantVectorStore | None = None


async def get_vector_store() -> QdrantVectorStore:
    """Get vector store instance.

    Returns:
        QdrantVectorStore instance
    """
    global _vector_store

    if _vector_store is None:
        _vector_store = QdrantVectorStore()

    return _vector_store
