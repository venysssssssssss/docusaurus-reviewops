"""Anthropic API provider (Claude models)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import httpx

from scripts.docgen.providers.base import (
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)

if TYPE_CHECKING:
    from scripts.docgen.config import ProviderConfig

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"
_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_MAX_RETRIES = 3
_BACKOFF_SECONDS = [1, 2, 4]


class AnthropicProvider(LLMProvider):
    """Provider that calls the Anthropic Messages API."""

    def __init__(self, config: ProviderConfig) -> None:
        self._model = config.model or _DEFAULT_MODEL
        self._api_key = config.api_key
        self._max_tokens = config.max_tokens
        self._timeout = config.timeout

    @property
    def name(self) -> str:
        return "anthropic"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key or "",
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        if not self._api_key:
            raise LLMProviderError(
                "Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable."
            )

        messages = [{"role": "user", "content": prompt}]
        payload: dict[str, object] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            start = time.monotonic_ns()
            try:
                resp = httpx.post(
                    _API_URL,
                    json=payload,
                    headers=self._headers(),
                    timeout=self._timeout,
                )
            except httpx.ConnectError as exc:
                raise LLMConnectionError("Cannot connect to Anthropic API.") from exc
            except httpx.TimeoutException as exc:
                raise LLMConnectionError(
                    f"Anthropic request timed out after {self._timeout}s."
                ) from exc

            duration_ms = int((time.monotonic_ns() - start) / 1_000_000)

            if resp.status_code == 429:
                last_error = LLMRateLimitError("Anthropic rate limit hit.")
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_SECONDS[attempt])
                    continue
                raise last_error

            if resp.status_code == 401:
                raise LLMProviderError("Invalid Anthropic API key.")

            if resp.status_code >= 400:
                raise LLMProviderError(
                    f"Anthropic API error {resp.status_code}: {resp.text[:200]}"
                )

            data = resp.json()
            content_blocks = data.get("content", [])
            content = "".join(
                block.get("text", "") for block in content_blocks if block.get("type") == "text"
            )
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self._model),
                provider="anthropic",
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                duration_ms=duration_ms,
            )

        raise last_error or LLMProviderError("Anthropic API call failed after retries.")
