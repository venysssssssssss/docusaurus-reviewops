"""File-based cache store for generation metadata and hashes."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GenerationMeta:
    """Metadata from a single generation run."""

    generator: str
    timestamp: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    duration_ms: int = 0


class CacheStore:
    """Manage generation cache: hashes and metadata."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir

    def _hash_path(self, generator_name: str) -> Path:
        return self._dir / f"{generator_name}.hash"

    def _meta_path(self, generator_name: str) -> Path:
        return self._dir / f"{generator_name}.meta.json"

    def is_stale(self, generator_name: str, input_hash: str) -> bool:
        """Return True if cache miss (hash differs or doesn't exist)."""
        hp = self._hash_path(generator_name)
        if not hp.exists():
            return True
        return hp.read_text(encoding="utf-8").strip() != input_hash

    def save(
        self,
        generator_name: str,
        input_hash: str,
        meta: GenerationMeta,
    ) -> None:
        """Persist hash and metadata to cache."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._hash_path(generator_name).write_text(input_hash, encoding="utf-8")
        self._meta_path(generator_name).write_text(
            json.dumps(asdict(meta), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_meta(self, generator_name: str) -> GenerationMeta | None:
        """Load metadata for a generator, or None if not cached."""
        mp = self._meta_path(generator_name)
        if not mp.exists():
            return None
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
            return GenerationMeta(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def summary(self) -> dict[str, GenerationMeta]:
        """Load all cached metadata."""
        result: dict[str, GenerationMeta] = {}
        if not self._dir.exists():
            return result
        for path in self._dir.glob("*.meta.json"):
            name = path.stem.replace(".meta", "")
            meta = self.get_meta(name)
            if meta:
                result[name] = meta
        return result

    def clear(self) -> None:
        """Remove all cached data."""
        if self._dir.exists():
            shutil.rmtree(self._dir)
