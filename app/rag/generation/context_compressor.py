"""
Context compression to reduce token usage and costs.
"""

from typing import Literal

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.interfaces.retriever import RetrievedChunk

logger = get_logger(__name__)


class ContextCompressor:
    """Compress retrieved context to fit token budget."""

    def __init__(self, max_tokens: int | None = None):
        """Initialize context compressor.

        Args:
            max_tokens: Maximum tokens for context
        """
        self.max_tokens = max_tokens or settings.CONTEXT_MAX_TOKENS

    async def compress(
        self,
        chunks: list[RetrievedChunk],
        strategy: Literal["top_k", "score_threshold", "token_limit"] = "top_k",
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Compress chunks to fit budget.

        Args:
            chunks: Retrieved chunks
            strategy: Compression strategy
            top_k: Number of top chunks to keep (for top_k strategy)
            score_threshold: Minimum score (for score_threshold strategy)

        Returns:
            Compressed list of chunks
        """
        if not chunks:
            return []

        if strategy == "top_k":
            return self._compress_top_k(chunks, top_k or settings.DEFAULT_TOP_K)
        elif strategy == "score_threshold":
            return self._compress_by_score(
                chunks, score_threshold or settings.DEFAULT_RETRIEVAL_SCORE_THRESHOLD
            )
        elif strategy == "token_limit":
            return self._compress_by_tokens(chunks)
        else:
            return self._compress_top_k(chunks, settings.DEFAULT_TOP_K)

    def _compress_top_k(
        self,
        chunks: list[RetrievedChunk],
        k: int,
    ) -> list[RetrievedChunk]:
        """Keep only top K chunks by score.

        Args:
            chunks: Retrieved chunks
            k: Number to keep

        Returns:
            Top K chunks
        """
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        compressed = sorted_chunks[:k]

        logger.debug(
            "context_compressed_top_k",
            original_count=len(chunks),
            compressed_count=len(compressed),
            k=k,
        )

        return compressed

    def _compress_by_score(
        self,
        chunks: list[RetrievedChunk],
        threshold: float,
    ) -> list[RetrievedChunk]:
        """Filter chunks by score threshold.

        Args:
            chunks: Retrieved chunks
            threshold: Minimum score

        Returns:
            Filtered chunks
        """
        compressed = [chunk for chunk in chunks if chunk.score >= threshold]

        logger.debug(
            "context_compressed_score",
            original_count=len(chunks),
            compressed_count=len(compressed),
            threshold=threshold,
        )

        return compressed

    def _compress_by_tokens(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Compress to fit token budget.

        Args:
            chunks: Retrieved chunks

        Returns:
            Compressed chunks fitting token budget
        """
        # Sort by score (highest first)
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)

        compressed = []
        total_tokens = 0

        for chunk in sorted_chunks:
            # Rough token estimation (1 token ≈ 4 characters for English)
            chunk_tokens = len(chunk.content) // 4

            if total_tokens + chunk_tokens <= self.max_tokens:
                compressed.append(chunk)
                total_tokens += chunk_tokens
            else:
                break

        logger.debug(
            "context_compressed_tokens",
            original_count=len(chunks),
            compressed_count=len(compressed),
            estimated_tokens=total_tokens,
            max_tokens=self.max_tokens,
        )

        return compressed

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
