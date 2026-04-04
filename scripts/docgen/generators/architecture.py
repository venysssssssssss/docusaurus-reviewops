"""Architecture document generator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.analyzer.codebase import build_context_for_prompt
from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output
from scripts.docgen.prompts.templates import render_template

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot

_SYSTEM_PROMPT = (
    "You are a senior software architect. Generate clear, accurate documentation "
    "in valid Docusaurus-compatible Markdown. Be concise and practical."
)


class ArchitectureGenerator(DocGenerator):
    """Generate architecture overview from codebase analysis."""

    @property
    def name(self) -> str:
        return "architecture"

    @property
    def output_filename(self) -> str:
        return "architecture/overview.md"

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        """Config files, entry points, and structural files."""
        relevant_names = {
            "Makefile", "pyproject.toml", "package.json", "docusaurus.config.ts",
            "tsconfig.json", "Dockerfile", "docker-compose.yml",
        }
        relevant_prefixes = ("src/", "app/", "api/", ".github/", "scripts/")

        return [
            f.path for f in snapshot.files
            if f.path.name in relevant_names
            or any(str(f.path.relative_to(snapshot.root)).startswith(p) for p in relevant_prefixes)
        ]

    def generate(self, snapshot: CodebaseSnapshot) -> str:
        context = build_context_for_prompt(snapshot, self.relevant_paths(snapshot))
        existing = self.existing_content()

        prompt = render_template(
            "architecture",
            directory_tree=snapshot.directory_tree,
            key_files_content=context,
            existing_doc=existing or "(No existing document)",
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content)
