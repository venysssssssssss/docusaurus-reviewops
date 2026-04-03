# docusaurus-reviewops

Sistema de governanca de PR e documentacao viva para repositorios GitHub.

## Contexto

Este repositorio implementa o blueprint de excelencia:
- **Agente de revisao automatica de PR** — aprova PRs elegiveis apos quality gates green
- **Portal Docusaurus versionado** — documentacao viva publicada no GitHub Pages

## Stack

- Python 3.12 + Poetry
- GitHub Actions (4 workflows)
- Docusaurus v3 + TypeScript + pnpm
- Plugin OpenAPI: docusaurus-plugin-openapi-docs

## Estrutura critica

```
.github/scripts/approval_policy.py   # logica de aprovacao
.github/scripts/docs_guardrails.py   # freshness de docs
.github/workflows/pr-ci.yml          # quality gates (nao privilegiado)
.github/workflows/pr-approval.yml    # aprovacao (privilegiado via workflow_run)
.github/workflows/docs-deploy.yml    # deploy do portal
.github/workflows/docs-version-pr.yml # freeze documental em releases
docs-site/                           # portal Docusaurus
scripts/export_openapi.py            # exporta schema FastAPI
```

## Principios de seguranca

1. Workflow privilegiado NUNCA faz checkout do codigo do PR
2. `fail_closed` — na duvida, nao aprova
3. Labels bloqueantes: security, breaking-change, db-migration, infra-change, needs-human-review
4. Caminhos protegidos: .github/, infra/, terraform/, helm/, migrations/, alembic/

## Comandos uteis

```bash
# Backend
poetry install
poetry run ruff check .
poetry run pytest
poetry run mypy src .github/scripts

# Portal
pnpm --dir docs-site install
pnpm --dir docs-site build
pnpm --dir docs-site start     # dev server local

# Setup em repo existente
bash scripts/setup_reviewops.sh
```
