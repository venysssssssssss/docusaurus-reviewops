"""Testes unitarios para .github/scripts/approval_policy.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixture: carrega o modulo sem executar main()
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.parent / ".github" / "scripts" / "approval_policy.py"


@pytest.fixture()
def policy(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Carrega approval_policy como modulo com env vars fakes."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/repo")
    monkeypatch.setenv("PR_NUMBER", "42")

    spec = importlib.util.spec_from_file_location("approval_policy", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Helpers para construir PR fakes
# ---------------------------------------------------------------------------


def _make_pr(**kwargs: object) -> dict:
    base: dict = {
        "state": "open",
        "draft": False,
        "labels": [],
        "head": {"repo": {"fork": False}},
    }
    base.update(kwargs)
    return base


def _make_file(filename: str, additions: int = 5, deletions: int = 3) -> dict:
    return {"filename": filename, "additions": additions, "deletions": deletions}


# ---------------------------------------------------------------------------
# Testes de fail_closed
# ---------------------------------------------------------------------------


class TestFailClosed:
    def test_exits_zero(self, policy: types.ModuleType) -> None:
        with pytest.raises(SystemExit) as exc:
            policy.fail_closed("motivo qualquer")
        assert exc.value.code == 0


# ---------------------------------------------------------------------------
# Testes do fluxo main()
# ---------------------------------------------------------------------------


class TestMainRejectsClosed:
    def test_pr_closed(self, policy: types.ModuleType) -> None:
        pr = _make_pr(state="closed")
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=[]
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsDraft:
    def test_pr_draft(self, policy: types.ModuleType) -> None:
        pr = _make_pr(draft=True)
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=[]
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsFork:
    def test_pr_from_fork(self, policy: types.ModuleType) -> None:
        pr = _make_pr(head={"repo": {"fork": True}})
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=[]
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsBlockingLabels:
    @pytest.mark.parametrize(
        "label",
        ["security", "breaking-change", "db-migration", "infra-change", "needs-human-review"],
    )
    def test_blocking_label(self, policy: types.ModuleType, label: str) -> None:
        pr = _make_pr(labels=[{"name": label}])
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=[]
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsTooManyFiles:
    def test_too_many_files(self, policy: types.ModuleType) -> None:
        pr = _make_pr()
        files = [_make_file(f"src/file_{i}.py") for i in range(31)]
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=files
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsTooLargeDelta:
    def test_large_delta(self, policy: types.ModuleType) -> None:
        pr = _make_pr()
        files = [_make_file("src/big.py", additions=500, deletions=400)]
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=files
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsProtectedPaths:
    @pytest.mark.parametrize(
        "filename",
        [
            ".github/workflows/pr-ci.yml",
            "infra/main.tf",
            "terraform/variables.tf",
            "helm/values.yaml",
            "migrations/001_init.sql",
            "alembic/versions/001.py",
            "Dockerfile",
            "pyproject.toml",
            "poetry.lock",
            "package.json",
            "pnpm-lock.yaml",
        ],
    )
    def test_protected_path(self, policy: types.ModuleType, filename: str) -> None:
        pr = _make_pr()
        files = [_make_file(filename)]
        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", return_value=files
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsChangesRequested:
    def test_changes_requested(self, policy: types.ModuleType) -> None:
        pr = _make_pr()
        files = [_make_file("src/app.py")]
        reviews = [{"state": "CHANGES_REQUESTED", "user": {"login": "reviewer"}}]

        call_count = 0

        def paginate_side_effect(path: str) -> list:
            nonlocal call_count
            call_count += 1
            if "files" in path:
                return files
            return reviews

        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", side_effect=paginate_side_effect
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainRejectsDuplicateApproval:
    def test_already_approved_by_bot(self, policy: types.ModuleType) -> None:
        pr = _make_pr()
        files = [_make_file("src/app.py")]
        reviews = [{"state": "APPROVED", "user": {"login": "github-actions[bot]"}}]

        def paginate_side_effect(path: str) -> list:
            if "files" in path:
                return files
            return reviews

        with patch.object(policy, "api_request", return_value=pr), patch.object(
            policy, "paginate", side_effect=paginate_side_effect
        ), pytest.raises(SystemExit) as exc:
            policy.main()
        assert exc.value.code == 0


class TestMainApproves:
    def test_eligible_pr_approved(self, policy: types.ModuleType) -> None:
        pr = _make_pr()
        files = [_make_file("src/feature.py", additions=10, deletions=5)]
        reviews: list = []

        api_calls: list[tuple] = []

        def api_side_effect(method: str, path: str, payload: dict | None = None) -> object:
            api_calls.append((method, path, payload))
            if method == "GET":
                return pr
            return {}  # POST de aprovacao

        def paginate_side_effect(path: str) -> list:
            if "files" in path:
                return files
            return reviews

        with patch.object(policy, "api_request", side_effect=api_side_effect), patch.object(
            policy, "paginate", side_effect=paginate_side_effect
        ):
            policy.main()

        # Deve ter chamado POST para registrar aprovacao
        post_calls = [(m, p, pl) for m, p, pl in api_calls if m == "POST"]
        assert len(post_calls) == 1
        assert "reviews" in post_calls[0][1]
        assert post_calls[0][2]["event"] == "APPROVE"
