"""Git history analysis — commits, tags, significant changes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommitInfo:
    """Parsed git commit."""

    sha: str
    message: str
    author: str
    date: str
    files_changed: int
    insertions: int
    deletions: int


def _run_git(args: list[str]) -> str:
    """Run a git command and return stdout. Returns empty string on error."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_commits(since_tag: str | None = None, limit: int = 100) -> list[CommitInfo]:
    """Parse git log into structured commits."""
    range_spec = f"{since_tag}..HEAD" if since_tag else f"HEAD~{limit}..HEAD"
    # Format: sha|message|author|date
    raw = _run_git([
        "log", range_spec, f"--max-count={limit}",
        "--format=%H|%s|%an|%aI",
        "--shortstat",
    ])
    if not raw:
        return []

    commits: list[CommitInfo] = []
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "|" not in line:
            i += 1
            continue

        parts = line.split("|", 3)
        if len(parts) < 4:
            i += 1
            continue

        sha, message, author, date = parts
        files_changed = insertions = deletions = 0

        # Next non-empty line might be shortstat
        if i + 1 < len(lines):
            stat_line = lines[i + 1].strip()
            if "changed" in stat_line:
                for token in stat_line.split(","):
                    token = token.strip()
                    if "file" in token:
                        files_changed = int(token.split()[0])
                    elif "insertion" in token:
                        insertions = int(token.split()[0])
                    elif "deletion" in token:
                        deletions = int(token.split()[0])
                i += 1

        commits.append(CommitInfo(
            sha=sha,
            message=message,
            author=author,
            date=date,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        ))
        i += 1

    return commits


def get_significant_changes(
    commits: list[CommitInfo],
    threshold: int = 10,
) -> list[CommitInfo]:
    """Filter commits that represent significant architectural changes."""
    return [c for c in commits if c.files_changed >= threshold]


def get_tag_history() -> list[tuple[str, str]]:
    """Return list of (tag_name, date) sorted by date descending."""
    raw = _run_git(["tag", "-l", "--sort=-creatordate", "--format=%(refname:short)|%(creatordate:short)"])
    if not raw:
        return []
    results: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if "|" in line:
            tag, date = line.split("|", 1)
            results.append((tag.strip(), date.strip()))
    return results


def get_latest_tag() -> str | None:
    """Return the most recent tag, or None if no tags exist."""
    tags = get_tag_history()
    return tags[0][0] if tags else None
