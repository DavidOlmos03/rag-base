"""
Embedding batch processor with caching and deduplication.
"""

from app.core.logging import get_logger
from app.domain.interfaces.embedding_provider import EmbeddingProvider
from app.infrastructure.cache.cache_service import CacheService

logger = get_logger(__name__)


class EmbeddingBatchProcessor:
    """Batch and deduplicate embedding requests with caching."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        cache_service: CacheService,
    ):
        """Initialize batch processor.

        Args:
            embedding_provider: Embedding provider instance
            cache_service: Cache service instance
        """
        self.provider = embedding_provider
        self.cache = cache_service

    async def embed_with_cache(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with caching and deduplication.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in original order
        """
        # Step 1: Check cache
        results: dict[str, list[float]] = {}
        to_compute: list[str] = []

        for text in texts:
            cached = await self.cache.get_embedding(text, self.provider.model_name)
            if cached:
                results[text] = cached
            else:
                to_compute.append(text)

        cache_hits = len(texts) - len(to_compute)
        if cache_hits > 0:
            logger.info(
                "embedding_cache_hits",
                total=len(texts),
                cache_hits=cache_hits,
                to_compute=len(to_compute),
            )

        if not to_compute:
            return [results[t] for t in texts]

        # Step 2: Deduplicate
        unique_texts = list(set(to_compute))
        dedup_savings = len(to_compute) - len(unique_texts)

        if dedup_savings > 0:
            logger.info("embedding_deduplication", duplicates_removed=dedup_savings)

        # Step 3: Batch compute
        embeddings = await self.provider.embed_batch(unique_texts)

        # Step 4: Cache results
        for text, emb in zip(unique_texts, embeddings):
            await self.cache.set_embedding(text, self.provider.model_name, emb)
            results[text] = emb

        # Step 5: Return in original order
        return [results[t] for t in texts]

    async def embed_single_with_cache(self, text: str) -> list[float]:
        """Embed single text with caching.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache
        cached = await self.cache.get_embedding(text, self.provider.model_name)
        if cached:
            return cached

        # Compute
        embedding = await self.provider.embed_text(text)

        # Cache
        await self.cache.set_embedding(text, self.provider.model_name, embedding)

        return embedding
