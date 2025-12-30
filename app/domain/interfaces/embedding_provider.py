"""
Abstract interface for embedding providers.
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding vector dimension
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name.

        Returns:
            Model name
        """
        pass

    @property
    @abstractmethod
    def max_length(self) -> int:
        """Get maximum input length.

        Returns:
            Maximum token/character length
        """
        pass
