"""
Politica de auto-aprovacao de Pull Requests.

Este script e executado pelo workflow privilegiado (pr-approval.yml) APOS
o PR CI completar com sucesso. Ele consulta a API REST do GitHub, aplica
a politica e registra um review APPROVE somente se o PR for elegivel.

SEGURANCA: Este script nunca executa codigo do PR. Apenas consome metadados
via API REST. Ref: GitHub Docs — Secure use reference [R12][R13].

Customizacao: ajuste as constantes BLOCKING_LABELS, PROTECTED_PATTERNS,
MAX_CHANGED_FILES e MAX_TOTAL_DELTA conforme a realidade do seu projeto.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from typing import NoReturn
from urllib.error import HTTPError

# ---------------------------------------------------------------------------
# Configuracao — ajuste para o seu repositorio
# ---------------------------------------------------------------------------

API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = os.environ["PR_NUMBER"]
BOT_LOGIN = "github-actions[bot]"

# Labels que bloqueiam auto-aprovacao (revisao humana obrigatoria)
BLOCKING_LABELS: set[str] = {
    "security",
    "breaking-change",
    "db-migration",
    "infra-change",
    "needs-human-review",
}

# Padroes de caminho protegidos — PRs que tocam esses arquivos nunca sao auto-aprovados.
#
# Design decision — Dependabot PRs:
# Dependabot PRs que atualizam pyproject.toml, poetry.lock, package.json ou pnpm-lock.yaml
# caem aqui e NAO sao auto-aprovados. Isso e intencional:
#   1. Bumps de dependencia podem introduzir breaking changes ou regressoes de seguranca
#      que os testes automatizados nao detectam (ex: mudancas de comportamento sutis).
#   2. O Dependabot agrupa atualizacoes e o delta de lockfile pode ser grande e opaco.
#   3. A revisao humana de deps e considerada parte essencial da postura de seguranca.
# Se quiser auto-aprovar Dependabot para patches, remova os patterns de lockfile acima
# E adicione uma condicao: `if pr.get("user", {}).get("login") == "dependabot[bot]"`.
PROTECTED_PATTERNS: list[str] = [
    r"^\.github/",
    r"^infra/",
    r"^terraform/",
    r"^helm/",
    r"^migrations?/",
    r"^alembic/",
    r"^docs-site/docusaurus\.config\.(js|ts)$",
    r"^docs-site/sidebars\.(js|ts)$",
    r"^Dockerfile",
    r"^pyproject\.toml$",
    r"^poetry\.lock$",
    r"^package\.json$",
    r"^pnpm-lock\.yaml$",
]

# Limites de tamanho do PR
MAX_CHANGED_FILES = 30
MAX_TOTAL_DELTA = 800   # total de linhas adicionadas + removidas
MAX_NET_CHANGE = 400    # net change = |adicoes - remocoes|; refactors grandes mas equilibrados
#                         podem ter MAX_TOTAL_DELTA alto mas net baixo — esse gate captura
#                         PRs que reescrevem funcionalidade significativa mascarados como
#                         "refactoring neutro" (ex: 600 add + 600 del = 1200 delta, 0 net).

# ---------------------------------------------------------------------------
# Utilitarios de API
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def api_request(method: str, path: str, payload: dict | None = None) -> dict | list | None:
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        headers=_headers(),
        data=json.dumps(payload).encode("utf-8") if payload else None,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc


def paginate(path: str) -> list[dict]:
    page = 1
    results: list[dict] = []
    while True:
        chunk = api_request("GET", f"{path}?per_page=100&page={page}")
        if not isinstance(chunk, list):
            break
        results.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return results


# ---------------------------------------------------------------------------
# Logica de decisao
# ---------------------------------------------------------------------------


def fail_closed(reason: str) -> NoReturn:
    """Encerra sem registrar aprovacao. Ausencia de aprovacao e parte da politica."""
    print(f"[policy] nao elegivel: {reason}")
    sys.exit(0)


def main() -> None:
    pr = api_request("GET", f"/repos/{REPO}/pulls/{PR_NUMBER}")
    if not isinstance(pr, dict):
        fail_closed("resposta inesperada da API")

    # Estado do PR
    if pr.get("state") != "open":
        fail_closed("PR nao esta aberto")

    if pr.get("draft"):
        fail_closed("PR ainda esta em draft")

    # Forks — nunca auto-aprovar (seguranca)
    if pr.get("head", {}).get("repo", {}).get("fork"):
        fail_closed("PR vem de um fork — politica proibe auto-aprovacao")

    # Labels bloqueantes
    labels: set[str] = {item["name"] for item in pr.get("labels", [])}
    matched = BLOCKING_LABELS.intersection(labels)
    if matched:
        fail_closed(f"labels bloqueantes encontrados: {sorted(matched)}")

    # Tamanho do PR
    files = paginate(f"/repos/{REPO}/pulls/{PR_NUMBER}/files")

    if len(files) > MAX_CHANGED_FILES:
        fail_closed(f"muitos arquivos alterados ({len(files)} > {MAX_CHANGED_FILES})")

    total_additions = sum(f.get("additions", 0) for f in files)
    total_deletions = sum(f.get("deletions", 0) for f in files)
    total_delta = total_additions + total_deletions
    net_change = abs(total_additions - total_deletions)

    if total_delta > MAX_TOTAL_DELTA:
        fail_closed(f"diff muito grande ({total_delta} linhas > {MAX_TOTAL_DELTA})")

    if net_change > MAX_NET_CHANGE:
        fail_closed(
            f"net change muito grande ({net_change} linhas > {MAX_NET_CHANGE}) — "
            "PR reescreve funcionalidade significativa e requer revisao humana"
        )

    # Caminhos protegidos
    filenames = [f["filename"] for f in files]
    for name in filenames:
        if any(re.search(pattern, name) for pattern in PROTECTED_PATTERNS):
            fail_closed(f"caminho protegido tocado: {name}")

    # Reviews existentes
    reviews = paginate(f"/repos/{REPO}/pulls/{PR_NUMBER}/reviews")
    for review in reviews:
        if review.get("state") == "CHANGES_REQUESTED":
            fail_closed("ha pelo menos um review CHANGES_REQUESTED pendente")
        if review.get("state") == "APPROVED" and review.get("user", {}).get("login") == BOT_LOGIN:
            fail_closed("aprovacao ja registrada pelo bot — evitando duplicata")

    # Tudo passou — registrar aprovacao
    body = (
        "Aprovacao automatica registrada.\n\n"
        "Todos os quality gates do workflow Pull Request CI passaram:\n"
        "- Lint (ruff) passou\n"
        "- Sintaxe e tipos verificados\n"
        "- Testes passaram\n"
        "- Docs freshness validado\n"
        "- Build do portal Docusaurus concluido\n\n"
        "O PR nao esta em draft, nao veio de fork, nao possui labels bloqueantes\n"
        "e nao tocou caminhos protegidos pela politica de auto-approval."
    )

    api_request(
        "POST",
        f"/repos/{REPO}/pulls/{PR_NUMBER}/reviews",
        {"event": "APPROVE", "body": body},
    )
    print("[policy] aprovacao registrada com sucesso.")


if __name__ == "__main__":
    main()
