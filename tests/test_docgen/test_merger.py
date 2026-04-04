"""Tests for document merger."""

from __future__ import annotations

from scripts.docgen.output.merger import merge_docs


class TestMergeDocs:
    def test_overwrite_replaces(self) -> None:
        result = merge_docs("old content", "new content", "overwrite")
        assert result == "new content"

    def test_append_concatenates(self) -> None:
        result = merge_docs("old", "new", "append")
        assert "old" in result
        assert "new" in result
        assert result.index("old") < result.index("new")

    def test_preserve_keeps_existing_sections(self) -> None:
        existing = "---\nid: test\n---\n\n## Section A\n\nContent A\n"
        generated = "---\nid: test\n---\n\n## Section A\n\nNew A\n\n## Section B\n\nContent B\n"
        result = merge_docs(existing, generated, "preserve")
        assert "Content A" in result  # existing preserved
        assert "Section B" in result  # new section added

    def test_preserve_empty_existing_uses_generated(self) -> None:
        result = merge_docs("", "# Generated", "preserve")
        assert result == "# Generated"

    def test_preserve_no_new_sections(self) -> None:
        existing = "---\nid: test\n---\n\n## Section A\n\nContent\n"
        generated = "---\nid: test\n---\n\n## Section A\n\nDifferent content\n"
        result = merge_docs(existing, generated, "preserve")
        assert result == existing  # nothing new to add
