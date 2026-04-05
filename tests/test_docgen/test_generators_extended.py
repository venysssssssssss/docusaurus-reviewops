"""Extended tests for ADR, Changelog, and APIEnricher generators.

Also adds generate() integration tests for Standards and Runbook generators.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts.docgen.analyzer.codebase import analyze_codebase
from scripts.docgen.config import DocgenConfig
from scripts.docgen.generators.adr import ADRGenerator
from scripts.docgen.generators.api_enricher import APIEnricherGenerator
from scripts.docgen.generators.changelog import ChangelogGenerator
from scripts.docgen.generators.runbook import RunbookGenerator
from scripts.docgen.generators.standards import StandardsGenerator
from scripts.docgen.providers.mock import MockProvider

# ---------------------------------------------------------------------------
# Standards — generate() integration
# ---------------------------------------------------------------------------


class TestStandardsGeneratorGenerate:
    def test_generates_content_with_pyproject(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = StandardsGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, [], [])
        content, response = gen.generate(snapshot)
        assert len(content) > 0
        assert response is not None
        assert response.provider == "mock"

    def test_output_filename(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = StandardsGenerator(mock_provider, sample_config)
        assert gen.output_filename == "standards/coding-standards.md"

    def test_generate_with_no_config_files(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Empty codebase (no pyproject/tsconfig) still calls LLM and returns content."""
        empty = tmp_path / "empty"
        empty.mkdir()
        (empty / "main.py").write_text("print('hello')\n")
        snapshot = analyze_codebase(empty, [], [])
        gen = StandardsGenerator(mock_provider, sample_config)
        content, response = gen.generate(snapshot)
        assert len(content) > 0


# ---------------------------------------------------------------------------
# Runbook — generate() integration
# ---------------------------------------------------------------------------


class TestRunbookGeneratorGenerate:
    def test_generates_content_with_workflows(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = RunbookGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, [".github/", "scripts/"], [])
        content, response = gen.generate(snapshot)
        assert len(content) > 0
        assert response is not None

    def test_output_filename(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = RunbookGenerator(mock_provider, sample_config)
        assert gen.output_filename == "runbooks/deploy.md"

    def test_generate_with_no_workflows(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """No workflows/Makefile still generates content (passes empty placeholders)."""
        empty = tmp_path / "no_workflows"
        empty.mkdir()
        snapshot = analyze_codebase(empty, [], [])
        gen = RunbookGenerator(mock_provider, sample_config)
        content, response = gen.generate(snapshot)
        assert len(content) > 0


# ---------------------------------------------------------------------------
# ADR generator
# ---------------------------------------------------------------------------

_FAKE_COMMITS = [
    {
        "sha": "abc123def456",
        "message": "feat: add LLM documentation generator",
        "author": "dev",
        "date": "2026-04-01T10:00:00+00:00",
        "files_changed": 30,
        "insertions": 500,
        "deletions": 10,
    },
    {
        "sha": "111222333444",
        "message": "fix: resolve cache invalidation bug",
        "author": "dev",
        "date": "2026-04-02T10:00:00+00:00",
        "files_changed": 2,
        "insertions": 15,
        "deletions": 5,
    },
]


class TestADRGenerator:
    def test_name(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = ADRGenerator(mock_provider, sample_config)
        assert gen.name == "adr"

    def test_output_filename_starts_with_001_when_no_existing_adrs(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = ADRGenerator(mock_provider, sample_config)
        assert gen.output_filename == "adr/001-auto-generated.md"

    def test_output_filename_increments_past_existing_adrs(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "001-some-decision.md").write_text("# ADR 001\n")
        (adr_dir / "002-another.md").write_text("# ADR 002\n")
        gen = ADRGenerator(mock_provider, sample_config)
        assert gen.output_filename == "adr/003-auto-generated.md"

    def test_relevant_paths_returns_config_files(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        gen = ADRGenerator(mock_provider, sample_config)
        snapshot = analyze_codebase(sample_codebase, [], [])
        paths = gen.relevant_paths(snapshot)
        names = [p.name for p in paths]
        assert "pyproject.toml" in names or "Makefile" in names

    def test_generate_returns_empty_when_no_commits(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = ADRGenerator(mock_provider, sample_config)
        with (
            patch("scripts.docgen.generators.adr.get_latest_tag", return_value=None),
            patch("scripts.docgen.generators.adr.get_commits", return_value=[]),
            patch("scripts.docgen.generators.adr.get_significant_changes", return_value=[]),
        ):
            content, response = gen.generate(snapshot)
        assert content == ""
        assert response is None

    def test_generate_returns_content_with_commits(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        from scripts.docgen.analyzer.git_history import CommitInfo

        commits = [
            CommitInfo(**c) for c in _FAKE_COMMITS
        ]
        significant = [commits[0]]  # Only the large feat commit

        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = ADRGenerator(mock_provider, sample_config)
        with (
            patch("scripts.docgen.generators.adr.get_latest_tag", return_value="v0.1.0"),
            patch("scripts.docgen.generators.adr.get_commits", return_value=commits),
            patch("scripts.docgen.generators.adr.get_significant_changes", return_value=significant),
        ):
            content, response = gen.generate(snapshot)
        assert len(content) > 0
        assert response is not None


# ---------------------------------------------------------------------------
# Changelog generator
# ---------------------------------------------------------------------------


class TestChangelogGenerator:
    def test_name(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = ChangelogGenerator(mock_provider, sample_config)
        assert gen.name == "changelog"

    def test_output_path_is_repo_root_changelog(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = ChangelogGenerator(mock_provider, sample_config)
        assert gen.output_path() == Path("CHANGELOG.md")

    def test_generate_returns_empty_when_no_commits(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = ChangelogGenerator(mock_provider, sample_config)
        with (
            patch("scripts.docgen.generators.changelog.get_latest_tag", return_value=None),
            patch("scripts.docgen.generators.changelog.get_commits", return_value=[]),
        ):
            content, response = gen.generate(snapshot)
        assert content == ""
        assert response is None

    def test_generate_returns_content_with_commits(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        from scripts.docgen.analyzer.git_history import CommitInfo

        commits = [CommitInfo(**c) for c in _FAKE_COMMITS]
        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = ChangelogGenerator(mock_provider, sample_config)
        with (
            patch("scripts.docgen.generators.changelog.get_latest_tag", return_value="v0.1.0"),
            patch("scripts.docgen.generators.changelog.get_commits", return_value=commits),
        ):
            content, response = gen.generate(snapshot)
        assert len(content) > 0
        assert response is not None

    def test_generate_suggests_next_patch_version(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, sample_codebase: Path
    ) -> None:
        """When last tag is v0.2.0, version in prompt should be 0.2.1."""
        from scripts.docgen.analyzer.git_history import CommitInfo

        commits = [CommitInfo(**_FAKE_COMMITS[0])]
        rendered_prompts: list[str] = []

        original_generate = mock_provider.generate

        def capture_prompt(prompt: str, **kwargs: object) -> object:
            rendered_prompts.append(prompt)
            return original_generate(prompt, **kwargs)

        mock_provider.generate = capture_prompt  # type: ignore[method-assign]
        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = ChangelogGenerator(mock_provider, sample_config)
        with (
            patch("scripts.docgen.generators.changelog.get_latest_tag", return_value="v0.2.0"),
            patch("scripts.docgen.generators.changelog.get_commits", return_value=commits),
        ):
            gen.generate(snapshot)
        assert any("0.2.1" in p for p in rendered_prompts)


# ---------------------------------------------------------------------------
# API Enricher generator
# ---------------------------------------------------------------------------


class TestAPIEnricherGenerator:
    def test_name(
        self, mock_provider: MockProvider, sample_config: DocgenConfig
    ) -> None:
        gen = APIEnricherGenerator(mock_provider, sample_config)
        assert gen.name == "api_enricher"

    def test_generate_returns_empty_when_no_schema(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        # No openapi.json exists
        content, response = gen.generate(snapshot)
        assert content == ""
        assert response is None

    def test_generate_skips_schema_without_operation_ids(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Schema with no operationId in any endpoint is treated as a stub and skipped."""
        schema = {
            "info": {"version": "1.0.0", "title": "Stub API"},
            "paths": {
                "/ping": {
                    "get": {
                        "summary": "Ping",
                        # no operationId — stub schema
                    }
                }
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch(
            "scripts.docgen.generators.api_enricher._OPENAPI_PATH",
            schema_path,
        ):
            content, response = gen.generate(snapshot)
        assert content == ""
        assert response is None

    def test_generate_enriches_endpoints_without_descriptions(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Endpoints with no/short descriptions should be enriched."""
        schema = {
            "info": {"version": "1.0.0", "title": "Test API"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "list_users",
                        "summary": "List all users",
                        "description": "",  # Empty — should be enriched
                    }
                }
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch(
            "scripts.docgen.generators.api_enricher._OPENAPI_PATH",
            schema_path,
        ):
            content, response = gen.generate(snapshot)
        assert len(content) > 0
        enriched_schema = json.loads(content)
        assert enriched_schema["paths"]["/users"]["get"]["description"] != ""
        assert response is not None

    def test_generate_skips_already_described_endpoints(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Endpoints with descriptions > 20 chars are not touched."""
        long_desc = "This endpoint retrieves a paginated list of all registered users."
        schema = {
            "info": {"version": "1.0.0", "title": "Test API"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "list_users",
                        "description": long_desc,
                    }
                }
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        calls: list[str] = []
        original = mock_provider.generate

        def track_calls(prompt: str, **kw: object) -> object:
            calls.append(prompt)
            return original(prompt, **kw)

        mock_provider.generate = track_calls  # type: ignore[method-assign]
        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch(
            "scripts.docgen.generators.api_enricher._OPENAPI_PATH",
            schema_path,
        ):
            content, _ = gen.generate(snapshot)
        # No LLM calls should have been made
        assert calls == []
        assert content == ""

    def test_two_pass_enriches_all_matching_endpoints(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Two-pass approach enriches all endpoints needing descriptions."""
        schema = {
            "info": {"version": "1.0.0", "title": "Test API"},
            "paths": {
                "/users": {
                    "get": {"operationId": "list_users", "description": ""},
                    "post": {"operationId": "create_user", "description": ""},
                },
                "/users/{id}": {
                    "delete": {"operationId": "delete_user", "description": "short"},
                },
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch("scripts.docgen.generators.api_enricher._OPENAPI_PATH", schema_path):
            content, _ = gen.generate(snapshot)

        enriched = json.loads(content)
        # All 3 endpoints had short/empty descriptions — all should be enriched
        assert enriched["paths"]["/users"]["get"]["description"] != ""
        assert enriched["paths"]["/users"]["post"]["description"] != ""
        assert enriched["paths"]["/users/{id}"]["delete"]["description"] != ""

    def test_extension_methods_are_not_enriched(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Methods starting with 'x-' (OpenAPI extensions) must be skipped."""
        schema = {
            "info": {"version": "1.0.0", "title": "Test API"},
            "paths": {
                "/items": {
                    "get": {"operationId": "list_items", "description": ""},
                    "x-amazon-apigateway-any-method": {
                        "description": "vendor extension — must not be enriched",
                    },
                }
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        calls: list[str] = []
        original = mock_provider.generate

        def track(prompt: str, **kw: object) -> object:
            calls.append(prompt)
            return original(prompt, **kw)

        mock_provider.generate = track  # type: ignore[method-assign]
        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch("scripts.docgen.generators.api_enricher._OPENAPI_PATH", schema_path):
            gen.generate(snapshot)

        # Only 1 call for the real GET endpoint; x- extension is not called
        assert len(calls) == 1
        assert "/items" in calls[0]

    def test_mixed_endpoints_only_enrich_undescribed(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Mix of described and undescribed: only undescribed ones are enriched."""
        long_desc = "A fully documented endpoint with a sufficiently long description."
        schema = {
            "info": {"version": "1.0.0", "title": "Mixed API"},
            "paths": {
                "/a": {"get": {"operationId": "op_a", "description": long_desc}},
                "/b": {"get": {"operationId": "op_b", "description": ""}},
                "/c": {"get": {"operationId": "op_c", "description": "tiny"}},
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        calls: list[str] = []
        original = mock_provider.generate

        def track(prompt: str, **kw: object) -> object:
            calls.append(prompt)
            return original(prompt, **kw)

        mock_provider.generate = track  # type: ignore[method-assign]
        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch("scripts.docgen.generators.api_enricher._OPENAPI_PATH", schema_path):
            content, _ = gen.generate(snapshot)

        enriched = json.loads(content)
        # /a already had a long description — must be unchanged
        assert enriched["paths"]["/a"]["get"]["description"] == long_desc
        # /b and /c must now have non-empty descriptions
        assert enriched["paths"]["/b"]["get"]["description"] != ""
        assert enriched["paths"]["/c"]["get"]["description"] != ""
        # Exactly 2 LLM calls (/b and /c)
        assert len(calls) == 2

    def test_preserves_summary_when_enriching_description(
        self, mock_provider: MockProvider, sample_config: DocgenConfig, tmp_path: Path
    ) -> None:
        """Enriching description must not clobber an existing summary field."""
        original_summary = "List all active users"
        schema = {
            "info": {"version": "1.0.0", "title": "Test API"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "list_users",
                        "summary": original_summary,
                        "description": "",
                    }
                }
            },
        }
        schema_path = tmp_path / "openapi.json"
        schema_path.write_text(json.dumps(schema))

        snapshot = analyze_codebase(tmp_path, [], [])
        gen = APIEnricherGenerator(mock_provider, sample_config)
        with patch("scripts.docgen.generators.api_enricher._OPENAPI_PATH", schema_path):
            content, _ = gen.generate(snapshot)

        enriched = json.loads(content)
        assert enriched["paths"]["/users"]["get"]["summary"] == original_summary
        assert enriched["paths"]["/users"]["get"]["description"] != ""
