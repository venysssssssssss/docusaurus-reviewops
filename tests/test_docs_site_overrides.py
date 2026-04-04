"""Smoke tests for local Docusaurus theme overrides and portal quality."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_SITE = REPO_ROOT / "docs-site"
DOCS_DIR = DOCS_SITE / "docs"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Theme swizzle tests
# ---------------------------------------------------------------------------


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


def test_schema_tabs_override_is_esm() -> None:
    override_path = DOCS_SITE / "src" / "theme" / "SchemaTabs" / "index.js"
    source = read_text(override_path)

    assert "export default function SchemaTabs" in source
    assert "sanitizeTabsChildren" in source
    assert "useTabs" in source
    assert "exports" not in source.split("*/")[-1]


def test_api_logo_override_is_esm() -> None:
    override_path = DOCS_SITE / "src" / "theme" / "ApiLogo" / "index.js"
    source = read_text(override_path)

    assert "export default function ApiLogo" in source
    assert "useColorMode" in source
    assert "exports" not in source.split("*/")[-1]


def test_export_override_is_esm() -> None:
    override_path = (
        DOCS_SITE / "src" / "theme" / "ApiExplorer" / "Export" / "index.js"
    )
    source = read_text(override_path)

    assert "export default function Export" in source
    assert "exports" not in source.split("*/")[-1]


# ---------------------------------------------------------------------------
# Webpack plugin tests
# ---------------------------------------------------------------------------


def test_webpack_plugin_applies_cjs_rule_to_both_client_and_server() -> None:
    plugin_path = DOCS_SITE / "src" / "webpack-fallback-plugin.js"
    source = read_text(plugin_path)

    assert "config.module.rules.unshift" in source
    assert 'type: "javascript/auto"' in source
    assert "if (isServer) return" not in source


def test_webpack_plugin_has_openapi_split_chunks() -> None:
    plugin_path = DOCS_SITE / "src" / "webpack-fallback-plugin.js"
    source = read_text(plugin_path)

    assert "openapiVendor" in source
    assert "openapi-vendor" in source


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


def test_docusaurus_config_uses_markdown_hook_for_broken_links() -> None:
    config_path = DOCS_SITE / "docusaurus.config.ts"
    source = read_text(config_path)

    assert "markdown:" in source
    assert 'onBrokenMarkdownLinks: "throw"' in source
    assert "\n  onBrokenMarkdownLinks: " not in source


def test_config_has_mermaid_theme() -> None:
    source = read_text(DOCS_SITE / "docusaurus.config.ts")

    assert "mermaid: true" in source
    assert "@docusaurus/theme-mermaid" in source


def test_config_has_search_plugin() -> None:
    source = read_text(DOCS_SITE / "docusaurus.config.ts")

    assert "docusaurus-search-local" in source


def test_config_has_announcement_bar() -> None:
    source = read_text(DOCS_SITE / "docusaurus.config.ts")

    assert "announcementBar" in source
    assert "isCloseable: true" in source


def test_config_has_color_mode_respect() -> None:
    source = read_text(DOCS_SITE / "docusaurus.config.ts")

    assert "respectPrefersColorScheme: true" in source


# ---------------------------------------------------------------------------
# Static asset tests
# ---------------------------------------------------------------------------


def test_favicon_svg_exists() -> None:
    assert (DOCS_SITE / "static" / "img" / "favicon.svg").exists()


def test_social_card_exists() -> None:
    assert (DOCS_SITE / "static" / "img" / "social-card.png").exists()


def test_robots_txt_exists() -> None:
    path = DOCS_SITE / "static" / "robots.txt"
    assert path.exists()
    content = read_text(path)
    assert "Sitemap:" in content


# ---------------------------------------------------------------------------
# Custom 404 page test
# ---------------------------------------------------------------------------


def test_custom_404_page_exists() -> None:
    path = DOCS_SITE / "src" / "pages" / "404.tsx"
    assert path.exists()
    source = read_text(path)
    assert "404" in source
    assert "Layout" in source


# ---------------------------------------------------------------------------
# Documentation quality tests
# ---------------------------------------------------------------------------

MAIN_DOCS = [
    DOCS_DIR / "index.md",
    DOCS_DIR / "architecture" / "overview.md",
    DOCS_DIR / "standards" / "coding-standards.md",
    DOCS_DIR / "runbooks" / "deploy.md",
    DOCS_DIR / "adr" / "001-docusaurus-reviewops.md",
]


def test_all_docs_have_description_in_frontmatter() -> None:
    for doc in MAIN_DOCS:
        source = read_text(doc)
        assert "description:" in source, f"{doc.name} missing description"


def test_all_docs_have_keywords_in_frontmatter() -> None:
    for doc in MAIN_DOCS:
        source = read_text(doc)
        assert "keywords:" in source, f"{doc.name} missing keywords"


def test_docs_use_admonitions() -> None:
    admonition_count = 0
    for doc in MAIN_DOCS:
        source = read_text(doc)
        if ":::" in source:
            admonition_count += 1
    assert admonition_count >= 4, (
        f"Expected >= 4 docs with admonitions, found {admonition_count}"
    )


def test_docs_have_cross_links() -> None:
    cross_link_count = 0
    for doc in MAIN_DOCS:
        source = read_text(doc)
        if "Veja tambem" in source:
            cross_link_count += 1
    assert cross_link_count >= 4, (
        f"Expected >= 4 docs with cross-links, found {cross_link_count}"
    )


def test_docs_use_mermaid_diagrams() -> None:
    mermaid_count = 0
    for doc in MAIN_DOCS:
        source = read_text(doc)
        if "```mermaid" in source:
            mermaid_count += 1
    assert mermaid_count >= 2, (
        f"Expected >= 2 docs with mermaid diagrams, found {mermaid_count}"
    )


# ---------------------------------------------------------------------------
# Category ordering tests
# ---------------------------------------------------------------------------

CATEGORY_DIRS = ["architecture", "standards", "runbooks", "adr", "api"]


def test_all_doc_dirs_have_category_json() -> None:
    for dirname in CATEGORY_DIRS:
        cat_file = DOCS_DIR / dirname / "_category_.json"
        assert cat_file.exists(), f"{dirname}/_category_.json missing"
