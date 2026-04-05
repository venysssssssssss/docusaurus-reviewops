"""Tests for LLM provider retry logic and connection error handling."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import httpx
import pytest

from scripts.docgen.config import ProviderConfig
from scripts.docgen.providers.anthropic import AnthropicProvider, _MAX_RETRIES
from scripts.docgen.providers.base import LLMConnectionError, LLMRateLimitError
from scripts.docgen.providers.ollama import OllamaProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_anthropic_provider() -> AnthropicProvider:
    cfg = ProviderConfig(name="anthropic", api_key="test-key", model="claude-test")
    return AnthropicProvider(cfg)


def _make_ollama_provider() -> OllamaProvider:
    cfg = ProviderConfig(name="ollama", base_url="http://localhost:11434", model="llama3.2")
    return OllamaProvider(cfg)


def _ok_response(text: str = "response text") -> MagicMock:
    """Build a mock httpx.Response that simulates a successful Anthropic call."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "content": [{"type": "text", "text": text}],
        "model": "claude-test",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    return mock


def _rate_limit_response() -> MagicMock:
    mock = MagicMock()
    mock.status_code = 429
    return mock


def _ollama_ok_response(text: str = "ollama response") -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "response": text,
        "model": "llama3.2",
        "prompt_eval_count": 5,
        "eval_count": 10,
    }
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# AnthropicProvider — retry on 429
# ---------------------------------------------------------------------------


class TestAnthropicRetry:
    def test_retries_twice_then_succeeds(self) -> None:
        """429 × 2 then 200 — should succeed and call post 3 times."""
        provider = _make_anthropic_provider()
        responses = [_rate_limit_response(), _rate_limit_response(), _ok_response()]

        with (
            patch("scripts.docgen.providers.anthropic.httpx.post", side_effect=responses) as mock_post,
            patch("scripts.docgen.providers.anthropic.time.sleep") as mock_sleep,
        ):
            result = provider.generate("test prompt")

        assert result.content == "response text"
        assert mock_post.call_count == 3
        # Backoff calls: attempt 0 → sleep(1), attempt 1 → sleep(2)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    def test_raises_rate_limit_error_after_all_retries_exhausted(self) -> None:
        """429 on every attempt — must raise LLMRateLimitError."""
        provider = _make_anthropic_provider()
        responses = [_rate_limit_response()] * _MAX_RETRIES

        with (
            patch("scripts.docgen.providers.anthropic.httpx.post", side_effect=responses),
            patch("scripts.docgen.providers.anthropic.time.sleep"),
        ):
            with pytest.raises(LLMRateLimitError):
                provider.generate("test prompt")

    def test_no_sleep_on_single_attempt_success(self) -> None:
        """First attempt succeeds — no backoff sleep at all."""
        provider = _make_anthropic_provider()

        with (
            patch("scripts.docgen.providers.anthropic.httpx.post", return_value=_ok_response()),
            patch("scripts.docgen.providers.anthropic.time.sleep") as mock_sleep,
        ):
            provider.generate("test prompt")

        mock_sleep.assert_not_called()

    def test_backoff_uses_correct_sequence(self) -> None:
        """Sleep durations follow the _BACKOFF_SECONDS sequence [1, 2, 4]."""
        from scripts.docgen.providers.anthropic import _BACKOFF_SECONDS

        provider = _make_anthropic_provider()
        # 429 enough times to exhaust all backoff entries
        responses = [_rate_limit_response()] * _MAX_RETRIES

        sleep_calls: list[float] = []
        with (
            patch("scripts.docgen.providers.anthropic.httpx.post", side_effect=responses),
            patch("scripts.docgen.providers.anthropic.time.sleep", side_effect=lambda s: sleep_calls.append(s)),
        ):
            with pytest.raises(LLMRateLimitError):
                provider.generate("test prompt")

        assert sleep_calls == _BACKOFF_SECONDS[: _MAX_RETRIES - 1]


# ---------------------------------------------------------------------------
# AnthropicProvider — connection errors
# ---------------------------------------------------------------------------


class TestAnthropicConnectionErrors:
    def test_connect_error_raises_llm_connection_error(self) -> None:
        """httpx.ConnectError → LLMConnectionError with actionable message."""
        provider = _make_anthropic_provider()

        with patch(
            "scripts.docgen.providers.anthropic.httpx.post",
            side_effect=httpx.ConnectError("connection refused"),
        ):
            with pytest.raises(LLMConnectionError):
                provider.generate("test prompt")

    def test_timeout_raises_llm_connection_error(self) -> None:
        """httpx.TimeoutException → LLMConnectionError."""
        provider = _make_anthropic_provider()

        with patch(
            "scripts.docgen.providers.anthropic.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            with pytest.raises(LLMConnectionError):
                provider.generate("test prompt")

    def test_is_available_false_when_no_api_key(self) -> None:
        cfg = ProviderConfig(name="anthropic", api_key=None)
        provider = AnthropicProvider(cfg)
        assert provider.is_available() is False

    def test_is_available_true_when_api_key_set(self) -> None:
        cfg = ProviderConfig(name="anthropic", api_key="sk-test-key")
        provider = AnthropicProvider(cfg)
        assert provider.is_available() is True


# ---------------------------------------------------------------------------
# OllamaProvider — connection errors
# ---------------------------------------------------------------------------


class TestOllamaConnectionErrors:
    def test_connect_error_raises_llm_connection_error(self) -> None:
        """httpx.ConnectError → LLMConnectionError with 'ollama serve' hint."""
        provider = _make_ollama_provider()

        with patch(
            "scripts.docgen.providers.ollama.httpx.post",
            side_effect=httpx.ConnectError("connection refused"),
        ):
            with pytest.raises(LLMConnectionError, match="ollama serve"):
                provider.generate("test prompt")

    def test_timeout_raises_llm_connection_error(self) -> None:
        """httpx.TimeoutException → LLMConnectionError."""
        provider = _make_ollama_provider()

        with patch(
            "scripts.docgen.providers.ollama.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            with pytest.raises(LLMConnectionError, match="timed out"):
                provider.generate("test prompt")

    def test_is_available_false_when_ollama_not_running(self) -> None:
        """is_available() returns False if Ollama is not reachable."""
        provider = _make_ollama_provider()

        with patch(
            "scripts.docgen.providers.ollama.httpx.get",
            side_effect=httpx.ConnectError("connection refused"),
        ):
            assert provider.is_available() is False

    def test_is_available_false_on_timeout(self) -> None:
        provider = _make_ollama_provider()

        with patch(
            "scripts.docgen.providers.ollama.httpx.get",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            assert provider.is_available() is False

    def test_is_available_true_when_ollama_responds(self) -> None:
        provider = _make_ollama_provider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("scripts.docgen.providers.ollama.httpx.get", return_value=mock_resp):
            assert provider.is_available() is True

    def test_generate_success(self) -> None:
        """Successful Ollama call returns LLMResponse."""
        provider = _make_ollama_provider()

        with patch(
            "scripts.docgen.providers.ollama.httpx.post",
            return_value=_ollama_ok_response("hello world"),
        ):
            result = provider.generate("test prompt")

        assert result.content == "hello world"
        assert result.provider == "ollama"
        assert result.input_tokens == 5
        assert result.output_tokens == 10
