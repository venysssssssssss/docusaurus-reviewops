"""Tests for LLM providers."""

from __future__ import annotations

import pytest

from scripts.docgen.config import ProviderConfig
from scripts.docgen.providers import create_provider
from scripts.docgen.providers.base import (
    LLMProviderError,
    LLMResponse,
    estimate_cost,
)
from scripts.docgen.providers.mock import MockProvider


class TestLLMResponse:
    def test_fields(self) -> None:
        resp = LLMResponse(
            content="hello",
            model="test",
            provider="mock",
            input_tokens=100,
            output_tokens=50,
            duration_ms=10,
        )
        assert resp.content == "hello"
        assert resp.model == "test"
        assert resp.input_tokens == 100

    def test_defaults(self) -> None:
        resp = LLMResponse(content="x", model="m", provider="p")
        assert resp.input_tokens is None
        assert resp.output_tokens is None
        assert resp.duration_ms == 0


class TestEstimateCost:
    def test_known_model(self) -> None:
        resp = LLMResponse(
            content="",
            model="gpt-4o",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
        )
        cost = estimate_cost(resp)
        assert cost is not None
        assert cost > 0

    def test_unknown_model_returns_none(self) -> None:
        resp = LLMResponse(
            content="",
            model="unknown-model",
            provider="test",
            input_tokens=100,
            output_tokens=50,
        )
        assert estimate_cost(resp) is None

    def test_none_tokens_returns_none(self) -> None:
        resp = LLMResponse(content="", model="gpt-4o", provider="openai")
        assert estimate_cost(resp) is None


class TestMockProvider:
    def test_always_available(self) -> None:
        provider = MockProvider()
        assert provider.is_available() is True

    def test_name(self) -> None:
        assert MockProvider().name == "mock"

    def test_returns_deterministic_output(self) -> None:
        provider = MockProvider()
        resp = provider.generate("test architecture prompt")
        assert "Architecture" in resp.content
        assert resp.provider == "mock"
        assert resp.input_tokens is not None

    def test_custom_responses(self) -> None:
        provider = MockProvider(responses={"custom": "# Custom Output"})
        resp = provider.generate("custom prompt")
        assert resp.content == "# Custom Output"


class TestCreateProvider:
    def test_mock(self) -> None:
        config = ProviderConfig(name="mock")
        provider = create_provider(config)
        assert isinstance(provider, MockProvider)

    def test_ollama(self) -> None:
        config = ProviderConfig(name="ollama")
        provider = create_provider(config)
        assert provider.name == "ollama"

    def test_anthropic(self) -> None:
        config = ProviderConfig(name="anthropic", api_key="test")
        provider = create_provider(config)
        assert provider.name == "anthropic"

    def test_openai(self) -> None:
        config = ProviderConfig(name="openai", api_key="test")
        provider = create_provider(config)
        assert provider.name == "openai"

    def test_claude_code(self) -> None:
        config = ProviderConfig(name="claude-code")
        provider = create_provider(config)
        assert provider.name == "claude-code"

    def test_unknown_raises(self) -> None:
        config = ProviderConfig(name="nonexistent")
        with pytest.raises(LLMProviderError, match="Unknown provider"):
            create_provider(config)
