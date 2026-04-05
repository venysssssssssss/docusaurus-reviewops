"""
Validador de configuracao do docusaurus-reviewops.

Verifica se todos os placeholders foram substituidos e se o projeto
esta pronto para deploy. Use antes de habilitar os workflows.

Uso:
  make validate
  python scripts/validate_config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Checagens
# ---------------------------------------------------------------------------

CHECKS: list[dict] = []
ISSUES: list[str] = []
WARNINGS: list[str] = []
PLACEHOLDER_FIXES: list[tuple[str, str, str]] = []  # (placeholder, description, example)


def check(name: str, passed: bool, message: str) -> None:
    CHECKS.append({"name": name, "passed": passed, "message": message})
    if not passed:
        ISSUES.append(f"  {name}: {message}")


def warn(message: str) -> None:
    WARNINGS.append(f"  {message}")


# ---------------------------------------------------------------------------
# 1. Placeholders no docusaurus.config.ts
# ---------------------------------------------------------------------------

# Maps placeholder → (description, example replacement)
_DOCUSAURUS_PLACEHOLDERS: dict[str, tuple[str, str]] = {
    "example.github.io": (
        "URL do GitHub Pages (url)",
        "sua-org.github.io",
    ),
    '"example"': (
        "organizationName (nome da org no GitHub)",
        '"sua-org"',
    ),
    '"engineering-docs"': (
        "projectName (nome do repositorio)",
        '"seu-repositorio"',
    ),
    "Example Corp": (
        "Copyright — nome da empresa",
        "Sua Empresa Ltda.",
    ),
    "github.com/example/repo": (
        "editUrl — URL do repositorio para editar docs",
        "github.com/sua-org/seu-repositorio",
    ),
}


def check_docusaurus_config() -> None:
    config_path = ROOT / "docs-site" / "docusaurus.config.ts"
    if not config_path.exists():
        check("docusaurus.config.ts", False, "Arquivo nao encontrado")
        return

    content = config_path.read_text()

    found: list[tuple[str, str, str]] = []
    for placeholder, (description, example) in _DOCUSAURUS_PLACEHOLDERS.items():
        if placeholder in content:
            found.append((placeholder, description, example))

    if found:
        check(
            "Placeholders docusaurus.config.ts",
            False,
            f"Encontrados {len(found)} placeholder(s) — veja guia abaixo",
        )
        PLACEHOLDER_FIXES.extend(found)
    else:
        check("Placeholders docusaurus.config.ts", True, "Todos substituidos")

    # Verifica TODOs
    todos = [line.strip() for line in content.splitlines() if "TODO:" in line]
    if todos:
        warn(f"docusaurus.config.ts tem {len(todos)} comentario(s) TODO restante(s)")


# ---------------------------------------------------------------------------
# 2. CODEOWNERS
# ---------------------------------------------------------------------------

def check_codeowners() -> None:
    path = ROOT / ".github" / "CODEOWNERS"
    if not path.exists():
        check("CODEOWNERS", False, "Arquivo nao encontrado")
        return

    content = path.read_text()
    if "@org/" in content:
        check(
            "CODEOWNERS",
            False,
            "Ainda contem @org/team — substitua pelos handles reais",
        )
    else:
        check("CODEOWNERS", True, "Handles configurados")


# ---------------------------------------------------------------------------
# 3. export_openapi.py
# ---------------------------------------------------------------------------

def check_openapi_export() -> None:
    path = ROOT / "scripts" / "export_openapi.py"
    if not path.exists():
        check("export_openapi.py", False, "Arquivo nao encontrado")
        return

    content = path.read_text()
    if "from app.main import app" in content and "ImportError" in content:
        warn(
            "export_openapi.py usa placeholder 'from app.main import app' "
            "— substitua pelo import real da sua app FastAPI"
        )


# ---------------------------------------------------------------------------
# 4. Estrutura de arquivos
# ---------------------------------------------------------------------------

def check_file_structure() -> None:
    required_files = [
        ".github/workflows/pr-ci.yml",
        ".github/workflows/pr-approval.yml",
        ".github/workflows/docs-deploy.yml",
        ".github/workflows/docs-version-pr.yml",
        ".github/scripts/approval_policy.py",
        ".github/scripts/docs_guardrails.py",
        ".github/CODEOWNERS",
        ".github/labels.yml",
        "docs-site/docusaurus.config.ts",
        "docs-site/package.json",
        "docs-site/sidebars.ts",
        "docs-site/docs/index.md",
        "scripts/export_openapi.py",
        "pyproject.toml",
    ]

    missing = [f for f in required_files if not (ROOT / f).exists()]
    if missing:
        check("Estrutura de arquivos", False, f"Faltando: {', '.join(missing)}")
    else:
        check("Estrutura de arquivos", True, f"Todos os {len(required_files)} arquivos presentes")


# ---------------------------------------------------------------------------
# 5. Lockfile do portal
# ---------------------------------------------------------------------------

def check_lockfile() -> None:
    lockfile = ROOT / "docs-site" / "pnpm-lock.yaml"
    if not lockfile.exists():
        check(
            "pnpm-lock.yaml",
            False,
            "Nao encontrado — rode 'pnpm --dir docs-site install'",
        )
    else:
        check("pnpm-lock.yaml", True, "Presente")


# ---------------------------------------------------------------------------
# 6. GitHub repo
# ---------------------------------------------------------------------------

def check_git() -> None:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        check("Repositorio git", False, "Nao e um repositorio git — rode 'git init'")
    else:
        check("Repositorio git", True, "Inicializado")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== docusaurus-reviewops: validacao de configuracao ===\n")

    check_git()
    check_file_structure()
    check_lockfile()
    check_codeowners()
    check_docusaurus_config()
    check_openapi_export()

    # Resultados
    passed = sum(1 for c in CHECKS if c["passed"])
    total = len(CHECKS)

    print(f"Checagens: {passed}/{total} OK\n")

    for c in CHECKS:
        icon = "OK" if c["passed"] else "!!"
        print(f"  [{icon}] {c['name']}: {c['message']}")

    if WARNINGS:
        print(f"\nAvisos ({len(WARNINGS)}):")
        for w in WARNINGS:
            print(w)

    if PLACEHOLDER_FIXES:
        print(f"\nGuia de substituicao de placeholders ({len(PLACEHOLDER_FIXES)} itens):")
        print("  Arquivo: docs-site/docusaurus.config.ts\n")
        for placeholder, description, example in PLACEHOLDER_FIXES:
            print(f"  Substituir : {placeholder}")
            print(f"  Campo      : {description}")
            print(f"  Exemplo    : {example}")
            print()

    if ISSUES:
        print(f"Problemas ({len(ISSUES)}):")
        for issue in ISSUES:
            print(issue)
        print("\nCorreja os problemas acima antes de habilitar os workflows.")
        sys.exit(1)
    else:
        print("\nPronto para deploy!")


if __name__ == "__main__":
    main()
