"""End-to-end integration tests: CLI → analyzer → generator → writer → cache."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.docgen.analyzer.codebase import analyze_codebase
from scripts.docgen.analyzer.hasher import compute_hash, has_changed, save_hash
from scripts.docgen.cache.store import CacheStore
from scripts.docgen.cli import _run
from scripts.docgen.config import DocgenConfig, ProviderConfig
from scripts.docgen.generators.architecture import ArchitectureGenerator
from scripts.docgen.providers.mock import MockProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path, cache_enabled: bool = True) -> DocgenConfig:
    return DocgenConfig(
        provider=ProviderConfig(name="mock"),
        generators={"architecture": True},
        output_dir=tmp_path / "docs",
        backup=False,
        merge_strategy="overwrite",
        cache_enabled=cache_enabled,
        cache_dir=tmp_path / "cache",
        include_paths=["src/"],
        exclude_paths=["__pycache__/"],
    )


def _make_codebase(base: Path) -> Path:
    src = base / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "main.py").write_text("def main():\n    print('hello')\n")
    (base / "Makefile").write_text("all:\n\tpython src/main.py\n")
    return base


# ---------------------------------------------------------------------------
# E2E: generator writes output
# ---------------------------------------------------------------------------


class TestE2EGeneratorWritesOutput:
    def test_architecture_generator_produces_valid_output(self, tmp_path: Path) -> None:
        """Full pipeline: analyze → generate → write."""
        codebase = _make_codebase(tmp_path / "repo")
        config = _make_config(tmp_path)
        provider = MockProvider()
        config.output_dir.mkdir(parents=True, exist_ok=True)

        snapshot = analyze_codebase(codebase, ["src/"], [])
        gen = ArchitectureGenerator(provider, config)

        content, response = gen.generate(snapshot)

        assert len(content) > 0
        assert response is not None
        assert response.provider == "mock"
        # MockProvider returns valid markdown with frontmatter
        assert "---" in content

    def test_output_path_is_under_output_dir(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        provider = MockProvider()
        gen = ArchitectureGenerator(provider, config)
        assert str(gen.output_path()).startswith(str(config.output_dir))


# ---------------------------------------------------------------------------
# E2E: cache hit
# ---------------------------------------------------------------------------


class TestE2ECacheHit:
    def test_cache_hit_skips_generation(self, tmp_path: Path) -> None:
        """After saving a hash, has_changed returns False (cache hit)."""
        codebase = _make_codebase(tmp_path / "repo")
        snapshot = analyze_codebase(codebase, ["src/"], [])
        config = _make_config(tmp_path)
        provider = MockProvider()
        gen = ArchitectureGenerator(provider, config)

        relevant = gen.relevant_paths(snapshot)
        cache_dir = config.cache_dir

        # Initially no cache
        assert has_changed(cache_dir, "architecture", relevant) is True

        # Save hash
        save_hash(cache_dir, "architecture", relevant)

        # Now should be a cache hit
        assert has_changed(cache_dir, "architecture", relevant) is False

    def test_cache_miss_after_source_change(self, tmp_path: Path) -> None:
        """Modifying a source file invalidates the cache."""
        codebase = _make_codebase(tmp_path / "repo")
        snapshot = analyze_codebase(codebase, ["src/"], [])
        config = _make_config(tmp_path)
        provider = MockProvider()
        gen = ArchitectureGenerator(provider, config)

        relevant = gen.relevant_paths(snapshot)
        cache_dir = config.cache_dir

        save_hash(cache_dir, "architecture", relevant)
        assert has_changed(cache_dir, "architecture", relevant) is False

        # Modify a source file
        (codebase / "src" / "main.py").write_text("def main():\n    print('changed')\n")

        assert has_changed(cache_dir, "architecture", relevant) is True


# ---------------------------------------------------------------------------
# E2E: CacheStore metadata
# ---------------------------------------------------------------------------


class TestCacheStoreMeta:
    def test_save_and_retrieve_metadata(self, tmp_path: Path) -> None:
        from scripts.docgen.cache.store import GenerationMeta

        cache = CacheStore(tmp_path / "cache")
        meta = GenerationMeta(
            generator="architecture",
            timestamp="2026-04-04T00:00:00+00:00",
            provider="mock",
            model="mock-model",
            estimated_cost_usd=None,
        )
        cache.save("architecture", "abc123", meta)
        assert cache.is_stale("architecture", "abc123") is False
        assert cache.is_stale("architecture", "differenthash") is True

    def test_clear_removes_all_entries(self, tmp_path: Path) -> None:
        from scripts.docgen.cache.store import GenerationMeta

        cache = CacheStore(tmp_path / "cache")
        meta = GenerationMeta(
            generator="standards",
            timestamp="2026-04-04T00:00:00+00:00",
            provider="mock",
            model="mock-model",
            estimated_cost_usd=0.01,
        )
        cache.save("standards", "xyz", meta)
        cache.clear()
        assert cache.is_stale("standards", "xyz") is True


# ---------------------------------------------------------------------------
# E2E: _run() integration via mock provider config
# ---------------------------------------------------------------------------


class TestRunIntegration:
    def test_run_returns_0_on_success(self, tmp_path: Path) -> None:
        """_run with mock provider and minimal codebase exits 0."""
        import argparse

        codebase = _make_codebase(tmp_path / "repo")
        config_file = tmp_path / ".docgen.yml"
        config_file.write_text(
            f"provider: mock\n"
            f"generators:\n  architecture: true\n"
            f"output:\n  docs_dir: {tmp_path / 'docs'}\n  backup: false\n"
            f"cache:\n  enabled: false\n"
            f"analyze:\n  include:\n    - src/\n  exclude: []\n"
        )

        args = argparse.Namespace(
            config=config_file,
            provider="mock",
            model=None,
            generators="architecture",
            output_dir=tmp_path / "docs",
            no_cache=True,
            dry_run=False,
            diff_only=False,
            preview=False,
            verbose=False,
        )

        # Change to codebase dir so analyze_codebase works with relative paths
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(codebase)
            exit_code = _run(args)
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0

    def test_run_dry_run_returns_0_even_with_changes(self, tmp_path: Path) -> None:
        """--dry-run never writes files and always returns 0 (no errors)."""
        import argparse
        import os

        codebase = _make_codebase(tmp_path / "repo")
        config_file = tmp_path / ".docgen.yml"
        config_file.write_text(
            f"provider: mock\n"
            f"generators:\n  architecture: true\n"
            f"output:\n  docs_dir: {tmp_path / 'docs'}\n  backup: false\n"
            f"cache:\n  enabled: false\n"
            f"analyze:\n  include:\n    - src/\n  exclude: []\n"
        )

        args = argparse.Namespace(
            config=config_file,
            provider="mock",
            model=None,
            generators="architecture",
            output_dir=tmp_path / "docs",
            no_cache=True,
            dry_run=True,
            diff_only=False,
            preview=False,
            verbose=False,
        )

        output_file = tmp_path / "docs" / "architecture" / "overview.md"
        old_cwd = os.getcwd()
        try:
            os.chdir(codebase)
            exit_code = _run(args)
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0
        # Dry-run must NOT have created the file
        assert not output_file.exists()
