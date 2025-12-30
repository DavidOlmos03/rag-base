"""
Base LLM adapter with common functionality.
"""

from app.domain.interfaces.llm_client import LLMClient


class BaseLLMAdapter(LLMClient):
    """Base class for LLM adapters with common utilities."""

    def __init__(self, model: str, provider: str):
        """Initialize base adapter.

        Args:
            model: Model name
            provider: Provider name
        """
        self._model = model
        self._provider = provider

    @property
    def model_name(self) -> str:
        """Get the model name.

        Returns:
            Model name
        """
        return self._model

    @property
    def provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name
        """
        return self._provider
