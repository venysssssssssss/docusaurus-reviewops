"""LLM provider implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.docgen.config import ProviderConfig

from scripts.docgen.providers.base import (
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)

__all__ = [
    "LLMConnectionError",
    "LLMProvider",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMResponse",
    "create_provider",
]


def create_provider(config: ProviderConfig) -> LLMProvider:
    """Instantiate the appropriate provider from config.

    Fallback chain: configured provider -> error with helpful message.
    """
    name = config.name

    if name == "ollama":
        from scripts.docgen.providers.ollama import OllamaProvider

        return OllamaProvider(config)

    if name == "anthropic":
        from scripts.docgen.providers.anthropic import AnthropicProvider

        return AnthropicProvider(config)

    if name == "openai":
        from scripts.docgen.providers.openai import OpenAIProvider

        return OpenAIProvider(config)

    if name == "claude-code":
        from scripts.docgen.providers.claude_code import ClaudeCodeProvider

        return ClaudeCodeProvider(config)

    if name == "mock":
        from scripts.docgen.providers.mock import MockProvider

        return MockProvider()

    raise LLMProviderError(
        f"Unknown provider: {name!r}. "
        "Valid options: ollama, anthropic, openai, claude-code, mock"
    )
