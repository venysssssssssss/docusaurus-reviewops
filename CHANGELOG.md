# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/).

## [0.4.0] - 2026-04-04

### Adicionado

- `LICENSE` (MIT) — licenca formal do projeto
- `SECURITY.md` — politica de seguranca, modelo de privilegios, instrucoes de reporte via GitHub Security Advisory
- `.github/dependabot.yml` — atualizacao automatica semanal de deps: pip, npm e github-actions;
  comentario de design explicando por que PRs do Dependabot exigem revisao humana (caminhos protegidos)
- `.env.example` — referencia completa de variaveis de ambiente (API keys, provider docgen, FastAPI module)
- `.github/PULL_REQUEST_TEMPLATE.md` — checklist obrigatorio de qualidade, docs, seguranca e convencoes
- `.github/ISSUE_TEMPLATE/bug_report.yml` — formulario estruturado (componente, logs, ambiente)
- `.github/ISSUE_TEMPLATE/feature_request.yml` — formulario com motivacao e alternativas
- `.github/ISSUE_TEMPLATE/config.yml` — desabilita issues em branco; redireciona para Advisory e Discussions
- `pytest-cov ^6.0` como dependencia de desenvolvimento
- `make coverage` — target que roda pytest com relatorio de cobertura e gate de 80%
- `[tool.coverage.*]` em `pyproject.toml` — configuracao de cobertura com `fail_under=80`, `branch=True`
- Etapa de cobertura no CI (`pr-ci.yml`): `--cov-fail-under=80`, job summary em markdown, artifact `coverage-report.xml`
- Badges no README: CI, Docs Deploy, Python 3.12, MIT
- README trilingual completo (PT / EN / ES) — passo a passo completo de instalacao, configuracao e uso
- `.pre-commit-config.yaml` — hooks: `ruff`, `ruff-format`, `check-yaml`, `detect-private-key`,
  `no-commit-to-branch (master)`, `mypy`
- `MAX_NET_CHANGE = 400` em `approval_policy.py` — detecta rewrites mascarados como refactors neutros
  (ex: 500 add + 300 del = 800 delta mas 200 net, que passa; 500 add + 50 del = 550 delta mas 450 net, que reprovaria)
- `AREA_DOC_MAP` em `docs_guardrails.py` — mapeamento semantico area-de-codigo -> secao-de-docs;
  mensagem de erro agora sugere a secao correta em vez de apenas falhar
- 2 novos testes para deteccao de net-zero: `test_large_net_change_rejected` e
  `test_balanced_refactor_passes_net_check` (184 testes no total)

### Melhorado

- `docs-site/docs/architecture/overview.md` — reescrita completa com sistema real:
  diagramas mermaid de fluxo de seguranca, componentes docgen, estrutura de diretorios
- `docs-site/docs/standards/coding-standards.md` — baseada no `pyproject.toml` real:
  regras ruff ativas, config mypy, gate de cobertura, convencoes de dataclass e NoReturn
- `docs-site/docs/runbooks/deploy.md` — setup inicial GitHub Pages passo a passo,
  URL real do portal, tabela de troubleshooting expandida

### Corrigido

- `.gitignore` — adicionada excecao `!.env.example` para que o arquivo de exemplo seja rastreado pelo git
  (era capturado pelo padrao `.env.*`)

## [0.3.0] - 2026-04-04

### Adicionado

- Sistema `docgen` — gerador de documentacao via LLM com 5 providers: Ollama (local),
  Anthropic Claude, OpenAI, Claude Code CLI e Mock (testes)
- 6 generators: architecture, coding standards, runbook, ADR, changelog, API enricher
- Cache incremental por SHA256 (`.docgen-cache/`) — evita chamadas LLM desnecessarias
- Cost tracking real: tokens LLM capturados e custo calculado via `estimate_cost()`,
  exibido no sumario do CLI (`~$0.04`)
- `make docs-gen` e `make docs-gen-preview` no Makefile
- `.docgen.yml` com interpolacao de env vars (`${ANTHROPIC_API_KEY}`)
- Workflow advisory-only `docs-gen.yml` — posta sugestoes como comentario de PR, nunca bloqueia
- Validacao de markdown Docusaurus-compativel (frontmatter, admonitions, code fences, sem TODO)
- 22 novos testes para ADR, Changelog, APIEnricher, Standards e Runbook generators
- Estrategia de merge `preserve` como padrao — nunca sobrescreve conteudo humano

### Corrigido

- Mypy: erro "source file found twice" em `git_history.py` — adicionado `scripts/__init__.py`
  para tornar `scripts/` um pacote Python proprio
- `types-pyyaml` adicionado como dep de desenvolvimento para cobertura mypy completa

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
