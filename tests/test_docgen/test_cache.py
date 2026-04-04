"""Tests for cache store."""

from __future__ import annotations

from pathlib import Path

from scripts.docgen.cache.store import CacheStore, GenerationMeta


class TestCacheStore:
    def test_is_stale_no_cache(self, tmp_path: Path) -> None:
        store = CacheStore(tmp_path / "cache")
        assert store.is_stale("test", "abc123") is True

    def test_save_and_check(self, tmp_path: Path) -> None:
        store = CacheStore(tmp_path / "cache")
        meta = GenerationMeta(
            generator="test",
            timestamp="2026-04-04T00:00:00Z",
            provider="mock",
            model="mock-model",
        )
        store.save("test", "abc123", meta)
        assert store.is_stale("test", "abc123") is False
        assert store.is_stale("test", "different") is True

    def test_get_meta(self, tmp_path: Path) -> None:
        store = CacheStore(tmp_path / "cache")
        meta = GenerationMeta(
            generator="arch",
            timestamp="2026-04-04T00:00:00Z",
            provider="anthropic",
            model="claude-sonnet",
            input_tokens=100,
            output_tokens=200,
            estimated_cost_usd=0.05,
            duration_ms=500,
        )
        store.save("arch", "hash1", meta)
        loaded = store.get_meta("arch")
        assert loaded is not None
        assert loaded.generator == "arch"
        assert loaded.input_tokens == 100

    def test_get_meta_missing(self, tmp_path: Path) -> None:
        store = CacheStore(tmp_path / "cache")
        assert store.get_meta("nonexistent") is None

    def test_summary(self, tmp_path: Path) -> None:
        store = CacheStore(tmp_path / "cache")
        for name in ("a", "b"):
            meta = GenerationMeta(
                generator=name, timestamp="t", provider="mock", model="m"
            )
            store.save(name, f"hash_{name}", meta)
        s = store.summary()
        assert "a" in s
        assert "b" in s

    def test_clear(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "cache"
        store = CacheStore(cache_dir)
        meta = GenerationMeta(generator="x", timestamp="t", provider="p", model="m")
        store.save("x", "h", meta)
        assert cache_dir.exists()
        store.clear()
        assert not cache_dir.exists()
