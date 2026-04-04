"""Tests for document generators using mock provider."""

from __future__ import annotations

from pathlib import Path

from scripts.docgen.analyzer.codebase import analyze_codebase
from scripts.docgen.config import DocgenConfig
from scripts.docgen.generators.architecture import ArchitectureGenerator
from scripts.docgen.generators.runbook import RunbookGenerator
from scripts.docgen.generators.standards import StandardsGenerator
from scripts.docgen.providers.mock import MockProvider


class TestArchitectureGenerator:
    def test_name(self, mock_provider: MockProvider, sample_config: DocgenConfig) -> None:
        gen = ArchitectureGenerator(mock_provider, sample_config)
        assert gen.name == "architecture"

    def test_output_filename(self, mock_provider: MockProvider, sample_config: DocgenConfig) -> None:
        gen = ArchitectureGenerator(mock_provider, sample_config)
        assert gen.output_filename == "architecture/overview.md"

    def test_generates_content(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = ArchitectureGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, ["src/", "scripts/"], [])
        content = gen.generate(snapshot)
        assert len(content) > 0
        assert "Architecture" in content

    def test_relevant_paths(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = ArchitectureGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, ["src/", "scripts/", ".github/"], [])
        paths = gen.relevant_paths(snapshot)
        assert len(paths) > 0


class TestStandardsGenerator:
    def test_name(self, mock_provider: MockProvider, sample_config: DocgenConfig) -> None:
        gen = StandardsGenerator(mock_provider, sample_config)
        assert gen.name == "standards"

    def test_relevant_paths_finds_pyproject(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = StandardsGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, [], [])
        paths = gen.relevant_paths(snapshot)
        names = [p.name for p in paths]
        assert "pyproject.toml" in names


class TestRunbookGenerator:
    def test_name(self, mock_provider: MockProvider, sample_config: DocgenConfig) -> None:
        gen = RunbookGenerator(mock_provider, sample_config)
        assert gen.name == "runbook"

    def test_relevant_paths_finds_workflows(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = RunbookGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, [".github/", "scripts/"], [])
        paths = gen.relevant_paths(snapshot)
        assert len(paths) > 0
