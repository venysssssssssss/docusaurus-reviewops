"""Tests for docgen CLI."""

from __future__ import annotations

from scripts.docgen.cli import _build_parser, _select_generators
from scripts.docgen.config import DocgenConfig, ProviderConfig


class TestBuildParser:
    def test_parses_defaults(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.config is None
        assert args.provider is None
        assert args.dry_run is False
        assert args.verbose is False

    def test_parses_flags(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([
            "--provider", "anthropic",
            "--model", "claude-sonnet-4-20250514",
            "--generators", "architecture,standards",
            "--dry-run",
            "--verbose",
        ])
        assert args.provider == "anthropic"
        assert args.model == "claude-sonnet-4-20250514"
        assert args.generators == "architecture,standards"
        assert args.dry_run is True
        assert args.verbose is True

    def test_parses_preview(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--preview"])
        assert args.preview is True

    def test_parses_no_cache(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--no-cache"])
        assert args.no_cache is True


class TestSelectGenerators:
    def test_all_enabled(self) -> None:
        config = DocgenConfig(
            provider=ProviderConfig(name="mock"),
            generators={"architecture": True, "standards": True, "runbook": True},
        )
        result = _select_generators(config, None)
        assert "architecture" in result
        assert "standards" in result
        assert "runbook" in result

    def test_filter_overrides(self) -> None:
        config = DocgenConfig(
            provider=ProviderConfig(name="mock"),
            generators={"architecture": True, "standards": True, "runbook": True},
        )
        result = _select_generators(config, "architecture,runbook")
        assert result == ["architecture", "runbook"]

    def test_disabled_generators_excluded(self) -> None:
        config = DocgenConfig(
            provider=ProviderConfig(name="mock"),
            generators={"architecture": True, "standards": False},
        )
        result = _select_generators(config, None)
        assert "architecture" in result
        assert "standards" not in result

    def test_unknown_generator_in_filter_ignored(self) -> None:
        config = DocgenConfig(
            provider=ProviderConfig(name="mock"),
            generators={"architecture": True},
        )
        result = _select_generators(config, "architecture,nonexistent")
        assert result == ["architecture"]
