"""
Cache service for embeddings, queries, and responses.
"""

import hashlib
import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Multi-layer caching service for cost optimization."""

    def __init__(self, redis: Redis):
        """Initialize cache service.

        Args:
            redis: Redis client instance
        """
        self.redis = redis
        self.embedding_cache_ttl = settings.EMBEDDING_CACHE_TTL
        self.query_cache_ttl = settings.QUERY_CACHE_TTL
        self.response_cache_ttl = settings.RESPONSE_CACHE_TTL

    def _make_key(self, prefix: str, data: str) -> str:
        """Generate cache key with hash.

        Args:
            prefix: Key prefix
            data: Data to hash

        Returns:
            Cache key
        """
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"

    async def get_embedding(self, text: str, model: str) -> list[float] | None:
        """Get cached embedding.

        Args:
            text: Text that was embedded
            model: Embedding model name

        Returns:
            Embedding vector or None if not cached
        """
        key = self._make_key(f"emb:{model}", text)
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug("embedding_cache_hit", key=key)
                return json.loads(cached)
        except Exception as e:
            logger.warning("embedding_cache_error", error=str(e))
        return None

    async def set_embedding(
        self,
        text: str,
        model: str,
        embedding: list[float],
    ) -> None:
        """Cache embedding.

        Args:
            text: Text that was embedded
            model: Embedding model name
            embedding: Embedding vector
        """
        key = self._make_key(f"emb:{model}", text)
        try:
            await self.redis.setex(
                key,
                self.embedding_cache_ttl,
                json.dumps(embedding),
            )
            logger.debug("embedding_cached", key=key)
        except Exception as e:
            logger.warning("embedding_cache_set_error", error=str(e))

    async def get_query_response(
        self,
        query: str,
        tenant_id: str,
        config_hash: str,
    ) -> dict[str, Any] | None:
        """Get cached query response.

        Args:
            query: Query text
            tenant_id: Tenant identifier
            config_hash: Hash of LLM configuration

        Returns:
            Cached response or None
        """
        key = self._make_key(
            f"query:{tenant_id}:{config_hash}",
            query,
        )
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug("query_cache_hit", key=key)
                return json.loads(cached)
        except Exception as e:
            logger.warning("query_cache_error", error=str(e))
        return None

    async def set_query_response(
        self,
        query: str,
        tenant_id: str,
        config_hash: str,
        response: dict[str, Any],
    ) -> None:
        """Cache query response.

        Args:
            query: Query text
            tenant_id: Tenant identifier
            config_hash: Hash of LLM configuration
            response: Query response to cache
        """
        key = self._make_key(
            f"query:{tenant_id}:{config_hash}",
            query,
        )
        try:
            await self.redis.setex(
                key,
                self.response_cache_ttl,
                json.dumps(response),
            )
            logger.debug("query_cached", key=key)
        except Exception as e:
            logger.warning("query_cache_set_error", error=str(e))

    async def invalidate_tenant_cache(self, tenant_id: str) -> None:
        """Invalidate all cache entries for a tenant.

        Args:
            tenant_id: Tenant identifier
        """
        pattern = f"query:{tenant_id}:*"
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info("tenant_cache_invalidated", tenant_id=tenant_id, keys_deleted=len(keys))
        except Exception as e:
            logger.warning("cache_invalidation_error", error=str(e))
