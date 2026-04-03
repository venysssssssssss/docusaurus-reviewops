"""Testes unitarios para scripts/validate_config.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "validate_config.py"


@pytest.fixture()
def validator() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("validate_config", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    # Limpa estado global entre testes
    mod.CHECKS.clear()
    mod.ISSUES.clear()
    mod.WARNINGS.clear()
    return mod


class TestCheckFileStructure:
    def test_all_files_present(self, validator: types.ModuleType) -> None:
        """Projeto completo deve passar."""
        validator.check_file_structure()
        result = validator.CHECKS[-1]
        assert result["passed"] is True

    def test_missing_file_detected(self, validator: types.ModuleType, tmp_path: Path) -> None:
        """Diretorio vazio detecta arquivos faltando."""
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_file_structure()
        result = validator.CHECKS[-1]
        assert result["passed"] is False
        assert "Faltando" in result["message"]


class TestCheckCodeowners:
    def test_detects_placeholder_teams(self, validator: types.ModuleType) -> None:
        """CODEOWNERS com @org/ e detectado."""
        validator.check_codeowners()
        result = [c for c in validator.CHECKS if "CODEOWNERS" in c["name"]]
        assert len(result) == 1
        # Nosso CODEOWNERS tem @org/ — deve falhar
        assert result[0]["passed"] is False

    def test_missing_codeowners(self, validator: types.ModuleType, tmp_path: Path) -> None:
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_codeowners()
        result = validator.CHECKS[-1]
        assert result["passed"] is False


class TestCheckDocusaurusConfig:
    def test_detects_example_placeholders(self, validator: types.ModuleType) -> None:
        """Config com placeholders de exemplo e detectada."""
        validator.check_docusaurus_config()
        result = [c for c in validator.CHECKS if "docusaurus" in c["name"].lower()]
        assert len(result) == 1
        # Nosso config tem "example.github.io" — deve falhar
        assert result[0]["passed"] is False

    def test_missing_config(self, validator: types.ModuleType, tmp_path: Path) -> None:
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_docusaurus_config()
        result = validator.CHECKS[-1]
        assert result["passed"] is False


class TestCheckGit:
    def test_git_initialized(self, validator: types.ModuleType) -> None:
        validator.check_git()
        result = validator.CHECKS[-1]
        assert result["passed"] is True


class TestMain:
    def test_exits_1_with_issues(self, validator: types.ModuleType) -> None:
        """main() deve falhar com exit 1 se ha problemas (nosso projeto tem placeholders)."""
        with pytest.raises(SystemExit) as exc:
            validator.main()
        assert exc.value.code == 1
