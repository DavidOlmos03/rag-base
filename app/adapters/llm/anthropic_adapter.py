"""
Anthropic LLM adapter implementation for Claude models.
"""

from typing import AsyncGenerator

import anthropic
from anthropic import AsyncAnthropic

from app.adapters.llm.base import BaseLLMAdapter
from app.core.exceptions import LLMProviderError, LLMTimeoutError
from app.core.logging import get_logger
from app.domain.interfaces.llm_client import LLMMessage, LLMResponse, LLMUsage

logger = get_logger(__name__)


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude LLM implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229",
    ):
        """Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key
            model: Model name (e.g., 'claude-3-opus-20240229', 'claude-3-sonnet-20240229')
        """
        super().__init__(model=model, provider="anthropic")
        self.client = AsyncAnthropic(api_key=api_key)

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
            temperature: Sampling temperature (0-1 for Anthropic)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM response
        """
        try:
            # Anthropic expects max_tokens to be provided (default to 1024 if not specified)
            if max_tokens is None:
                max_tokens = 1024

            # Convert messages to Anthropic format
            # Anthropic separates system messages from the rest
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Build request parameters
            request_params = {
                "model": self._model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add system message if present
            if system_message:
                request_params["system"] = system_message

            # Add any additional kwargs
            request_params.update(kwargs)

            response = await self.client.messages.create(**request_params)

            # Extract content from response
            content = ""
            if response.content:
                # Anthropic returns a list of content blocks
                content = " ".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )

            return LLMResponse(
                content=content,
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                ),
                finish_reason=response.stop_reason or "stop",
            )
        except anthropic.APITimeoutError as e:
            logger.error("anthropic_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("Anthropic request timed out") from e
        except anthropic.APIError as e:
            logger.error("anthropic_api_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Anthropic API error: {str(e)}") from e
        except Exception as e:
            logger.error("anthropic_unexpected_error", model=self._model, error=str(e))
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
            temperature: Sampling temperature (0-1 for Anthropic)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Response chunks as they arrive
        """
        try:
            # Anthropic expects max_tokens to be provided
            if max_tokens is None:
                max_tokens = 1024

            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Build request parameters
            request_params = {
                "model": self._model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add system message if present
            if system_message:
                request_params["system"] = system_message

            # Add any additional kwargs
            request_params.update(kwargs)

            # Create streaming response
            async with self.client.messages.stream(**request_params) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.APITimeoutError as e:
            logger.error("anthropic_stream_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("Anthropic streaming timed out") from e
        except anthropic.APIError as e:
            logger.error("anthropic_stream_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Anthropic streaming error: {str(e)}") from e
        except Exception as e:
            logger.error("anthropic_stream_unexpected_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Unexpected streaming error: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if service is healthy
        """
        try:
            # Anthropic doesn't have a dedicated health check endpoint
            # We'll do a minimal test request to verify the API key and connectivity
            await self.client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except anthropic.AuthenticationError:
            logger.warning(
                "anthropic_health_check_auth_failed",
                model=self._model,
                error="Invalid API key"
            )
            return False
        except anthropic.NotFoundError:
            logger.warning(
                "anthropic_health_check_model_not_found",
                model=self._model,
                error="Model not found or not accessible"
            )
            return False
        except Exception as e:
            logger.warning("anthropic_health_check_failed", model=self._model, error=str(e))
            return False
