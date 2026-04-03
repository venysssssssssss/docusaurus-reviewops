"""Testes unitarios para scripts/export_openapi.py."""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "export_openapi.py"


@pytest.fixture()
def exporter() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestGetSchema:
    def test_returns_valid_openapi_dict(self, exporter: types.ModuleType) -> None:
        schema = exporter._get_schema()
        assert isinstance(schema, dict)
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_placeholder_has_correct_version(self, exporter: types.ModuleType) -> None:
        schema = exporter._get_schema()
        assert schema["openapi"] == "3.1.0"

    def test_placeholder_has_info(self, exporter: types.ModuleType) -> None:
        schema = exporter._get_schema()
        assert "title" in schema["info"]
        assert "version" in schema["info"]


class TestMain:
    def test_creates_output_file(self, exporter: types.ModuleType, tmp_path: Path) -> None:
        output = tmp_path / "openapi" / "openapi.json"
        with patch.object(exporter, "OUTPUT_PATH", output):
            exporter.main()

        assert output.exists()
        content = json.loads(output.read_text())
        assert content["openapi"] == "3.1.0"

    def test_output_is_valid_json(self, exporter: types.ModuleType, tmp_path: Path) -> None:
        output = tmp_path / "openapi.json"
        with patch.object(exporter, "OUTPUT_PATH", output):
            exporter.main()

        content = output.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_creates_parent_dirs(self, exporter: types.ModuleType, tmp_path: Path) -> None:
        output = tmp_path / "deep" / "nested" / "openapi.json"
        with patch.object(exporter, "OUTPUT_PATH", output):
            exporter.main()

        assert output.exists()
