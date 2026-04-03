"""Testes unitarios para .github/scripts/docs_guardrails.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Carregamento do modulo
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.parent / ".github" / "scripts" / "docs_guardrails.py"


@pytest.fixture()
def guardrails(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    monkeypatch.setenv("BASE_SHA", "abc123")
    monkeypatch.setenv("HEAD_SHA", "def456")

    spec = importlib.util.spec_from_file_location("docs_guardrails", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestDocsGuardrailsPass:
    def test_only_tests_changed(self, guardrails: types.ModuleType) -> None:
        """Mudancas somente em tests/ nao exigem docs."""
        with patch.object(guardrails, "changed_files", return_value=["tests/test_foo.py"]):
            guardrails.main()  # nao deve levantar excecao nem sys.exit(1)

    def test_public_and_docs_changed(self, guardrails: types.ModuleType) -> None:
        """Mudanca publica + docs = OK."""
        files = ["src/feature.py", "docs-site/docs/architecture/overview.md"]
        with patch.object(guardrails, "changed_files", return_value=files):
            guardrails.main()

    def test_only_docs_changed(self, guardrails: types.ModuleType) -> None:
        """Apenas docs alterados = sempre OK."""
        files = ["docs-site/docs/runbooks/deploy.md", "README.md"]
        with patch.object(guardrails, "changed_files", return_value=files):
            guardrails.main()

    def test_github_scripts_ignored(self, guardrails: types.ModuleType) -> None:
        """.github/ e ignorado como codigo publico."""
        files = [".github/workflows/pr-ci.yml"]
        with patch.object(guardrails, "changed_files", return_value=files):
            guardrails.main()

    def test_readme_counts_as_doc(self, guardrails: types.ModuleType) -> None:
        """README.md e considerado documentacao."""
        files = ["src/utils.py", "README.md"]
        with patch.object(guardrails, "changed_files", return_value=files):
            guardrails.main()

    def test_changelog_counts_as_doc(self, guardrails: types.ModuleType) -> None:
        """CHANGELOG.md e considerado documentacao."""
        files = ["api/endpoints.py", "CHANGELOG.md"]
        with patch.object(guardrails, "changed_files", return_value=files):
            guardrails.main()

    def test_empty_changeset(self, guardrails: types.ModuleType) -> None:
        """Changeset vazio = OK."""
        with patch.object(guardrails, "changed_files", return_value=[]):
            guardrails.main()


class TestDocsGuardrailsFail:
    def test_public_without_docs(self, guardrails: types.ModuleType) -> None:
        """Codigo publico sem docs = falha."""
        files = ["src/feature.py"]
        with patch.object(guardrails, "changed_files", return_value=files):
            with pytest.raises(SystemExit) as exc:
                guardrails.main()
            assert exc.value.code == 1

    def test_api_without_docs(self, guardrails: types.ModuleType) -> None:
        """api/ sem docs = falha."""
        files = ["api/routes.py"]
        with patch.object(guardrails, "changed_files", return_value=files):
            with pytest.raises(SystemExit) as exc:
                guardrails.main()
            assert exc.value.code == 1

    def test_openapi_without_docs(self, guardrails: types.ModuleType) -> None:
        """openapi/ sem docs = falha."""
        files = ["openapi/schema.json"]
        with patch.object(guardrails, "changed_files", return_value=files):
            with pytest.raises(SystemExit) as exc:
                guardrails.main()
            assert exc.value.code == 1

    def test_app_without_docs(self, guardrails: types.ModuleType) -> None:
        """app/ sem docs = falha."""
        files = ["app/models.py", "app/views.py"]
        with patch.object(guardrails, "changed_files", return_value=files):
            with pytest.raises(SystemExit) as exc:
                guardrails.main()
            assert exc.value.code == 1

    def test_multiple_public_no_docs(self, guardrails: types.ModuleType) -> None:
        """Multiplos arquivos publicos sem docs = falha."""
        files = ["src/a.py", "src/b.py", "api/routes.py"]
        with patch.object(guardrails, "changed_files", return_value=files):
            with pytest.raises(SystemExit) as exc:
                guardrails.main()
            assert exc.value.code == 1
