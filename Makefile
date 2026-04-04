.PHONY: setup lint typecheck test docs docs-dev docs-gen docs-gen-preview validate all clean help

# Detecta se esta dentro de um venv ou precisa usar poetry run
PYTHON := $(shell if [ -n "$$VIRTUAL_ENV" ]; then echo python; elif command -v poetry > /dev/null 2>&1; then echo poetry run python; else echo python3; fi)
PYTEST := $(shell if [ -n "$$VIRTUAL_ENV" ]; then echo pytest; elif command -v poetry > /dev/null 2>&1; then echo poetry run pytest; else echo pytest; fi)
RUFF   := $(shell if [ -n "$$VIRTUAL_ENV" ]; then echo ruff; elif command -v poetry > /dev/null 2>&1; then echo poetry run ruff; else echo ruff; fi)
MYPY   := $(shell if [ -n "$$VIRTUAL_ENV" ]; then echo mypy; elif command -v poetry > /dev/null 2>&1; then echo poetry run mypy; else echo mypy; fi)

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Instala dependencias Python e Node
	@echo "--- Instalando dependencias Python ---"
	@if command -v poetry > /dev/null 2>&1; then \
		poetry install --no-interaction; \
	elif [ -f ".venv/bin/pip" ]; then \
		.venv/bin/pip install -e ".[dev]" 2>/dev/null || \
		.venv/bin/pip install ruff pytest mypy pytest-mock; \
	else \
		echo "Criando venv..."; \
		python3 -m venv .venv && \
		.venv/bin/pip install ruff pytest mypy pytest-mock; \
	fi
	@echo ""
	@echo "--- Instalando dependencias do portal ---"
	@if command -v pnpm > /dev/null 2>&1; then \
		pnpm --dir docs-site install; \
	elif command -v corepack > /dev/null 2>&1; then \
		corepack enable && pnpm --dir docs-site install; \
	else \
		echo "ERRO: pnpm nao encontrado. Instale Node 22+ e rode: corepack enable"; \
		exit 1; \
	fi
	@echo ""
	@echo "Setup concluido. Rode 'make validate' para verificar placeholders."

lint: ## Roda ruff check (lint)
	$(RUFF) check .

lint-fix: ## Roda ruff check --fix (auto-corrige)
	$(RUFF) check . --fix

typecheck: ## Roda mypy no src e scripts
	$(MYPY) src .github/scripts scripts

test: ## Roda pytest
	$(PYTEST) tests/ -v

docs: ## Exporta OpenAPI + gera API docs + build do portal
	@echo "--- Exportando OpenAPI ---"
	$(PYTHON) scripts/export_openapi.py
	@echo ""
	@echo "--- Gerando API reference ---"
	pnpm --dir docs-site gen-api
	@echo ""
	@echo "--- Build do portal ---"
	pnpm --dir docs-site build
	@echo ""
	@echo "Build concluido em docs-site/build/"

docs-dev: ## Sobe servidor local do portal (localhost:3000)
	@$(PYTHON) scripts/export_openapi.py 2>/dev/null || true
	@pnpm --dir docs-site gen-api 2>/dev/null || true
	pnpm --dir docs-site start

docs-typecheck: ## Roda TypeScript check no portal
	pnpm --dir docs-site typecheck

validate: ## Verifica placeholders pendentes e prontidao para deploy
	$(PYTHON) scripts/validate_config.py

docs-gen: ## Gera documentacao via LLM (usa .docgen.yml)
	$(PYTHON) -m scripts.docgen.cli

docs-gen-preview: ## Pre-visualiza docs gerados (nao escreve)
	$(PYTHON) -m scripts.docgen.cli --preview --verbose

all: lint typecheck test docs ## Roda tudo: lint + types + tests + docs build

clean: ## Limpa artefatos de build
	rm -rf docs-site/build docs-site/.docusaurus reports .mypy_cache .ruff_cache .pytest_cache
	rm -rf docs-site/docs/api
	@echo "Limpo."
