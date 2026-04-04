"""Deploy runbook document generator."""

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
    "You are a senior DevOps engineer. Generate a practical deploy runbook "
    "in valid Docusaurus-compatible Markdown. Focus on actionable steps."
)


class RunbookGenerator(DocGenerator):
    """Generate deploy runbook from CI/CD workflows and Makefile."""

    @property
    def name(self) -> str:
        return "runbook"

    @property
    def output_filename(self) -> str:
        return "runbooks/deploy.md"

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        relevant: list[Path] = []
        for f in snapshot.files:
            rel = str(f.path.relative_to(snapshot.root))
            if (
                rel.startswith(".github/workflows/")
                or f.path.name in ("Makefile", "Dockerfile", "docker-compose.yml")
                or rel.startswith("scripts/")
            ):
                relevant.append(f.path)
        return relevant

    def generate(self, snapshot: CodebaseSnapshot) -> str:
        # Collect workflow contents
        workflow_parts: list[str] = []
        makefile_content = ""

        for path in self.relevant_paths(snapshot):
            rel = str(path.relative_to(snapshot.root))
            content = read_file_content(path)
            if not content:
                continue

            if rel.startswith(".github/workflows/"):
                workflow_parts.append(f"### {rel}\n```yaml\n{content}\n```")
            elif path.name == "Makefile":
                makefile_content = content

        existing = self.existing_content()

        prompt = render_template(
            "runbook",
            workflows_content="\n\n".join(workflow_parts) or "(No workflows found)",
            makefile_content=makefile_content or "(No Makefile found)",
            existing_doc=existing or "(No existing document)",
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content)
