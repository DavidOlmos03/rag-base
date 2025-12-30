"""
SentenceTransformers embedding provider implementation.
"""

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.exceptions import EmbeddingError, EmbeddingModelNotFoundError
from app.core.logging import get_logger
from app.domain.interfaces.embedding_provider import EmbeddingProvider

logger = get_logger(__name__)


class SentenceTransformersProvider(EmbeddingProvider):
    """SentenceTransformers implementation of embedding provider."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):
        """Initialize SentenceTransformers provider.

        Args:
            model_name: Name of the model to use
            device: Device to use (cpu, cuda, mps)
        """
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._device = device or settings.EMBEDDING_DEVICE
        self._model: SentenceTransformer | None = None
        self._dimension: int | None = None
        self._max_length: int = settings.EMBEDDING_MAX_LENGTH

    def _load_model(self) -> None:
        """Lazy load the model."""
        if self._model is None:
            try:
                logger.info("loading_embedding_model", model=self._model_name, device=self._device)
                self._model = SentenceTransformer(
                    self._model_name,
                    device=self._device,
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(
                    "embedding_model_loaded",
                    model=self._model_name,
                    dimension=self._dimension,
                )
            except Exception as e:
                logger.error("embedding_model_load_failed", model=self._model_name, error=str(e))
                raise EmbeddingModelNotFoundError(
                    f"Failed to load embedding model: {str(e)}"
                ) from e

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingError: If embedding fails
        """
        self._load_model()

        try:
            # Truncate if needed
            if len(text) > self._max_length:
                text = text[: self._max_length]

            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding fails
        """
        self._load_model()

        try:
            # Truncate texts if needed
            truncated_texts = [
                text[: self._max_length] if len(text) > self._max_length else text
                for text in texts
            ]

            embeddings = self._model.encode(
                truncated_texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error("batch_embedding_failed", batch_size=len(texts), error=str(e))
            raise EmbeddingError(f"Failed to generate batch embeddings: {str(e)}") from e

    @property
    def dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding vector dimension
        """
        if self._dimension is None:
            self._load_model()
        return self._dimension or 0

    @property
    def model_name(self) -> str:
        """Get model name.

        Returns:
            Model name
        """
        return self._model_name

    @property
    def max_length(self) -> int:
        """Get maximum input length.

        Returns:
            Maximum token/character length
        """
        return self._max_length


# Global instance
_embedding_provider: SentenceTransformersProvider | None = None


def get_embedding_provider() -> SentenceTransformersProvider:
    """Get singleton embedding provider instance.

    Returns:
        SentenceTransformersProvider instance
    """
    global _embedding_provider

    if _embedding_provider is None:
        _embedding_provider = SentenceTransformersProvider()

    return _embedding_provider
