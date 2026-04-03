#!/usr/bin/env bash
# setup_reviewops.sh — instala o docusaurus-reviewops em um repositorio existente
#
# Uso:
#   bash scripts/setup_reviewops.sh
#   bash scripts/setup_reviewops.sh --target /caminho/do/repo
#
# O script detecta o que ja existe e oferece merge seguro,
# nunca sobrescrevendo arquivos sem confirmacao.

set -euo pipefail

# ---------------------------------------------------------------------------
# Variaveis
# ---------------------------------------------------------------------------

REVIEWOPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-$PWD}"
if [[ "${1:-}" == "--target" ]]; then
  TARGET_DIR="${2}"
  shift 2
fi

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Funcoes utilitarias
# ---------------------------------------------------------------------------

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

confirm() {
  local prompt="${1:-Continuar?}"
  read -r -p "$prompt [s/N] " response
  [[ "$response" =~ ^[sS]$ ]]
}

copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ -f "$dst" ]]; then
    warn "Arquivo ja existe: $dst (pulando)"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    success "Copiado: $dst"
  fi
}

copy_with_confirm() {
  local src="$1"
  local dst="$2"
  if [[ -f "$dst" ]]; then
    warn "Arquivo ja existe: $dst"
    if confirm "  Sobrescrever?"; then
      cp "$src" "$dst"
      success "Sobrescrito: $dst"
    else
      info "  Mantendo arquivo existente."
    fi
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    success "Copiado: $dst"
  fi
}

# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

echo ""
echo "======================================================"
echo "  docusaurus-reviewops — Setup"
echo "======================================================"
echo ""
info "Repositorio origem (reviewops): $REVIEWOPS_DIR"
info "Repositorio destino:            $TARGET_DIR"
echo ""

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  error "O diretorio destino nao parece ser um repositorio git: $TARGET_DIR"
  exit 1
fi

cd "$TARGET_DIR"

# ---------------------------------------------------------------------------
# Passo 1: Verificar pre-requisitos
# ---------------------------------------------------------------------------

echo "--- Verificando pre-requisitos ---"

HAS_PYPROJECT=false
HAS_PACKAGE_JSON=false
HAS_GITHUB_DIR=false
HAS_DOCS_SITE=false

[[ -f "pyproject.toml" ]] && HAS_PYPROJECT=true && info "pyproject.toml encontrado"
[[ -f "package.json" ]] && HAS_PACKAGE_JSON=true && info "package.json encontrado"
[[ -d ".github/workflows" ]] && HAS_GITHUB_DIR=true && info ".github/workflows/ encontrado"
[[ -d "docs-site" ]] && HAS_DOCS_SITE=true && info "docs-site/ encontrado"

echo ""
confirm "Prosseguir com a instalacao?" || exit 0

# ---------------------------------------------------------------------------
# Passo 2: GitHub workflows
# ---------------------------------------------------------------------------

echo ""
echo "--- Instalando workflows GitHub Actions ---"

mkdir -p ".github/workflows" ".github/scripts"

copy_if_missing "$REVIEWOPS_DIR/.github/workflows/pr-ci.yml" ".github/workflows/pr-ci.yml"
copy_if_missing "$REVIEWOPS_DIR/.github/workflows/pr-approval.yml" ".github/workflows/pr-approval.yml"
copy_if_missing "$REVIEWOPS_DIR/.github/workflows/docs-deploy.yml" ".github/workflows/docs-deploy.yml"
copy_if_missing "$REVIEWOPS_DIR/.github/workflows/docs-version-pr.yml" ".github/workflows/docs-version-pr.yml"

copy_if_missing "$REVIEWOPS_DIR/.github/scripts/approval_policy.py" ".github/scripts/approval_policy.py"
copy_if_missing "$REVIEWOPS_DIR/.github/scripts/docs_guardrails.py" ".github/scripts/docs_guardrails.py"

# ---------------------------------------------------------------------------
# Passo 3: CODEOWNERS
# ---------------------------------------------------------------------------

echo ""
echo "--- Configurando CODEOWNERS ---"

if [[ -f ".github/CODEOWNERS" ]]; then
  warn "CODEOWNERS ja existe."
  info "Verifique manualmente se as areas criticas estao mapeadas:"
  info "  .github/, infra/, terraform/, migrations/, alembic/"
  confirm "  Adicionar bloco do reviewops ao CODEOWNERS existente?" && {
    echo "" >> ".github/CODEOWNERS"
    echo "# Adicionado pelo docusaurus-reviewops" >> ".github/CODEOWNERS"
    grep -E "^/docs-site/" "$REVIEWOPS_DIR/.github/CODEOWNERS" >> ".github/CODEOWNERS" || true
    success "Bloco de docs-site adicionado ao CODEOWNERS existente"
  }
else
  copy_if_missing "$REVIEWOPS_DIR/.github/CODEOWNERS" ".github/CODEOWNERS"
  warn "IMPORTANTE: Edite .github/CODEOWNERS e substitua @org/team pelos handles reais"
fi

# ---------------------------------------------------------------------------
# Passo 4: Labels
# ---------------------------------------------------------------------------

echo ""
echo "--- Labels operacionais ---"

copy_if_missing "$REVIEWOPS_DIR/.github/labels.yml" ".github/labels.yml"

if command -v gh &>/dev/null; then
  if confirm "  Criar labels via GitHub CLI (gh label import)?"; then
    gh label import .github/labels.yml && success "Labels criados via gh CLI"
  fi
else
  info "GitHub CLI (gh) nao encontrado."
  info "Para criar os labels: gh label import .github/labels.yml"
fi

# ---------------------------------------------------------------------------
# Passo 5: pyproject.toml
# ---------------------------------------------------------------------------

echo ""
echo "--- Dependencias Python ---"

if [[ "$HAS_PYPROJECT" == "true" ]]; then
  warn "pyproject.toml ja existe — nao sera sobrescrito."
  info "Adicione manualmente as dependencias de dev:"
  info "  ruff, pytest, mypy, pytest-mock"
else
  copy_if_missing "$REVIEWOPS_DIR/pyproject.toml" "pyproject.toml"
fi

# ---------------------------------------------------------------------------
# Passo 6: Portal Docusaurus
# ---------------------------------------------------------------------------

echo ""
echo "--- Portal Docusaurus ---"

if [[ "$HAS_DOCS_SITE" == "true" ]]; then
  warn "docs-site/ ja existe — nao sera sobrescrito."
  info "Verifique manualmente se as dependencias do plugin OpenAPI estao configuradas:"
  info "  docusaurus-plugin-openapi-docs, docusaurus-theme-openapi-docs"
else
  info "Copiando docs-site/..."
  cp -r "$REVIEWOPS_DIR/docs-site" "./"
  success "docs-site/ copiado"
  warn "IMPORTANTE: Edite docs-site/docusaurus.config.ts e substitua os placeholders"
fi

# ---------------------------------------------------------------------------
# Passo 7: Script export_openapi.py
# ---------------------------------------------------------------------------

echo ""
echo "--- Script de export OpenAPI ---"

mkdir -p scripts
copy_if_missing "$REVIEWOPS_DIR/scripts/export_openapi.py" "scripts/export_openapi.py"

if [[ ! -f "scripts/export_openapi.py" ]]; then
  warn "Edite scripts/export_openapi.py e aponte para o modulo da sua app FastAPI"
fi

# ---------------------------------------------------------------------------
# Passo 8: Estrutura minima
# ---------------------------------------------------------------------------

echo ""
echo "--- Estrutura minima de diretorios ---"

mkdir -p src tests
[[ -f "src/__init__.py" ]] || touch "src/__init__.py" && success "src/__init__.py criado"
[[ -f "tests/__init__.py" ]] || touch "tests/__init__.py" && success "tests/__init__.py criado"

# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------

echo ""
echo "======================================================"
echo "  Setup concluido!"
echo "======================================================"
echo ""
echo "Proximos passos obrigatorios:"
echo ""
echo "  1. Edite .github/CODEOWNERS"
echo "     Substitua @org/team pelos handles reais da sua org"
echo ""
echo "  2. Edite docs-site/docusaurus.config.ts"
echo "     Substitua: url, baseUrl, organizationName, projectName, editUrl, copyright"
echo ""
echo "  3. Configure branch protection em main:"
echo "     - Required status checks: quality-gates, docs-gates"
echo "     - Block force pushes"
echo "     - Require conversation resolution"
echo ""
echo "  4. Habilite GitHub Actions para aprovar PRs:"
echo "     Settings > Actions > General > Allow GitHub Actions to create and approve PRs"
echo ""
echo "  5. Edite scripts/export_openapi.py"
echo "     Aponte para o modulo correto da sua app FastAPI"
echo ""
echo "  6. Instale dependencias:"
echo "     poetry install"
echo "     pnpm --dir docs-site install"
echo ""
echo "Documentacao completa: README.md"
echo ""
