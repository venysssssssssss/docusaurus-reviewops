"""Ollama local LLM provider."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import httpx

from scripts.docgen.providers.base import (
    LLMConnectionError,
    LLMProvider,
    LLMResponse,
)

if TYPE_CHECKING:
    from scripts.docgen.config import ProviderConfig

_DEFAULT_MODEL = "llama3.2"
_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    """Provider that calls a local Ollama instance."""

    def __init__(self, config: ProviderConfig) -> None:
        self._model = config.model or _DEFAULT_MODEL
        self._base_url = (config.base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = config.timeout

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        payload: dict[str, object] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        start = time.monotonic_ns()
        try:
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMConnectionError(
                f"Ollama request timed out after {self._timeout}s."
            ) from exc

        duration_ms = int((time.monotonic_ns() - start) / 1_000_000)
        data = resp.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", self._model),
            provider="ollama",
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            duration_ms=duration_ms,
        )
