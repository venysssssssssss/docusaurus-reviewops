"""Tests for output formatter."""

from __future__ import annotations

from scripts.docgen.output.formatter import (
    DocMetadata,
    inject_frontmatter,
    parse_frontmatter,
    sanitize_llm_output,
    validate_docusaurus_markdown,
)


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        content = "---\nid: test\ntitle: Test\n---\n\n# Body"
        meta, body = parse_frontmatter(content)
        assert meta["id"] == "test"
        assert meta["title"] == "Test"
        assert body.strip() == "# Body"

    def test_no_frontmatter(self) -> None:
        content = "# No frontmatter here"
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert body == content

    def test_invalid_yaml(self) -> None:
        content = "---\n{{invalid\n---\n\nbody"
        meta, body = parse_frontmatter(content)
        assert meta == {}


class TestInjectFrontmatter:
    def test_injects_correct_yaml(self) -> None:
        metadata = DocMetadata(
            id="test",
            title="Test Doc",
            sidebar_label="Test",
            sidebar_position=1,
            description="A test document.",
            keywords=["test", "doc"],
        )
        result = inject_frontmatter("# Content", metadata)
        assert result.startswith("---\n")
        assert "id: test" in result
        assert "title: Test Doc" in result
        assert "# Content" in result


class TestSanitizeLlmOutput:
    def test_strips_markdown_fence(self) -> None:
        raw = "```markdown\n# Hello\n```"
        assert sanitize_llm_output(raw) == "# Hello"

    def test_strips_md_fence(self) -> None:
        raw = "```md\n# Hello\n```"
        assert sanitize_llm_output(raw) == "# Hello"

    def test_preserves_mermaid_blocks(self) -> None:
        raw = "```mermaid\ngraph LR\n  A --> B\n```"
        result = sanitize_llm_output(raw)
        assert "```mermaid" in result

    def test_strips_whitespace(self) -> None:
        raw = "  \n\n# Hello  \n\n  "
        assert sanitize_llm_output(raw) == "# Hello"


class TestValidateDocusaurusMarkdown:
    def test_valid_doc(self) -> None:
        doc = "---\nid: x\ntitle: X\ndescription: Y\n---\n\n# Content"
        issues = validate_docusaurus_markdown(doc)
        assert issues == []

    def test_missing_frontmatter(self) -> None:
        issues = validate_docusaurus_markdown("# No frontmatter")
        assert any("Missing YAML frontmatter" in i for i in issues)

    def test_missing_required_field(self) -> None:
        doc = "---\nid: x\n---\n\n# Content"
        issues = validate_docusaurus_markdown(doc)
        assert any("title" in i for i in issues)

    def test_detects_todo(self) -> None:
        doc = "---\nid: x\ntitle: X\ndescription: Y\n---\n\nTODO: fix this"
        issues = validate_docusaurus_markdown(doc)
        assert any("TODO" in i for i in issues)

    def test_unclosed_admonition(self) -> None:
        doc = "---\nid: x\ntitle: X\ndescription: Y\n---\n\n:::tip\nContent"
        issues = validate_docusaurus_markdown(doc)
        assert any("admonition" in i.lower() for i in issues)
