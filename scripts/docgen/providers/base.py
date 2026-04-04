"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int = 0


# Approximate pricing per 1M tokens (USD), as of mid-2026.
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
}


def estimate_cost(response: LLMResponse) -> float | None:
    """Estimate USD cost from token counts and model pricing."""
    if response.input_tokens is None or response.output_tokens is None:
        return None
    prices = PRICING.get(response.model)
    if prices is None:
        return None
    input_cost = (response.input_tokens / 1_000_000) * prices["input"]
    output_cost = (response.output_tokens / 1_000_000) * prices["output"]
    return input_cost + output_cost


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        """Send prompt to LLM and return response.

        Raises LLMProviderError on failure.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is reachable (API key valid, Ollama running, etc.)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier string."""


class LLMProviderError(Exception):
    """Base exception for provider errors."""


class LLMRateLimitError(LLMProviderError):
    """Rate limit hit — caller should retry with backoff."""


class LLMConnectionError(LLMProviderError):
    """Cannot reach provider (Ollama not running, network issue, etc.)."""
