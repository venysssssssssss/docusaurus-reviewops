"""Configuration loading for docgen (.docgen.yml + env var interpolation)."""

from __future__ import annotations

import difflib
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_KNOWN_TOP_LEVEL_KEYS = frozenset({
    "provider", "model", "anthropic", "openai", "ollama", "claude_code",
    "generators", "output", "cache", "analyze",
})

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")

_DEFAULTS: dict[str, object] = {
    "provider": "ollama",
    "model": None,
    "anthropic": {
        "api_key": "${ANTHROPIC_API_KEY}",
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
    },
    "openai": {
        "api_key": "${OPENAI_API_KEY}",
        "model": "gpt-4o",
        "max_tokens": 4096,
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3.2",
        "timeout": 120,
    },
    "claude_code": {
        "binary": "claude",
        "model": None,
    },
    "generators": {
        "architecture": True,
        "standards": True,
        "runbook": True,
        "adr": True,
        "changelog": True,
        "api_enricher": False,
    },
    "output": {
        "docs_dir": "docs-site/docs",
        "backup": True,
        "merge_strategy": "preserve",
    },
    "cache": {
        "enabled": True,
        "dir": ".docgen-cache",
    },
    "analyze": {
        "include": ["src/", "app/", "api/", "scripts/", ".github/"],
        "exclude": ["node_modules/", ".venv/", "__pycache__/", "*.pyc"],
    },
}


def resolve_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} with os.environ value, or empty string if unset."""

    def _replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PATTERN.sub(_replace, value)


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    name: str
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 4096
    timeout: int = 120


@dataclass(frozen=True)
class DocgenConfig:
    """Full docgen configuration."""

    provider: ProviderConfig
    generators: dict[str, bool] = field(default_factory=dict)
    output_dir: Path = field(default_factory=lambda: Path("docs-site/docs"))
    backup: bool = True
    merge_strategy: str = "preserve"
    cache_enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path(".docgen-cache"))
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)


def _build_provider_config(raw: dict, provider_name: str) -> ProviderConfig:
    """Build ProviderConfig from raw YAML data for the selected provider."""
    provider_section = raw.get(provider_name.replace("-", "_"), {})
    global_model = raw.get("model")

    api_key_raw = provider_section.get("api_key", "")
    api_key = resolve_env_vars(str(api_key_raw)) if api_key_raw else None
    if api_key == "":
        api_key = None

    return ProviderConfig(
        name=provider_name,
        model=provider_section.get("model") or global_model,
        api_key=api_key,
        base_url=provider_section.get("base_url"),
        max_tokens=provider_section.get("max_tokens", 4096),
        timeout=provider_section.get("timeout", 120),
    )


def load_config(
    config_path: Path | None = None,
    overrides: dict[str, object] | None = None,
) -> DocgenConfig:
    """Load configuration from .docgen.yml with env var interpolation.

    Falls back to defaults if file does not exist.
    """
    raw: dict = dict(_DEFAULTS)

    if config_path is None:
        config_path = Path(".docgen.yml")

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                file_data = yaml.safe_load(f) or {}
            # Warn about unrecognised top-level keys and suggest corrections
            for key in file_data:
                if key not in _KNOWN_TOP_LEVEL_KEYS:
                    suggestions = difflib.get_close_matches(
                        key, _KNOWN_TOP_LEVEL_KEYS, n=1, cutoff=0.6
                    )
                    hint = f" — did you mean '{suggestions[0]}'?" if suggestions else ""
                    logger.warning(
                        "%s: unknown key '%s'%s (will be ignored)",
                        config_path, key, hint,
                    )
            raw = _deep_merge(raw, file_data)
        except yaml.YAMLError as exc:
            # Surface file path + line/column from problem_mark for actionable errors
            mark = getattr(exc, "problem_mark", None)
            location = (
                f"{config_path}:{mark.line + 1}:{mark.column + 1}"
                if mark is not None
                else str(config_path)
            )
            problem = getattr(exc, "problem", str(exc))
            logger.warning(
                "YAML parse error in %s: %s — using defaults",
                location, problem,
            )

    if overrides:
        raw = _deep_merge(raw, overrides)

    provider_name = str(raw.get("provider", "ollama"))
    provider_config = _build_provider_config(raw, provider_name)

    output_section = raw.get("output", {})
    cache_section = raw.get("cache", {})
    analyze_section = raw.get("analyze", {})
    generators_section = raw.get("generators", {})

    return DocgenConfig(
        provider=provider_config,
        generators=dict(generators_section) if isinstance(generators_section, dict) else {},
        output_dir=Path(output_section.get("docs_dir", "docs-site/docs")),
        backup=output_section.get("backup", True),
        merge_strategy=output_section.get("merge_strategy", "preserve"),
        cache_enabled=cache_section.get("enabled", True),
        cache_dir=Path(cache_section.get("dir", ".docgen-cache")),
        include_paths=analyze_section.get("include", []),
        exclude_paths=analyze_section.get("exclude", []),
    )
