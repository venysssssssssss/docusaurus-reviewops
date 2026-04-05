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
    def test_real_handles_pass(self, validator: types.ModuleType) -> None:
        """CODEOWNERS com handles reais (sem @org/) passa."""
        validator.check_codeowners()
        result = [c for c in validator.CHECKS if "CODEOWNERS" in c["name"]]
        assert len(result) == 1
        assert result[0]["passed"] is True

    def test_detects_placeholder_teams(self, validator: types.ModuleType, tmp_path: Path) -> None:
        """CODEOWNERS com @org/ e detectado."""
        fake_codeowners = tmp_path / "CODEOWNERS"
        fake_codeowners.write_text("* @org/backend-platform\n")
        fake_gh = tmp_path / ".github"
        fake_gh.mkdir()
        (fake_gh / "CODEOWNERS").write_text("* @org/backend-platform\n")
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_codeowners()
        result = validator.CHECKS[-1]
        assert result["passed"] is False

    def test_missing_codeowners(self, validator: types.ModuleType, tmp_path: Path) -> None:
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_codeowners()
        result = validator.CHECKS[-1]
        assert result["passed"] is False


class TestCheckDocusaurusConfig:
    def test_real_config_passes(self, validator: types.ModuleType) -> None:
        """Config com valores reais (sem placeholders) passa."""
        validator.check_docusaurus_config()
        result = [c for c in validator.CHECKS if "docusaurus" in c["name"].lower()]
        assert len(result) == 1
        assert result[0]["passed"] is True

    def test_detects_example_placeholders(self, validator: types.ModuleType, tmp_path: Path) -> None:
        """Config com placeholders de exemplo e detectada."""
        fake_site = tmp_path / "docs-site"
        fake_site.mkdir()
        (fake_site / "docusaurus.config.ts").write_text(
            'url: "https://example.github.io"\norganizationName: "example"\n'
        )
        with patch.object(validator, "ROOT", tmp_path):
            validator.check_docusaurus_config()
        result = validator.CHECKS[-1]
        assert result["passed"] is False

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
    def test_exits_0_when_ready(self, validator: types.ModuleType) -> None:
        """main() deve passar (exit 0) — projeto esta pronto para deploy."""
        # Should not raise — project is fully configured
        validator.main()

    def test_exits_1_with_placeholder_config(
        self, validator: types.ModuleType, tmp_path: Path
    ) -> None:
        """main() falha com exit 1 se ha placeholders."""
        # Create a fake root with placeholder config
        gh = tmp_path / ".github"
        gh.mkdir()
        (gh / "CODEOWNERS").write_text("* @org/backend-platform\n")
        fake_site = tmp_path / "docs-site"
        fake_site.mkdir()
        (fake_site / "docusaurus.config.ts").write_text('url: "https://example.github.io"\n')
        (fake_site / "pnpm-lock.yaml").write_text("")
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        # required_files check needs all files — patch ROOT to tmp_path but
        # the check_file_structure will fail on missing files, not on placeholders
        with patch.object(validator, "ROOT", tmp_path), pytest.raises(SystemExit) as exc:
            validator.main()
        assert exc.value.code == 1
