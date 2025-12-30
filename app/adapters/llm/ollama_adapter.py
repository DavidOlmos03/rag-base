"""
Ollama LLM adapter implementation for local models.
"""

from typing import AsyncGenerator

import httpx

from app.adapters.llm.base import BaseLLMAdapter
from app.core.exceptions import LLMProviderError, LLMTimeoutError
from app.core.logging import get_logger
from app.domain.interfaces.llm_client import LLMMessage, LLMResponse, LLMUsage

logger = get_logger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """Ollama LLM implementation for local models."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ):
        """Initialize Ollama adapter.

        Args:
            model: Model name (e.g., 'llama3', 'mistral')
            base_url: Ollama server URL
        """
        super().__init__(model=model, provider="ollama")
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

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
            payload = {
                "model": self._model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

            # Ollama doesn't provide detailed token counts, estimate them
            prompt_text = " ".join(m.content for m in messages)
            response_text = data["message"]["content"]
            estimated_prompt_tokens = len(prompt_text.split())
            estimated_completion_tokens = len(response_text.split())

            return LLMResponse(
                content=response_text,
                model=self._model,
                usage=LLMUsage(
                    prompt_tokens=estimated_prompt_tokens,
                    completion_tokens=estimated_completion_tokens,
                    total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
                ),
                finish_reason="stop",
            )
        except httpx.TimeoutException as e:
            logger.error("ollama_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("Ollama request timed out") from e
        except httpx.HTTPError as e:
            logger.error("ollama_http_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Ollama HTTP error: {str(e)}") from e
        except Exception as e:
            logger.error("ollama_unexpected_error", model=self._model, error=str(e))
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
            payload = {
                "model": self._model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": True,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        import json
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

        except httpx.TimeoutException as e:
            logger.error("ollama_stream_timeout", model=self._model, error=str(e))
            raise LLMTimeoutError("Ollama streaming timed out") from e
        except httpx.HTTPError as e:
            logger.error("ollama_stream_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Ollama streaming error: {str(e)}") from e
        except Exception as e:
            logger.error("ollama_stream_unexpected_error", model=self._model, error=str(e))
            raise LLMProviderError(f"Unexpected streaming error: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if service is healthy
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            # Check if our model is available
            models = [model["name"] for model in data.get("models", [])]
            return self._model in models or any(self._model in name for name in models)
        except Exception as e:
            logger.warning("ollama_health_check_failed", model=self._model, error=str(e))
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
