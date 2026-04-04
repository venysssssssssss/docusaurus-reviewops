# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/).

## [0.2.0] - 2026-04-04

### Adicionado

- Busca local offline (`@easyops-cn/docusaurus-search-local`) — Ctrl+K
- Diagramas Mermaid nativos (`@docusaurus/theme-mermaid`)
- Favicon SVG com identidade visual (static/img/favicon.svg)
- Social card PNG para OG/Twitter cards (static/img/social-card.png)
- robots.txt para SEO
- Pagina 404 customizada em portugues (src/pages/404.tsx)
- Announcement bar configuravel em docusaurus.config.ts
- `colorMode.respectPrefersColorScheme` para deteccao automatica de tema
- SEO metadata (keywords) no config
- Frontmatter completo (description, keywords, sidebar_position) em todos os docs
- Admonitions (:::tip, :::warning, :::danger, :::info, :::note) em todos os docs
- Diagramas Mermaid substituindo ASCII art (architecture, deploy)
- Titulos em todos os code blocks
- Secao "Veja tambem" com cross-links em todos os docs
- `_category_.json` para ordenacao deterministica de sidebar
- CSS expandido (~200 linhas): navbar frosted glass, sidebar accent, cards hover, hero gradient, tabelas responsivas, footer estilizado
- Bundle splitting: OpenAPI theme em chunk separado (openapi-vendor)
- 15 novos testes (73 total)
- Documentacao do projeto: ARCHITECTURE.md, DESIGN-SYSTEM.md, CONTRIBUTING.md, SPRINT-LOG.md

### Corrigido

- Theme swizzles ESM para SchemaTabs, ApiLogo, Export (corrige "exports is not defined")
- Webpack plugin aplica regra CJS tanto em client quanto server (corrige SSG crash)
- Webpack plugin usa config.module.rules.unshift em vez de merge (garante prioridade)

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
