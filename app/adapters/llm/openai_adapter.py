"""
OpenAI LLM adapter implementation.
"""

from typing import AsyncGenerator

import openai
from openai import AsyncOpenAI

from app.adapters.llm.base import BaseLLMAdapter
from app.core.exceptions import LLMProviderError, LLMTimeoutError
from app.core.logging import get_logger
from app.domain.interfaces.llm_client import LLMMessage, LLMResponse, LLMUsage

logger = get_logger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI LLM implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: str | None = None,
    ):
        """Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            model: Model name
            base_url: Optional base URL for API
        """
        super().__init__(model=model, provider="openai")
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

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
        try:
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                finish_reason=response.choices[0].finish_reason,
            )
        except openai.APITimeoutError as e:
            logger.error("openai_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("OpenAI request timed out") from e
        except openai.APIError as e:
            logger.error("openai_api_error", model=self._model, error=str(e))
            raise LLMProviderError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error("openai_unexpected_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Unexpected error: {str(e)}") from e

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
        try:
            stream = await self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except openai.APITimeoutError as e:
            logger.error("openai_stream_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("OpenAI streaming timed out") from e
        except openai.APIError as e:
            logger.error("openai_stream_error", model=self._model, error=str(e))
            raise LLMProviderError(f"OpenAI streaming error: {str(e)}") from e
        except Exception as e:
            logger.error("openai_stream_unexpected_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Unexpected streaming error: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if service is healthy
        """
        try:
            await self.client.models.retrieve(self._model)
            return True
        except Exception as e:
            logger.warning("openai_health_check_failed", model=self._model, error=str(e))
            return False
