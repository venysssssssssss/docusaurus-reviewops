"""Tests for codebase analyzer and hasher."""

from __future__ import annotations

from pathlib import Path

from scripts.docgen.analyzer.codebase import (
    CodebaseSnapshot,
    analyze_codebase,
    build_context_for_prompt,
    read_file_content,
)
from scripts.docgen.analyzer.hasher import compute_hash, has_changed, save_hash


class TestAnalyzeCodebase:
    def test_scans_included_files(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(
            sample_codebase,
            include=["src/", "scripts/"],
            exclude=["__pycache__/"],
        )
        assert isinstance(snapshot, CodebaseSnapshot)
        assert len(snapshot.files) > 0
        assert snapshot.total_lines > 0

    def test_excludes_patterns(self, sample_codebase: Path) -> None:
        # Create a __pycache__ file
        cache_dir = sample_codebase / "src" / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "main.cpython-312.pyc").write_bytes(b"fake")

        snapshot = analyze_codebase(
            sample_codebase,
            include=["src/"],
            exclude=["__pycache__/"],
        )
        paths = [str(f.path) for f in snapshot.files]
        assert not any("__pycache__" in p for p in paths)

    def test_detects_languages(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(
            sample_codebase,
            include=["src/", "scripts/", ".github/"],
            exclude=[],
        )
        assert "python" in snapshot.languages
        assert "shell" in snapshot.languages or "yaml" in snapshot.languages

    def test_empty_include_matches_all(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(sample_codebase, include=[], exclude=[])
        assert len(snapshot.files) > 0

    def test_directory_tree_populated(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(sample_codebase, include=[], exclude=[])
        assert snapshot.directory_tree != ""


class TestReadFileContent:
    def test_reads_small_file(self, sample_codebase: Path) -> None:
        content = read_file_content(sample_codebase / "src" / "main.py")
        assert "def run" in content

    def test_truncates_large_file(self, tmp_path: Path) -> None:
        big_file = tmp_path / "big.py"
        big_file.write_text("\n".join(f"line {i}" for i in range(500)))
        content = read_file_content(big_file, max_lines=10)
        assert "truncated" in content

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert read_file_content(tmp_path / "nonexistent.py") == ""


class TestBuildContext:
    def test_produces_context_string(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(sample_codebase, include=["src/"], exclude=[])
        context = build_context_for_prompt(snapshot)
        assert "Codebase Summary" in context
        assert "Directory Tree" in context

    def test_respects_max_chars(self, sample_codebase: Path) -> None:
        snapshot = analyze_codebase(sample_codebase, include=[], exclude=[])
        context = build_context_for_prompt(snapshot, max_chars=200)
        assert len(context) < 1000  # some overhead for truncation message


class TestHasher:
    def test_same_files_same_hash(self, sample_codebase: Path) -> None:
        paths = [sample_codebase / "src" / "main.py"]
        h1 = compute_hash(paths)
        h2 = compute_hash(paths)
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("v1")
        h1 = compute_hash([f])
        f.write_text("v2")
        h2 = compute_hash([f])
        assert h1 != h2

    def test_has_changed_no_cache(self, tmp_path: Path) -> None:
        assert has_changed(tmp_path / "cache", "test", [tmp_path / "nonexistent"]) is True

    def test_save_and_check(self, tmp_path: Path) -> None:
        f = tmp_path / "file.py"
        f.write_text("content")
        cache_dir = tmp_path / "cache"

        save_hash(cache_dir, "gen", [f])
        assert has_changed(cache_dir, "gen", [f]) is False

        # Modify file
        f.write_text("changed")
        assert has_changed(cache_dir, "gen", [f]) is True
