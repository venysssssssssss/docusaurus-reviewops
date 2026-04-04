"""Coding standards document generator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.analyzer.codebase import read_file_content
from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output
from scripts.docgen.prompts.templates import render_template

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot

_SYSTEM_PROMPT = (
    "You are a senior software engineer. Generate clear coding standards documentation "
    "in valid Docusaurus-compatible Markdown. Be specific about the project's actual tools."
)

_CONFIG_FILES = [
    "pyproject.toml",
    "tsconfig.json",
    ".editorconfig",
    ".eslintrc.json",
    ".eslintrc.js",
    "ruff.toml",
    ".prettierrc",
    ".prettierrc.json",
]


class StandardsGenerator(DocGenerator):
    """Generate coding standards from linter/formatter configuration."""

    @property
    def name(self) -> str:
        return "standards"

    @property
    def output_filename(self) -> str:
        return "standards/coding-standards.md"

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        return [
            f.path for f in snapshot.files
            if f.path.name in _CONFIG_FILES
        ]

    def generate(self, snapshot: CodebaseSnapshot) -> str:
        config_parts: list[str] = []
        for path in self.relevant_paths(snapshot):
            content = read_file_content(path)
            if content:
                rel = path.relative_to(snapshot.root)
                config_parts.append(f"### {rel}\n```\n{content}\n```")

        existing = self.existing_content()

        prompt = render_template(
            "standards",
            config_content="\n\n".join(config_parts) or "(No config files found)",
            existing_doc=existing or "(No existing document)",
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content)
