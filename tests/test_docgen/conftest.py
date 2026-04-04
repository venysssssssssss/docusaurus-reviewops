"""Shared fixtures for docgen tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.docgen.config import DocgenConfig, ProviderConfig
from scripts.docgen.providers.mock import MockProvider


@pytest.fixture
def mock_provider() -> MockProvider:
    """Provider that returns deterministic markdown."""
    return MockProvider()


@pytest.fixture
def sample_config(tmp_path: Path) -> DocgenConfig:
    """Config pointing to tmp_path for output."""
    return DocgenConfig(
        provider=ProviderConfig(name="mock"),
        generators={
            "architecture": True,
            "standards": True,
            "runbook": True,
            "adr": True,
            "changelog": True,
            "api_enricher": False,
        },
        output_dir=tmp_path / "docs",
        backup=False,
        merge_strategy="preserve",
        cache_enabled=False,
        cache_dir=tmp_path / "cache",
        include_paths=["src/", "scripts/"],
        exclude_paths=["__pycache__/"],
    )


@pytest.fixture
def sample_codebase(tmp_path: Path) -> Path:
    """Create a minimal fake codebase in tmp_path."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("# main module\n")
    (src / "main.py").write_text(
        "from pathlib import Path\n\ndef run() -> None:\n    print('hello')\n"
    )

    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "deploy.sh").write_text("#!/bin/bash\necho 'deploying'\n")

    (tmp_path / "Makefile").write_text("all:\n\techo done\n")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 100\ntarget-version = "py312"\n'
    )

    # Fake .github
    gh = tmp_path / ".github" / "workflows"
    gh.mkdir(parents=True)
    (gh / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

    return tmp_path
