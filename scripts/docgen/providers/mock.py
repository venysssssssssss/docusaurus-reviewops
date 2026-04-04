"""Mock LLM provider for testing — returns deterministic markdown."""

from __future__ import annotations

from scripts.docgen.providers.base import LLMProvider, LLMResponse

_MOCK_ARCHITECTURE = """\
---
id: overview
title: Architecture Overview
sidebar_label: Overview
sidebar_position: 1
description: "System architecture and component overview."
keywords: [architecture, system, components]
---

# Architecture Overview

:::info Auto-generated
This document was generated automatically by docgen.
:::

## Components

```mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Service Layer]
    C --> D[Database]
```

## Veja tambem

- [Standards](/standards/coding-standards)
- [Deploy](/runbooks/deploy)
"""

_MOCK_RESPONSES: dict[str, str] = {
    "architecture": _MOCK_ARCHITECTURE,
}


class MockProvider(LLMProvider):
    """Provider that returns deterministic markdown for testing."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or _MOCK_RESPONSES

    @property
    def name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        # Try to match prompt content to a known response
        content = _MOCK_ARCHITECTURE
        for key, value in self._responses.items():
            if key.lower() in prompt.lower():
                content = value
                break

        return LLMResponse(
            content=content,
            model="mock-model",
            provider="mock",
            input_tokens=len(prompt.split()),
            output_tokens=len(content.split()),
            duration_ms=1,
        )
