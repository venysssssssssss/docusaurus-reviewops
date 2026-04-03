"""Smoke tests for local Docusaurus theme overrides."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_SITE = REPO_ROOT / "docs-site"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_api_explorer_override_avoids_theme_runtime_modules() -> None:
    override_path = DOCS_SITE / "src" / "theme" / "ApiExplorer" / "index.js"
    source = read_text(override_path)

    assert "API Explorer Preview" in source
    assert "@theme/ApiExplorer/SecuritySchemes" not in source
    assert "@theme/ApiExplorer/Request" not in source
    assert "@theme/ApiExplorer/Response" not in source
    assert "@theme/ApiExplorer/CodeSnippets" not in source


def test_api_code_block_override_uses_stable_docusaurus_code_block() -> None:
    override_path = (
        DOCS_SITE / "src" / "theme" / "ApiExplorer" / "ApiCodeBlock" / "index.js"
    )
    source = read_text(override_path)

    assert 'import CodeBlock from "@theme/CodeBlock";' in source
    assert "function maybeStringifyChildren" in source


def test_docusaurus_config_uses_markdown_hook_for_broken_links() -> None:
    config_path = DOCS_SITE / "docusaurus.config.ts"
    source = read_text(config_path)

    assert "markdown:" in source
    assert "onBrokenMarkdownLinks: \"throw\"" in source
    assert "\n  onBrokenMarkdownLinks: " not in source
