"""Architecture Decision Record (ADR) generator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.analyzer.git_history import get_commits, get_latest_tag, get_significant_changes
from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output
from scripts.docgen.prompts.templates import render_template

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot

_SYSTEM_PROMPT = (
    "You are a senior software architect. Generate an Architecture Decision Record "
    "in valid Docusaurus-compatible Markdown. Base it on the actual changes, not hypotheticals."
)

_ADR_NUMBER_PATTERN = re.compile(r"^(\d+)-")


class ADRGenerator(DocGenerator):
    """Generate ADR from git history analysis."""

    @property
    def name(self) -> str:
        return "adr"

    @property
    def output_filename(self) -> str:
        # Dynamic — depends on next ADR number
        num = self._next_adr_number()
        return f"adr/{num:03d}-auto-generated.md"

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        # ADR generation depends on git history, not specific files.
        # Use config files as proxy for "something significant changed".
        return [
            f.path for f in snapshot.files
            if f.path.name in ("pyproject.toml", "package.json", "Makefile")
            or str(f.path.relative_to(snapshot.root)).startswith(".github/workflows/")
        ]

    def _next_adr_number(self) -> int:
        """Scan existing ADRs and return next number."""
        adr_dir = self.config.output_dir / "adr"
        if not adr_dir.exists():
            return 1
        max_num = 0
        for path in adr_dir.glob("*.md"):
            match = _ADR_NUMBER_PATTERN.match(path.name)
            if match:
                max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    def _list_existing_adrs(self) -> str:
        """List existing ADR filenames for context."""
        adr_dir = self.config.output_dir / "adr"
        if not adr_dir.exists():
            return "(No existing ADRs)"
        adrs = sorted(adr_dir.glob("*.md"))
        if not adrs:
            return "(No existing ADRs)"
        return "\n".join(f"- {p.name}" for p in adrs)

    def generate(self, snapshot: CodebaseSnapshot) -> str:
        latest_tag = get_latest_tag()
        commits = get_commits(since_tag=latest_tag, limit=50)
        significant = get_significant_changes(commits, threshold=5)

        if not significant and not commits:
            return ""  # Nothing to document

        changes_summary = "\n".join(
            f"- [{c.sha[:8]}] {c.message} ({c.files_changed} files, "
            f"+{c.insertions}/-{c.deletions})"
            for c in (significant or commits[:10])
        )

        commits_content = "\n".join(
            f"- {c.date[:10]} {c.message} (by {c.author})"
            for c in commits[:20]
        )

        num = self._next_adr_number()
        adr_id = f"{num:03d}-auto-generated"

        prompt = render_template(
            "adr",
            changes_summary=changes_summary,
            commits_content=commits_content,
            existing_adrs=self._list_existing_adrs(),
            adr_id=adr_id,
            adr_title=f"ADR-{num:03d}: Auto-generated Decision Record",
            adr_label=f"ADR-{num:03d}",
            adr_position=str(num),
            adr_description=f"Architecture decision record #{num} based on recent changes.",
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content)
