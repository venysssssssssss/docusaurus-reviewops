"""
Guardrail de freshness de documentacao.

Falha o PR CI se codigo publico foi alterado mas nenhum caminho de documentacao
foi tocado. Isso garante que docs nascem junto com o produto, nao depois.

Politica de relevancia:
  - Mudancas pequenas (<=3 arquivos publicos): qualquer doc touch satisfaz
    (CHANGELOG.md, README.md, docs-site/docs/, etc.)
  - Mudancas grandes (>3 arquivos publicos): exige ao menos 1 arquivo em
    docs-site/docs/ ou docs/ — nao e suficiente apenas tocar CHANGELOG/README.
    Isso previne o bypass trivial de adicionar uma linha em CHANGELOG.md para
    satisfazer a politica em mudancas substanciais de funcionalidade.

Mapeamento semantico (AREA_DOC_MAP):
  Cada area de codigo publica tem uma secao de documentacao correspondente.
  Quando codigo de uma area muda, a politica sugere a secao de doc correta
  na mensagem de erro. Isso orienta o desenvolvedor ao inves de apenas falhar.

Customizacao: ajuste PUBLIC_CHANGE_PREFIXES, DOC_TOUCH_PREFIXES e AREA_DOC_MAP
conforme a estrutura do seu repositorio.

Variaveis de ambiente requeridas (injetadas pelo pr-ci.yml):
  BASE_SHA — SHA da base do PR
  HEAD_SHA — SHA do HEAD do PR
"""

from __future__ import annotations

import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Configuracao — ajuste para o seu repositorio
# ---------------------------------------------------------------------------

# Prefixos que representam codigo com comportamento publico
PUBLIC_CHANGE_PREFIXES: list[str] = [
    "src/",
    "app/",
    "api/",
    "openapi/",
]

# Prefixos/nomes que representam documentacao curada (qualquer tamanho de PR)
DOC_TOUCH_PREFIXES: list[str] = [
    "docs-site/docs/",
    "docs-site/openapi/",
    "docs/",
    "README.md",
    "CHANGELOG.md",
]

# Prefixos de documentacao especifica (exigida em PRs grandes)
SPECIFIC_DOC_PREFIXES: list[str] = [
    "docs-site/docs/",
    "docs/",
]

# Prefixos ignorados ao classificar codigo publico
# (mudancas somente nesses caminhos nao exigem docs)
IGNORED_CODE_PREFIXES: list[str] = [
    "tests/",
    "docs-site/",
    ".github/",
    "scripts/",
]

# Threshold: acima deste numero de arquivos publicos alterados, exige doc especifica
LARGE_CHANGE_THRESHOLD: int = 3

# Mapeamento semantico: area de codigo -> secao de documentacao correspondente.
# Usado para orientar o desenvolvedor na mensagem de erro quando docs estao faltando.
AREA_DOC_MAP: dict[str, str] = {
    "src/": "docs-site/docs/architecture/ ou docs-site/docs/standards/",
    "app/": "docs-site/docs/architecture/ ou docs-site/docs/runbooks/",
    "api/": "docs-site/docs/api/ ou docs-site/openapi/",
    "openapi/": "docs-site/docs/api/ ou docs-site/openapi/",
}

# ---------------------------------------------------------------------------
# Logica principal
# ---------------------------------------------------------------------------


def changed_files() -> list[str]:
    base_sha = os.environ["BASE_SHA"]
    head_sha = os.environ["HEAD_SHA"]
    cmd = ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"]
    output = subprocess.check_output(cmd, text=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def main() -> None:
    files = changed_files()

    public_changes = [
        f
        for f in files
        if any(f.startswith(prefix) for prefix in PUBLIC_CHANGE_PREFIXES)
        and not any(f.startswith(prefix) for prefix in IGNORED_CODE_PREFIXES)
    ]

    doc_changes = [
        f
        for f in files
        if any(f == prefix or f.startswith(prefix) for prefix in DOC_TOUCH_PREFIXES)
    ]

    specific_doc_changes = [
        f
        for f in doc_changes
        if any(f.startswith(prefix) for prefix in SPECIFIC_DOC_PREFIXES)
    ]

    if not public_changes:
        print("Politica de freshness de documentacao: OK (sem mudancas em codigo publico)")
        return

    # Nenhum doc foi tocado — falha sempre
    if not doc_changes:
        print("FALHA: codigo publico alterado mas nenhum caminho de documentacao foi tocado.")
        print("Arquivos publicos alterados:")
        for item in public_changes:
            print(f"  - {item}")

        # Orientacao semantica: sugere a secao de doc mais relevante para cada area tocada
        areas_touched = {
            prefix
            for prefix in PUBLIC_CHANGE_PREFIXES
            if any(f.startswith(prefix) for f in public_changes)
        }
        suggested_docs: list[str] = list({
            AREA_DOC_MAP[area] for area in areas_touched if area in AREA_DOC_MAP
        })
        if suggested_docs:
            print("\nSecoes de documentacao recomendadas para as areas alteradas:")
            for suggestion in sorted(suggested_docs):
                print(f"  -> {suggestion}")

        print(
            "\nAdicione ou atualize documentacao em docs-site/docs/, docs/, "
            "README.md ou CHANGELOG.md."
        )
        print(
            "\nSUGESTAO: execute 'make docs-gen' para gerar documentacao automaticamente via LLM."
        )
        sys.exit(1)

    # Mudanca grande: exige documentacao especifica (nao apenas CHANGELOG/README)
    is_large_change = len(public_changes) > LARGE_CHANGE_THRESHOLD
    if is_large_change and not specific_doc_changes:
        print(
            f"FALHA: {len(public_changes)} arquivos publicos alterados (> {LARGE_CHANGE_THRESHOLD}) "
            "mas apenas documentacao generica foi tocada (CHANGELOG.md / README.md)."
        )
        print(
            "Mudancas substanciais de funcionalidade exigem atualizacao em "
            "docs-site/docs/ ou docs/."
        )
        print("Arquivos publicos alterados:")
        for item in public_changes:
            print(f"  - {item}")
        print(
            "\nSUGESTAO: execute 'make docs-gen' para gerar documentacao automaticamente via LLM."
        )
        sys.exit(1)

    print("Politica de freshness de documentacao: OK")
    print(f"  Arquivos publicos alterados: {len(public_changes)}")
    print(f"  Docs tocados: {len(doc_changes)} ({len(specific_doc_changes)} especificos)")


if __name__ == "__main__":
    main()
