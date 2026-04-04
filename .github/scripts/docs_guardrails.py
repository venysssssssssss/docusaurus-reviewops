"""
Guardrail de freshness de documentacao.

Falha o PR CI se codigo publico foi alterado mas nenhum caminho de documentacao
foi tocado. Isso garante que docs nascem junto com o produto, nao depois.

Customizacao: ajuste PUBLIC_CHANGE_PREFIXES e DOC_TOUCH_PREFIXES conforme
a estrutura do seu repositorio.

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

# Prefixos/nomes que representam documentacao curada
DOC_TOUCH_PREFIXES: list[str] = [
    "docs-site/docs/",
    "docs-site/openapi/",
    "docs/",
    "README.md",
    "CHANGELOG.md",
]

# Prefixos ignorados ao classificar codigo publico
# (mudancas somente nesses caminhos nao exigem docs)
IGNORED_CODE_PREFIXES: list[str] = [
    "tests/",
    "docs-site/",
    ".github/",
    "scripts/",
]

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

    if public_changes and not doc_changes:
        print("FALHA: codigo publico alterado mas nenhum caminho de documentacao foi tocado.")
        print("Arquivos publicos alterados:")
        for item in public_changes:
            print(f"  - {item}")
        print(
            "\nAdicione ou atualize documentacao em docs-site/docs/, docs/, "
            "README.md ou CHANGELOG.md."
        )
        print(
            "\nSUGESTAO: execute 'make docs-gen' para gerar documentacao automaticamente via LLM."
        )
        sys.exit(1)

    print("Politica de freshness de documentacao: OK")
    if public_changes:
        print(f"  Arquivos publicos alterados: {len(public_changes)}")
        print(f"  Docs tocados: {len(doc_changes)}")


if __name__ == "__main__":
    main()
