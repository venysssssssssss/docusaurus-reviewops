"""Atomic file writer with backup support."""

from __future__ import annotations

import shutil
from pathlib import Path


def write_doc(path: Path, content: str, backup: bool = True) -> None:
    """Write content to path.

    If backup=True and file exists, create a .bak copy first.
    Creates parent directories as needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and backup:
        bak_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak_path)

    path.write_text(content, encoding="utf-8")
