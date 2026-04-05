"""Changelog generator from git history."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.analyzer.git_history import get_commits, get_latest_tag
from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output
from scripts.docgen.prompts.templates import render_template

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot
    from scripts.docgen.providers.base import LLMResponse

_SYSTEM_PROMPT = (
    "You are a technical writer. Generate a clean changelog entry "
    "in Keep-a-Changelog format. Focus on user-facing changes."
)


class ChangelogGenerator(DocGenerator):
    """Generate CHANGELOG.md entry from git commits."""

    @property
    def name(self) -> str:
        return "changelog"

    @property
    def output_filename(self) -> str:
        # Changelog lives at repo root, not in docs-site/docs
        return "../../CHANGELOG.md"

    def output_path(self) -> Path:
        """Override to write at repo root."""
        return Path("CHANGELOG.md")

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        # Changelog depends on git history; use pyproject.toml as proxy
        return [
            f.path for f in snapshot.files
            if f.path.name == "pyproject.toml"
        ]

    def generate(self, snapshot: CodebaseSnapshot) -> tuple[str, LLMResponse | None]:
        latest_tag = get_latest_tag()
        commits = get_commits(since_tag=latest_tag, limit=100)

        if not commits:
            return "", None  # Nothing to document

        commits_content = "\n".join(
            f"- {c.sha[:8]} {c.message} (by {c.author}, {c.date[:10]})"
            for c in commits
        )

        existing = ""
        changelog_path = Path("CHANGELOG.md")
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding="utf-8")

        today = datetime.date.today().isoformat()
        version = "Unreleased"
        if latest_tag:
            # Suggest next patch version
            parts = latest_tag.lstrip("v").split(".")
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                version = ".".join(parts)

        prompt = render_template(
            "changelog",
            commits_content=commits_content,
            existing_changelog=existing[:2000] if existing else "(No existing changelog)",
            version=version,
            date=today,
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content), response
