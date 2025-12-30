"""
Abstract interface for LLM clients.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """LLM message structure."""

    role: str
    content: str


class LLMUsage(BaseModel):
    """LLM usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """LLM response structure."""

    content: str
    model: str
    usage: LLMUsage
    finish_reason: str


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: dict,
    ) -> LLMResponse:
        """Generate a single response.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: dict,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Response chunks as they arrive
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if service is healthy
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name.

        Returns:
            Model name
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name (e.g., 'openai', 'anthropic')
        """
        pass
