# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/).

## [0.1.0] - 2026-04-03

### Adicionado

- Workflow `pr-ci.yml` com quality-gates (ruff, mypy, pytest) e docs-gates (freshness, OpenAPI, build)
- Workflow `pr-approval.yml` com agente de aprovacao automatica (fail_closed)
- Workflow `docs-deploy.yml` para publicacao automatica no GitHub Pages
- Workflow `docs-version-pr.yml` para congelamento documental em releases
- Script `approval_policy.py` com 11 condicoes de rejeicao
- Script `docs_guardrails.py` para validacao de freshness de documentacao
- Script `export_openapi.py` para exportacao de schema FastAPI
- Script `validate_config.py` para verificacao de prontidao de deploy
- Script `setup_reviewops.sh` para instalacao em repositorios existentes
- Portal Docusaurus v3 com plugin OpenAPI, TypeScript e versionamento
- Templates de docs: architecture, standards, runbooks, ADR
- CODEOWNERS com mapeamento de areas criticas
- Labels operacionais para governanca de PRs
- Makefile com comandos unificados
- Suite de testes unitarios (37 testes)
