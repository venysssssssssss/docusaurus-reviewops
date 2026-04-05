"""OpenAPI description enricher — adds LLM-generated descriptions to endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot
    from scripts.docgen.config import DocgenConfig
    from scripts.docgen.providers.base import LLMProvider, LLMResponse

_OPENAPI_PATH = Path("docs-site/openapi/openapi.json")

_SYSTEM_PROMPT = (
    "You are an API documentation writer. Enrich OpenAPI endpoint descriptions "
    "with clear, concise explanations. Output ONLY the description text, no markdown."
)

_ENRICH_PROMPT = """\
Write a clear, concise description (1-3 sentences) for this API endpoint:

Method: {method}
Path: {path}
Operation ID: {operation_id}
Current description: {current_description}

Parameters: {parameters}

Output ONLY the description text, no formatting or markdown.
"""


class APIEnricherGenerator(DocGenerator):
    """Enrich OpenAPI schema with LLM-generated endpoint descriptions."""

    def __init__(self, provider: LLMProvider, config: DocgenConfig) -> None:
        super().__init__(provider, config)
        self._schema: dict | None = None

    @property
    def name(self) -> str:
        return "api_enricher"

    @property
    def output_filename(self) -> str:
        return "../../docs-site/openapi/openapi.json"

    def output_path(self) -> Path:
        return _OPENAPI_PATH

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        paths: list[Path] = []
        if _OPENAPI_PATH.exists():
            paths.append(_OPENAPI_PATH)
        # Also watch source files that might define API routes
        for f in snapshot.files:
            if f.language == "python" and any(
                kw in f.path.name for kw in ("route", "api", "endpoint", "view")
            ):
                paths.append(f.path)
        return paths

    def _load_schema(self) -> dict | None:
        if not _OPENAPI_PATH.exists():
            return None
        try:
            schema = json.loads(_OPENAPI_PATH.read_text(encoding="utf-8"))
            # Skip placeholder schemas
            if schema.get("info", {}).get("version") == "0.0.0":
                return None
            return schema
        except (json.JSONDecodeError, OSError):
            return None

    def generate(self, snapshot: CodebaseSnapshot) -> tuple[str, LLMResponse | None]:
        schema = self._load_schema()
        if schema is None:
            return "", None  # No valid schema to enrich

        paths = schema.get("paths", {})
        enriched = False
        last_response: LLMResponse | None = None

        for path_str, methods in paths.items():
            for method, operation in methods.items():
                if method.startswith("x-") or not isinstance(operation, dict):
                    continue

                description = operation.get("description", "")
                summary = operation.get("summary", "")

                # Only enrich if description is empty or very short
                if description and len(description) > 20:
                    continue

                params = operation.get("parameters", [])
                params_str = json.dumps(params, indent=2) if params else "None"

                prompt = _ENRICH_PROMPT.format(
                    method=method.upper(),
                    path=path_str,
                    operation_id=operation.get("operationId", "N/A"),
                    current_description=description or summary or "None",
                    parameters=params_str,
                )

                last_response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
                new_desc = sanitize_llm_output(last_response.content).strip()

                if new_desc:
                    operation["description"] = new_desc
                    enriched = True

        if not enriched:
            return "", None

        return json.dumps(schema, indent=2, ensure_ascii=False), last_response
