"""
Redis client configuration.
"""

from redis.asyncio import Redis

from app.core.config import settings

# Global Redis client instance
redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Get Redis client instance.

    Returns:
        Redis client
    """
    global redis_client

    if redis_client is None:
        redis_client = Redis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )

    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client is not None:
        await redis_client.close()
        redis_client = None
