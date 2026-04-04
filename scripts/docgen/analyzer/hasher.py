"""Content hashing for incremental generation."""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_hash(paths: list[Path]) -> str:
    """SHA256 of sorted file contents. Used for incremental generation."""
    h = hashlib.sha256()
    for path in sorted(paths):
        try:
            h.update(str(path).encode("utf-8"))
            h.update(path.read_bytes())
        except OSError:
            h.update(b"<missing>")
    return h.hexdigest()


def _hash_file(cache_dir: Path, generator_name: str) -> Path:
    """Return path to the hash file for a generator."""
    return cache_dir / f"{generator_name}.hash"


def has_changed(cache_dir: Path, generator_name: str, paths: list[Path]) -> bool:
    """Compare current hash against cached hash.

    Returns True if changed or no cache exists.
    """
    hf = _hash_file(cache_dir, generator_name)
    if not hf.exists():
        return True
    cached = hf.read_text(encoding="utf-8").strip()
    current = compute_hash(paths)
    return cached != current


def save_hash(cache_dir: Path, generator_name: str, paths: list[Path]) -> None:
    """Persist current hash to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    hf = _hash_file(cache_dir, generator_name)
    hf.write_text(compute_hash(paths), encoding="utf-8")
