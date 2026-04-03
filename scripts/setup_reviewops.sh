#!/usr/bin/env bash
# setup_reviewops.sh — instala o docusaurus-reviewops em um repositorio existente
#
# Uso:
#   bash scripts/setup_reviewops.sh                       # interativo
#   bash scripts/setup_reviewops.sh --yes                  # aceita tudo
#   bash scripts/setup_reviewops.sh --dry-run              # mostra o que faria
#   bash scripts/setup_reviewops.sh --target /caminho/repo # outro diretorio
#
# Flags podem ser combinadas:
#   bash scripts/setup_reviewops.sh --dry-run --target /meu/repo

set -euo pipefail

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

DRY_RUN=false
AUTO_YES=false
TARGET_DIR="$PWD"
REVIEWOPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --yes|-y)   AUTO_YES=true; shift ;;
    --target)   TARGET_DIR="$2"; shift 2 ;;
    -*)         echo "Flag desconhecida: $1"; exit 1 ;;
    *)          TARGET_DIR="$1"; shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Cores e funcoes utilitarias
# ---------------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[ OK ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERRO]${NC} $*" >&2; }
dry()     { echo -e "${GRAY}[DRY]${NC}  $*"; }

confirm() {
  if [[ "$AUTO_YES" == "true" ]]; then return 0; fi
  local prompt="${1:-Continuar?}"
  read -r -p "$prompt [s/N] " response
  [[ "$response" =~ ^[sS]$ ]]
}

safe_copy() {
  local src="$1" dst="$2"
  if [[ "$DRY_RUN" == "true" ]]; then
    if [[ -f "$dst" ]]; then
      dry "Pularia (ja existe): $dst"
    else
      dry "Copiaria: $dst"
    fi
    return
  fi
  if [[ -f "$dst" ]]; then
    warn "Ja existe: $dst (pulando)"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    success "Copiado: $dst"
  fi
}

safe_copy_dir() {
  local src="$1" dst="$2"
  if [[ "$DRY_RUN" == "true" ]]; then
    if [[ -d "$dst" ]]; then
      dry "Pularia diretorio (ja existe): $dst"
    else
      dry "Copiaria diretorio: $dst"
    fi
    return
  fi
  if [[ -d "$dst" ]]; then
    warn "Ja existe: $dst (pulando)"
  else
    cp -r "$src" "$dst"
    success "Copiado: $dst"
  fi
}

safe_mkdir() {
  local dir="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    [[ -d "$dir" ]] || dry "Criaria: $dir"
    return
  fi
  mkdir -p "$dir"
}

safe_touch() {
  local file="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    [[ -f "$file" ]] || dry "Criaria: $file"
    return
  fi
  [[ -f "$file" ]] || { touch "$file" && success "Criado: $file"; }
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

echo ""
echo "======================================================"
echo "  docusaurus-reviewops — Setup"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  MODO DRY-RUN: nenhum arquivo sera alterado"
fi
echo "======================================================"
echo ""
info "Origem:  $REVIEWOPS_DIR"
info "Destino: $TARGET_DIR"
echo ""

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  error "Nao e um repositorio git: $TARGET_DIR"
  exit 1
fi

cd "$TARGET_DIR"

# ---------------------------------------------------------------------------
# Deteccao do estado atual
# ---------------------------------------------------------------------------

echo "--- Estado atual do repositorio ---"

HAS_PYPROJECT=false; [[ -f "pyproject.toml" ]] && HAS_PYPROJECT=true && info "pyproject.toml encontrado"
HAS_DOCS_SITE=false; [[ -d "docs-site" ]] && HAS_DOCS_SITE=true && info "docs-site/ encontrado"
HAS_GITHUB=false;    [[ -d ".github/workflows" ]] && HAS_GITHUB=true && info ".github/workflows/ encontrado"

echo ""
confirm "Prosseguir com a instalacao?" || exit 0

# ---------------------------------------------------------------------------
# 1. Workflows e scripts
# ---------------------------------------------------------------------------

echo ""
echo "--- Workflows e scripts ---"

safe_mkdir ".github/workflows"
safe_mkdir ".github/scripts"

safe_copy "$REVIEWOPS_DIR/.github/workflows/pr-ci.yml"           ".github/workflows/pr-ci.yml"
safe_copy "$REVIEWOPS_DIR/.github/workflows/pr-approval.yml"     ".github/workflows/pr-approval.yml"
safe_copy "$REVIEWOPS_DIR/.github/workflows/docs-deploy.yml"     ".github/workflows/docs-deploy.yml"
safe_copy "$REVIEWOPS_DIR/.github/workflows/docs-version-pr.yml" ".github/workflows/docs-version-pr.yml"
safe_copy "$REVIEWOPS_DIR/.github/scripts/approval_policy.py"    ".github/scripts/approval_policy.py"
safe_copy "$REVIEWOPS_DIR/.github/scripts/docs_guardrails.py"    ".github/scripts/docs_guardrails.py"

# ---------------------------------------------------------------------------
# 2. CODEOWNERS e labels
# ---------------------------------------------------------------------------

echo ""
echo "--- CODEOWNERS e labels ---"

safe_copy "$REVIEWOPS_DIR/.github/CODEOWNERS" ".github/CODEOWNERS"
safe_copy "$REVIEWOPS_DIR/.github/labels.yml" ".github/labels.yml"

if [[ "$DRY_RUN" == "false" ]] && [[ -f ".github/CODEOWNERS" ]]; then
  if grep -q "@org/" ".github/CODEOWNERS"; then
    warn "CODEOWNERS contem @org/team — substitua pelos handles reais"
  fi
fi

if [[ "$DRY_RUN" == "false" ]] && command -v gh &>/dev/null; then
  if confirm "Criar labels via GitHub CLI?"; then
    gh label import .github/labels.yml 2>/dev/null && success "Labels criados" || warn "Falha ao criar labels (verifique autenticacao do gh)"
  fi
fi

# ---------------------------------------------------------------------------
# 3. Python config
# ---------------------------------------------------------------------------

echo ""
echo "--- Configuracao Python ---"

if [[ "$HAS_PYPROJECT" == "true" ]]; then
  warn "pyproject.toml ja existe — nao sera sobrescrito"
  info "Adicione as deps de dev manualmente: ruff, pytest, mypy, pytest-mock"
else
  safe_copy "$REVIEWOPS_DIR/pyproject.toml" "pyproject.toml"
fi

# ---------------------------------------------------------------------------
# 4. Portal Docusaurus
# ---------------------------------------------------------------------------

echo ""
echo "--- Portal Docusaurus ---"

if [[ "$HAS_DOCS_SITE" == "true" ]]; then
  warn "docs-site/ ja existe — nao sera sobrescrito"
  info "Verifique se docusaurus-plugin-openapi-docs esta configurado"
else
  safe_copy_dir "$REVIEWOPS_DIR/docs-site" "./docs-site"
  if [[ "$DRY_RUN" == "false" ]]; then
    warn "Edite docs-site/docusaurus.config.ts e substitua os placeholders"
  fi
fi

# ---------------------------------------------------------------------------
# 5. Scripts auxiliares
# ---------------------------------------------------------------------------

echo ""
echo "--- Scripts auxiliares ---"

safe_mkdir "scripts"
safe_copy "$REVIEWOPS_DIR/scripts/export_openapi.py"   "scripts/export_openapi.py"
safe_copy "$REVIEWOPS_DIR/scripts/validate_config.py"   "scripts/validate_config.py"

# ---------------------------------------------------------------------------
# 6. Estrutura minima
# ---------------------------------------------------------------------------

echo ""
echo "--- Estrutura minima ---"

safe_mkdir "src"
safe_mkdir "tests"
safe_touch "src/__init__.py"
safe_touch "tests/__init__.py"

# ---------------------------------------------------------------------------
# 7. Makefile
# ---------------------------------------------------------------------------

echo ""
echo "--- Makefile ---"
safe_copy "$REVIEWOPS_DIR/Makefile" "Makefile"

# ---------------------------------------------------------------------------
# Resumo
# ---------------------------------------------------------------------------

echo ""
echo "======================================================"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  Dry-run concluido. Nenhum arquivo foi alterado."
  echo "  Remova --dry-run para executar de verdade."
else
  echo "  Setup concluido!"
  echo ""
  echo "  Proximos passos:"
  echo ""
  echo "    1. Edite .github/CODEOWNERS — substitua @org/team"
  echo "    2. Edite docs-site/docusaurus.config.ts — substitua placeholders"
  echo "    3. Edite scripts/export_openapi.py — aponte para sua app"
  echo "    4. Rode: make setup"
  echo "    5. Rode: make validate"
  echo "    6. Configure branch protection em main"
  echo "    7. Habilite GitHub Actions para aprovar PRs"
fi
echo "======================================================"
echo ""
