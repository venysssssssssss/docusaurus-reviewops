"""Codebase analysis — file tree, language detection, context building."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".mdx": "markdown",
    ".css": "css",
    ".html": "html",
    ".sh": "shell",
    ".bash": "shell",
    ".toml": "toml",
    ".cfg": "config",
    ".ini": "config",
    ".sql": "sql",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".tf": "terraform",
    ".dockerfile": "docker",
}

_SPECIAL_NAMES: dict[str, str] = {
    "Makefile": "makefile",
    "Dockerfile": "docker",
    "Jenkinsfile": "groovy",
    ".gitignore": "gitignore",
    ".dockerignore": "gitignore",
}


@dataclass(frozen=True)
class FileInfo:
    """Metadata about a single source file."""

    path: Path
    language: str
    size_bytes: int
    line_count: int


@dataclass(frozen=True)
class CodebaseSnapshot:
    """Analysis result for the entire codebase."""

    root: Path
    files: list[FileInfo]
    languages: dict[str, int] = field(default_factory=dict)
    total_lines: int = 0
    directory_tree: str = ""


def _detect_language(path: Path) -> str:
    """Detect programming language from file extension or name."""
    name = path.name
    if name in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[name]
    suffix = path.suffix.lower()
    return _EXTENSIONS.get(suffix, "unknown")


def _count_lines(path: Path) -> int:
    """Count lines in a text file, return 0 on error."""
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def _is_excluded(path: Path, root: Path, exclude_patterns: list[str]) -> bool:
    """Check if path matches any exclude pattern."""
    relative = str(path.relative_to(root))
    for pattern in exclude_patterns:
        if pattern.endswith("/"):
            if relative.startswith(pattern) or f"/{pattern}" in f"/{relative}":
                return True
        elif fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
    return False


def _is_included(path: Path, root: Path, include_patterns: list[str]) -> bool:
    """Check if path falls under any include pattern."""
    if not include_patterns:
        return True
    relative = str(path.relative_to(root))
    return any(relative.startswith(pattern) for pattern in include_patterns)


def _build_tree(root: Path, files: list[FileInfo], max_depth: int = 4) -> str:
    """Build a formatted directory tree string."""
    dirs: dict[str, list[str]] = {}
    for fi in files:
        rel = fi.path.relative_to(root)
        parts = rel.parts
        if len(parts) > max_depth:
            continue
        parent = str(Path(*parts[:-1])) if len(parts) > 1 else "."
        dirs.setdefault(parent, []).append(parts[-1])

    lines: list[str] = []
    for dir_path in sorted(dirs.keys()):
        if dir_path != ".":
            lines.append(f"{dir_path}/")
        for fname in sorted(dirs[dir_path])[:20]:  # cap per directory
            prefix = "  " if dir_path == "." else "  " * (dir_path.count("/") + 2)
            lines.append(f"{prefix}{fname}")
        remaining = len(dirs[dir_path]) - 20
        if remaining > 0:
            prefix = "  " if dir_path == "." else "  " * (dir_path.count("/") + 2)
            lines.append(f"{prefix}... and {remaining} more files")

    return "\n".join(lines)


def analyze_codebase(
    root: Path,
    include: list[str],
    exclude: list[str],
) -> CodebaseSnapshot:
    """Walk the file tree, classify files, build summary."""
    files: list[FileInfo] = []
    languages: dict[str, int] = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path, root, exclude):
            continue
        if not _is_included(path, root, include):
            continue

        lang = _detect_language(path)
        line_count = _count_lines(path)

        fi = FileInfo(
            path=path,
            language=lang,
            size_bytes=path.stat().st_size,
            line_count=line_count,
        )
        files.append(fi)
        languages[lang] = languages.get(lang, 0) + 1

    total_lines = sum(f.line_count for f in files)
    tree = _build_tree(root, files)

    return CodebaseSnapshot(
        root=root,
        files=files,
        languages=languages,
        total_lines=total_lines,
        directory_tree=tree,
    )


def read_file_content(path: Path, max_lines: int = 200) -> str:
    """Read file content, truncated for prompt context."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""

    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n\n... ({len(lines) - max_lines} lines truncated)"
    return "\n".join(lines)


def build_context_for_prompt(
    snapshot: CodebaseSnapshot,
    focus_paths: list[Path] | None = None,
    max_chars: int = 32000,
) -> tuple[str, int]:
    """Build a condensed text representation of the codebase for LLM context.

    Returns:
        A tuple of (context_string, omitted_file_count). ``omitted_file_count``
        is the number of files that were not included due to the ``max_chars``
        limit. Callers should surface this to users so they know analysis was
        partial.
    """
    sections: list[str] = []

    # Summary
    sections.append("## Codebase Summary\n")
    sections.append(f"Root: {snapshot.root.name}")
    sections.append(f"Files: {len(snapshot.files)}")
    sections.append(f"Total lines: {snapshot.total_lines}")
    sections.append(f"Languages: {', '.join(f'{k} ({v})' for k, v in sorted(snapshot.languages.items(), key=lambda x: -x[1]))}")
    sections.append("")

    # Directory tree
    sections.append(f"## Directory Tree\n```\n{snapshot.directory_tree}\n```\n")

    # Key file contents
    target_files = focus_paths or [f.path for f in snapshot.files]
    # Prioritize config/entry files
    priority_names = {
        "Makefile", "pyproject.toml", "package.json", "docusaurus.config.ts",
        "__init__.py", "main.py", "app.py", "index.ts", "index.md",
    }

    prioritized = sorted(
        target_files,
        key=lambda p: (0 if p.name in priority_names else 1, str(p)),
    )

    current_chars = sum(len(s) for s in sections)
    sections.append("## Key Files\n")

    omitted = 0
    for idx, path in enumerate(prioritized):
        if current_chars >= max_chars:
            omitted = len(prioritized) - idx
            sections.append(f"\n... ({omitted} files omitted — context limit {max_chars} chars reached)")
            break

        content = read_file_content(path, max_lines=100)
        if not content:
            continue

        header = f"### {path.relative_to(snapshot.root)}\n```\n{content}\n```\n"
        current_chars += len(header)
        sections.append(header)

    return "\n".join(sections), omitted
