"""OpenAI API provider (GPT models)."""

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

_API_URL = "https://api.openai.com/v1/chat/completions"
_DEFAULT_MODEL = "gpt-4o"
_MAX_RETRIES = 3
_BACKOFF_SECONDS = [1, 2, 4]


class OpenAIProvider(LLMProvider):
    """Provider that calls the OpenAI Chat Completions API."""

    def __init__(self, config: ProviderConfig) -> None:
        self._model = config.model or _DEFAULT_MODEL
        self._api_key = config.api_key
        self._max_tokens = config.max_tokens
        self._timeout = config.timeout

    @property
    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        if not self._api_key:
            raise LLMProviderError(
                "OpenAI API key not set. Set OPENAI_API_KEY environment variable."
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, object] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }

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
                raise LLMConnectionError("Cannot connect to OpenAI API.") from exc
            except httpx.TimeoutException as exc:
                raise LLMConnectionError(
                    f"OpenAI request timed out after {self._timeout}s."
                ) from exc

            duration_ms = int((time.monotonic_ns() - start) / 1_000_000)

            if resp.status_code == 429:
                last_error = LLMRateLimitError("OpenAI rate limit hit.")
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_SECONDS[attempt])
                    continue
                raise last_error

            if resp.status_code == 401:
                raise LLMProviderError("Invalid OpenAI API key.")

            if resp.status_code >= 400:
                raise LLMProviderError(
                    f"OpenAI API error {resp.status_code}: {resp.text[:200]}"
                )

            data = resp.json()
            choices = data.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self._model),
                provider="openai",
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                duration_ms=duration_ms,
            )

        raise last_error or LLMProviderError("OpenAI API call failed after retries.")
