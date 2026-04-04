"""Tests for docgen configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.docgen.config import DocgenConfig, load_config, resolve_env_vars


class TestResolveEnvVars:
    def test_replaces_known_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_KEY", "secret123")
        assert resolve_env_vars("key=${MY_KEY}") == "key=secret123"

    def test_unknown_var_becomes_empty(self) -> None:
        result = resolve_env_vars("${UNLIKELY_VAR_NAME_XYZ}")
        assert result == ""

    def test_no_vars_unchanged(self) -> None:
        assert resolve_env_vars("plain text") == "plain text"

    def test_multiple_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("A", "1")
        monkeypatch.setenv("B", "2")
        assert resolve_env_vars("${A}-${B}") == "1-2"


class TestLoadConfig:
    def test_defaults_when_no_file(self, tmp_path: Path) -> None:
        config = load_config(config_path=tmp_path / "nonexistent.yml")
        assert isinstance(config, DocgenConfig)
        assert config.provider.name == "ollama"
        assert config.merge_strategy == "preserve"
        assert config.cache_enabled is True

    def test_loads_from_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / ".docgen.yml"
        yaml_path.write_text(
            "provider: mock\ngenerators:\n  architecture: false\n  standards: true\n"
        )
        config = load_config(config_path=yaml_path)
        assert config.provider.name == "mock"
        assert config.generators["architecture"] is False
        assert config.generators["standards"] is True

    def test_overrides_take_precedence(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / ".docgen.yml"
        yaml_path.write_text("provider: ollama\n")
        config = load_config(
            config_path=yaml_path,
            overrides={"provider": "anthropic"},
        )
        assert config.provider.name == "anthropic"

    def test_env_var_in_api_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        yaml_path = tmp_path / ".docgen.yml"
        yaml_path.write_text(
            "provider: anthropic\nanthropic:\n  api_key: ${ANTHROPIC_API_KEY}\n"
        )
        config = load_config(config_path=yaml_path)
        assert config.provider.api_key == "sk-test-123"

    def test_empty_api_key_is_none(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / ".docgen.yml"
        yaml_path.write_text("provider: anthropic\nanthropic:\n  api_key: ''\n")
        config = load_config(config_path=yaml_path)
        assert config.provider.api_key is None

    def test_invalid_yaml_uses_defaults(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / ".docgen.yml"
        yaml_path.write_text("{{invalid yaml")
        # Should not crash — falls back to defaults
        config = load_config(config_path=yaml_path)
        assert config.provider.name == "ollama"
