"""Abstract base class for document generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.analyzer.hasher import has_changed

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot
    from scripts.docgen.config import DocgenConfig
    from scripts.docgen.providers.base import LLMProvider


class DocGenerator(ABC):
    """Base class for all document generators."""

    def __init__(self, provider: LLMProvider, config: DocgenConfig) -> None:
        self.provider = provider
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Generator identifier (used for caching, logging)."""

    @property
    @abstractmethod
    def output_filename(self) -> str:
        """Relative path under output_dir for the generated file."""

    @abstractmethod
    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        """Return paths this generator cares about (for incremental hashing)."""

    @abstractmethod
    def generate(self, snapshot: CodebaseSnapshot) -> str:
        """Generate markdown document from codebase analysis."""

    def should_run(self, snapshot: CodebaseSnapshot) -> bool:
        """Check if generation is needed (cache check)."""
        if not self.config.cache_enabled:
            return True
        return has_changed(
            self.config.cache_dir,
            self.name,
            self.relevant_paths(snapshot),
        )

    def output_path(self) -> Path:
        """Full path to the output file."""
        return self.config.output_dir / self.output_filename

    def existing_content(self) -> str:
        """Read existing doc content, or empty string if not found."""
        path = self.output_path()
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""
