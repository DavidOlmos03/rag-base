"""
Factory for creating LLM client instances.
"""

from app.adapters.llm.ollama_adapter import OllamaAdapter
from app.adapters.llm.openai_adapter import OpenAIAdapter
from app.core.config import settings
from app.core.exceptions import InvalidLLMConfigError
from app.domain.interfaces.llm_client import LLMClient


class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(
        provider: str,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> LLMClient:
        """Create an LLM client based on provider.

        Args:
            provider: Provider name (openai, anthropic, deepseek, ollama)
            model: Model name
            api_key: API key (optional for local models)
            base_url: Base URL (optional)

        Returns:
            LLMClient instance

        Raises:
            InvalidLLMConfigError: If provider is not supported
        """
        if provider == "openai":
            if not api_key and not settings.OPENAI_API_KEY:
                raise InvalidLLMConfigError("OpenAI API key is required")

            return OpenAIAdapter(
                api_key=api_key or settings.OPENAI_API_KEY or "",
                model=model,
                base_url=base_url or settings.OPENAI_BASE_URL,
            )

        elif provider == "anthropic":
            # Import only when needed to avoid dependency issues
            try:
                from app.adapters.llm.anthropic_adapter import AnthropicAdapter

                if not api_key and not settings.ANTHROPIC_API_KEY:
                    raise InvalidLLMConfigError("Anthropic API key is required")

                return AnthropicAdapter(
                    api_key=api_key or settings.ANTHROPIC_API_KEY or "",
                    model=model,
                )
            except ImportError:
                raise InvalidLLMConfigError("Anthropic adapter not implemented yet")

        elif provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            if not api_key and not settings.DEEPSEEK_API_KEY:
                raise InvalidLLMConfigError("DeepSeek API key is required")

            return OpenAIAdapter(
                api_key=api_key or settings.DEEPSEEK_API_KEY or "",
                model=model,
                base_url=base_url or settings.DEEPSEEK_BASE_URL,
            )

        elif provider == "ollama":
            return OllamaAdapter(
                model=model,
                base_url=base_url or settings.OLLAMA_BASE_URL,
            )

        else:
            raise InvalidLLMConfigError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def get_available_providers() -> dict[str, dict]:
        """Get information about available LLM providers.

        Returns:
            Dictionary of provider information
        """
        return {
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "deepseek": {
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-coder"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "ollama": {
                "name": "Ollama (Local)",
                "models": ["llama3", "mistral", "mixtral", "phi3", "gemma"],
                "requires_api_key": False,
                "supports_streaming": True,
            },
        }
