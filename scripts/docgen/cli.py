"""CLI entry point for docgen — LLM-powered documentation generator."""

from __future__ import annotations

import argparse
import datetime
import difflib
import itertools
import logging
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from scripts.docgen.analyzer.codebase import analyze_codebase
from scripts.docgen.analyzer.hasher import compute_hash, save_hash
from scripts.docgen.cache.store import CacheStore, GenerationMeta
from scripts.docgen.config import DocgenConfig, load_config
from scripts.docgen.generators.adr import ADRGenerator
from scripts.docgen.generators.api_enricher import APIEnricherGenerator
from scripts.docgen.generators.architecture import ArchitectureGenerator
from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.generators.changelog import ChangelogGenerator
from scripts.docgen.generators.runbook import RunbookGenerator
from scripts.docgen.generators.standards import StandardsGenerator
from scripts.docgen.output.merger import merge_docs
from scripts.docgen.output.writer import write_doc
from scripts.docgen.providers import create_provider
from scripts.docgen.providers.base import LLMProviderError, estimate_cost

logger = logging.getLogger("docgen")

_SPINNER_CHARS = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")


@contextmanager
def _spinner(label: str) -> Generator[None, None, None]:
    """TTY-aware spinner context manager.

    Shows an animated spinner on stderr when connected to a TTY.
    Falls back to a plain "generating..." log line in non-TTY environments
    (CI, pipes) to avoid polluting captured output.
    """
    if not sys.stderr.isatty():
        logger.info("  [%s] generating...", label)
        yield
        return

    stop_event = threading.Event()

    def _spin() -> None:
        while not stop_event.is_set():
            sys.stderr.write(f"\r  {next(_SPINNER_CHARS)} {label} ...")
            sys.stderr.flush()
            time.sleep(0.1)

    thread = threading.Thread(target=_spin, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join()
        sys.stderr.write("\r")  # clear spinner line
        sys.stderr.flush()

_GENERATORS: dict[str, type[DocGenerator]] = {
    "architecture": ArchitectureGenerator,
    "standards": StandardsGenerator,
    "runbook": RunbookGenerator,
    "adr": ADRGenerator,
    "changelog": ChangelogGenerator,
    "api_enricher": APIEnricherGenerator,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docgen",
        description="LLM-powered documentation generator for docusaurus-reviewops.",
    )
    parser.add_argument(
        "--config", type=Path, default=None,
        help="Config file path (default: .docgen.yml)",
    )
    parser.add_argument(
        "--provider", choices=["ollama", "anthropic", "openai", "claude-code", "mock"],
        help="Override LLM provider from config",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Override model from config",
    )
    parser.add_argument(
        "--generators", type=str, default=None,
        help="Comma-separated list of generators (default: all enabled in config)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Override output directory",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Force regeneration, ignore cache",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show unified diff of what would change without writing files",
    )
    parser.add_argument(
        "--diff-only", action="store_true",
        help="Like --dry-run but exits with code 1 if any file would change (useful in CI)",
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Generate to stdout instead of files",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )
    return parser


def _resolve_config(args: argparse.Namespace) -> DocgenConfig:
    """Build config from file + CLI overrides."""
    overrides: dict[str, object] = {}
    if args.provider:
        overrides["provider"] = args.provider
    if args.model:
        overrides["model"] = args.model
    if args.output_dir:
        overrides.setdefault("output", {})
        overrides["output"]["docs_dir"] = str(args.output_dir)  # type: ignore[index]
    if args.no_cache:
        overrides.setdefault("cache", {})
        overrides["cache"]["enabled"] = False  # type: ignore[index]

    return load_config(config_path=args.config, overrides=overrides)


def _select_generators(
    config: DocgenConfig,
    generator_filter: str | None,
) -> list[str]:
    """Determine which generators to run."""
    if generator_filter:
        return [g.strip() for g in generator_filter.split(",") if g.strip() in _GENERATORS]
    return [name for name, enabled in config.generators.items() if enabled and name in _GENERATORS]


def _show_diff(output_path: Path, new_content: str) -> bool:
    """Print a unified diff between existing and new content.

    Returns True if there are any differences.
    """
    existing_lines = output_path.read_text(encoding="utf-8").splitlines(keepends=True) if output_path.exists() else []
    new_lines = new_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        existing_lines,
        new_lines,
        fromfile=f"a/{output_path}",
        tofile=f"b/{output_path}",
        lineterm="",
    ))
    if diff:
        print("\n" + "".join(diff))
        return True
    print(f"  (no changes: {output_path})")
    return False


def _run(args: argparse.Namespace) -> int:
    """Main execution logic."""
    config = _resolve_config(args)
    provider = create_provider(config.provider)

    if not provider.is_available():
        logger.error(
            "LLM provider '%s' is not available.\n"
            "  - For Ollama: start with 'ollama serve' and pull a model\n"
            "  - For Anthropic: set ANTHROPIC_API_KEY environment variable\n"
            "  - For OpenAI: set OPENAI_API_KEY environment variable\n"
            "  - For Claude Code: install the claude CLI",
            config.provider.name,
        )
        return 1

    logger.info("Provider: %s (model: %s)", provider.name, config.provider.model or "default")

    # Analyze codebase
    root = Path.cwd()
    snapshot = analyze_codebase(root, config.include_paths, config.exclude_paths)
    logger.info(
        "Codebase: %d files, %d lines, languages: %s",
        len(snapshot.files),
        snapshot.total_lines,
        ", ".join(f"{k}({v})" for k, v in sorted(snapshot.languages.items(), key=lambda x: -x[1])[:5]),
    )

    # Select generators
    gen_names = _select_generators(config, args.generators)
    if not gen_names:
        logger.warning("No generators selected. Check .docgen.yml or --generators flag.")
        return 0

    cache = CacheStore(config.cache_dir)
    results: list[tuple[str, str, float | None, bool]] = []  # (name, status, cost, skipped)

    for gen_name in gen_names:
        gen_cls = _GENERATORS[gen_name]
        gen = gen_cls(provider, config)

        # Cache check
        if not args.no_cache and config.cache_enabled:
            relevant = gen.relevant_paths(snapshot)
            current_hash = compute_hash(relevant)
            if not cache.is_stale(gen_name, current_hash):
                logger.info("  [%s] cached, skipping", gen_name)
                results.append((gen_name, "cached", None, True))
                continue

        if args.dry_run or args.diff_only:
            try:
                t_start = time.monotonic()
                with _spinner(gen_name):
                    content, llm_response = gen.generate(snapshot)
                elapsed = time.monotonic() - t_start
            except LLMProviderError as exc:
                logger.error("  [%s] provider error: %s", gen_name, exc)
                results.append((gen_name, f"error: {exc}", None, False))
                continue

            if not content:
                results.append((gen_name, "empty", None, True))
                continue

            existing = gen.existing_content()
            if existing and config.merge_strategy != "overwrite":
                content = merge_docs(existing, content, config.merge_strategy)

            cost = estimate_cost(llm_response) if llm_response is not None else None
            print(f"\n--- diff: {gen.output_path()} ---")
            has_diff = _show_diff(gen.output_path(), content)
            status = "would-change" if has_diff else "no-change"
            results.append((gen_name, status, cost, False))
            continue

        try:
            t_start = time.monotonic()
            with _spinner(gen_name):
                content, llm_response = gen.generate(snapshot)
            elapsed = time.monotonic() - t_start
            tokens = (
                (llm_response.input_tokens or 0) + (llm_response.output_tokens or 0)
                if llm_response else 0
            )
            logger.info(
                "  [%s] done (%d tokens, %.1fs)", gen_name, tokens, elapsed
            )
        except LLMProviderError as exc:
            logger.error("  [%s] provider error: %s", gen_name, exc)
            results.append((gen_name, f"error: {exc}", None, False))
            continue

        if not content:
            logger.info("  [%s] no content generated (nothing to document)", gen_name)
            results.append((gen_name, "empty", None, True))
            continue

        # Merge with existing
        existing = gen.existing_content()
        if existing and config.merge_strategy != "overwrite":
            content = merge_docs(existing, content, config.merge_strategy)

        cost = estimate_cost(llm_response) if llm_response is not None else None

        if args.preview:
            print(f"\n{'=' * 60}")
            print(f"# {gen_name} -> {gen.output_path()}")
            print(f"{'=' * 60}\n")
            print(content)
            results.append((gen_name, "preview", cost, False))
        else:
            write_doc(gen.output_path(), content, backup=config.backup)
            logger.info("  [%s] written -> %s", gen_name, gen.output_path())

            # Save cache
            if config.cache_enabled:
                relevant = gen.relevant_paths(snapshot)
                current_hash = compute_hash(relevant)
                save_hash(config.cache_dir, gen_name, relevant)
                meta = GenerationMeta(
                    generator=gen_name,
                    timestamp=datetime.datetime.now(tz=datetime.UTC).isoformat(),
                    provider=provider.name,
                    model=config.provider.model or "default",
                    estimated_cost_usd=cost,
                )
                cache.save(gen_name, current_hash, meta)

            results.append((gen_name, "written", cost, False))

    # Summary
    total_cost = sum(c for _, _, c, _ in results if c is not None)
    print("\n--- docgen summary ---")
    for name, status, cost, _skipped in results:
        cost_str = f" (~${cost:.4f})" if cost is not None else ""
        print(f"  {name:20s} {status}{cost_str}")
    if total_cost > 0:
        print(f"\nTotal estimated cost: ~${total_cost:.4f}")

    generated = sum(1 for _, s, _, _ in results if s in ("written", "preview"))
    cached = sum(1 for _, s, _, _ in results if s == "cached")
    errors = sum(1 for _, s, _, _ in results if s.startswith("error"))
    would_change = sum(1 for _, s, _, _ in results if s == "would-change")
    print(f"\nGenerated: {generated}, Cached: {cached}, Errors: {errors}")

    if args.diff_only and would_change > 0:
        print(f"\n{would_change} file(s) would change. Run 'make docs-gen' to update.")
        return 1

    return 1 if errors > 0 else 0


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )

    sys.exit(_run(args))


if __name__ == "__main__":
    main()
