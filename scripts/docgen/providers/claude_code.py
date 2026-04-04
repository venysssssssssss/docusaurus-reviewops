"""Claude Code CLI provider — invokes the claude CLI as a subprocess."""

from __future__ import annotations

import shutil
import subprocess
import time
from typing import TYPE_CHECKING

from scripts.docgen.providers.base import (
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
)

if TYPE_CHECKING:
    from scripts.docgen.config import ProviderConfig

_DEFAULT_BINARY = "claude"


class ClaudeCodeProvider(LLMProvider):
    """Provider that invokes the Claude Code CLI for generation."""

    def __init__(self, config: ProviderConfig) -> None:
        self._binary = config.base_url or _DEFAULT_BINARY  # reuse base_url field for binary path
        self._model = config.model
        self._timeout = config.timeout

    @property
    def name(self) -> str:
        return "claude-code"

    def is_available(self) -> bool:
        return shutil.which(self._binary) is not None

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        binary = shutil.which(self._binary)
        if binary is None:
            raise LLMConnectionError(
                f"Claude Code CLI not found: {self._binary!r}. "
                "Install it from https://claude.ai/code"
            )

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

        cmd = [binary, "--print", "--dangerously-skip-permissions"]
        if self._model:
            cmd.extend(["--model", self._model])

        start = time.monotonic_ns()
        try:
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise LLMConnectionError(
                f"Claude Code CLI timed out after {self._timeout}s."
            ) from exc
        except FileNotFoundError as exc:
            raise LLMConnectionError(
                f"Claude Code CLI not found: {self._binary!r}"
            ) from exc

        duration_ms = int((time.monotonic_ns() - start) / 1_000_000)

        if result.returncode != 0:
            stderr = result.stderr.strip()[:200]
            raise LLMProviderError(
                f"Claude Code CLI exited with code {result.returncode}: {stderr}"
            )

        return LLMResponse(
            content=result.stdout,
            model=self._model or "claude-code-default",
            provider="claude-code",
            input_tokens=None,  # CLI doesn't report token counts
            output_tokens=None,
            duration_ms=duration_ms,
        )
