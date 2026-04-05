# docusaurus-reviewops

[![Pull Request CI](https://github.com/venysssssssssss/docusaurus-reviewops/actions/workflows/pr-ci.yml/badge.svg?branch=master)](https://github.com/venysssssssssss/docusaurus-reviewops/actions/workflows/pr-ci.yml)
[![Docs Deploy](https://github.com/venysssssssssss/docusaurus-reviewops/actions/workflows/docs-deploy.yml/badge.svg?branch=master)](https://github.com/venysssssssssss/docusaurus-reviewops/actions/workflows/docs-deploy.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

> **Idioma / Language / Idioma:**
> [Portugues](#-portugues) | [English](#-english) | [Espanol](#-espanol)

---

## 🇧🇷 Portugues

### O que e

**docusaurus-reviewops** e um sistema de governanca de Pull Requests + portal de documentacao viva para qualquer repositorio GitHub.

Aplique em um projeto novo ou existente e tenha imediatamente:

- **Quality gates** em todo PR — lint (`ruff`), tipos (`mypy`), testes (`pytest`), cobertura (≥ 80%), build do portal
- **Aprovacao automatica** de PRs de baixo risco apos CI green (fail-closed, 11 condicoes de rejeicao)
- **Portal Docusaurus v3** publicado automaticamente a cada merge em `master`
- **Versionamento de docs** congelado em cada release
- **Geracao de documentacao via LLM** (`make docs-gen`) com suporte a Ollama, Claude, OpenAI e Claude Code CLI

### Como funciona

```
PR aberto
 |
 v
pr-ci.yml ─────────── lint + tipos + testes + cobertura + build do portal
 |                     Permissao: somente leitura (contents: read)
 |                     Nunca tem write access
 v
pr-approval.yml ───── Se CI passou, avalia politica e aprova via API REST
 |                     Permissao: pull-requests: write
 |                     NUNCA faz checkout do codigo do PR
 v
Merge em master
 |
 v
docs-deploy.yml ───── Publica portal no GitHub Pages (< 5 min)
 |
 v
git tag v1.2.0
 |
 v
docs-version-pr.yml ─ Congela docs da release e abre PR automatico
```

### Pre-requisitos

| Ferramenta | Versao minima | Como instalar |
|-----------|--------------|---------------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Poetry | 1.8+ | `pip install poetry` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 9+ | `corepack enable && corepack prepare pnpm@latest --activate` |
| Git | qualquer | [git-scm.com](https://git-scm.com/) |
| GitHub CLI (`gh`) | 2.x | [cli.github.com](https://cli.github.com/) |

### Instalacao passo a passo

#### Passo 1 — Clone o repositorio

```bash
git clone https://github.com/venysssssssssss/docusaurus-reviewops.git
cd docusaurus-reviewops
```

#### Passo 2 — Instale as dependencias

```bash
make setup
```

Isso executa:
- `poetry install` — instala todas as dependencias Python (incluindo dev: ruff, mypy, pytest, pytest-cov)
- `pnpm --dir docs-site install` — instala as dependencias Node do portal Docusaurus

> **Solucao de problemas:** Se `pnpm` nao for encontrado, execute `corepack enable` primeiro.

#### Passo 3 — Configure variaveis de ambiente (opcional)

```bash
cp .env.example .env
# Edite .env com seu editor preferido
```

Variaveis relevantes:

| Variavel | Obrigatoria? | Para que serve |
|----------|-------------|----------------|
| `ANTHROPIC_API_KEY` | Nao | Geracao de docs via Claude (`make docs-gen`) |
| `OPENAI_API_KEY` | Nao | Geracao de docs via GPT-4o (`make docs-gen`) |
| `DOCGEN_PROVIDER` | Nao | Provider LLM: `ollama` (default), `anthropic`, `openai`, `claude-code` |

> **Sem API key:** O sistema funciona localmente com [Ollama](https://ollama.com/) instalado. Rode `ollama pull llama3.2` antes de `make docs-gen`.

#### Passo 4 — Valide a configuracao

```bash
make validate
```

Saida esperada:
```
[OK] Estrutura de arquivos
[OK] CODEOWNERS
[OK] docusaurus.config.ts
[OK] Git inicializado

Pronto para deploy!
```

> Se houver placeholders pendentes, o comando mostra exatamente o que substituir e um exemplo.

#### Passo 5 — Rode os testes

```bash
make test         # apenas testes
make coverage     # testes + cobertura (falha se < 80%)
make lint         # linting (ruff)
make typecheck    # type checking (mypy)
make all          # tudo de uma vez: lint + types + tests + docs build
```

#### Passo 6 — Suba o portal localmente

```bash
make docs-dev
# Acesse http://localhost:3000
```

#### Passo 7 — Configure o repositorio GitHub

**7.1 Habilitar GitHub Pages**

```
GitHub > Settings > Pages > Source: GitHub Actions
```

**7.2 Permissoes para workflows**

```
GitHub > Settings > Actions > General > Workflow permissions
  [x] Read and write permissions
  [x] Allow GitHub Actions to create and approve pull requests
```

**7.3 Criar labels operacionais**

```bash
gh label import .github/labels.yml
```

**7.4 Branch protection**

```
GitHub > Settings > Branches > Add rule
  Branch: master
  [x] Require status checks: quality-gates, docs-gates
  [x] Require conversation resolution
  [x] Block force pushes
```

#### Passo 8 — Instale os hooks de pre-commit (opcional mas recomendado)

```bash
poetry run pre-commit install
```

Isso configura hooks que rodam automaticamente antes de cada `git commit`:
- `ruff` — lint e format
- `detect-private-key` — previne commit acidental de secrets
- `no-commit-to-branch` — protege o branch `master`
- `mypy` — type checking

### Personalizar a politica de aprovacao

Edite as constantes em [.github/scripts/approval_policy.py](.github/scripts/approval_policy.py):

```python
# Labels que bloqueiam aprovacao automatica
BLOCKING_LABELS = {'security', 'breaking-change', 'db-migration', 'infra-change', 'needs-human-review'}

# Caminhos protegidos — PRs que tocam esses arquivos nao sao auto-aprovados
PROTECTED_PATTERNS = [r'^\.github/', r'^infra/', ...]

# Limites de tamanho
MAX_CHANGED_FILES = 30     # numero maximo de arquivos
MAX_TOTAL_DELTA = 800      # total de linhas adicionadas + removidas
MAX_NET_CHANGE = 400       # net change (|adicoes - remocoes|) para detectar rewrites
```

### Gerar documentacao via LLM

```bash
# Preview (nao escreve nada)
make docs-gen-preview

# Gerar e salvar
make docs-gen

# Com provider especifico
DOCGEN_PROVIDER=anthropic make docs-gen

# Opcoes avancadas
poetry run python -m scripts.docgen.cli --help
```

Providers suportados:
- **Ollama** (default, local, gratuito) — requer `ollama pull llama3.2`
- **Anthropic** — requer `ANTHROPIC_API_KEY`
- **OpenAI** — requer `OPENAI_API_KEY`
- **Claude Code CLI** — requer `claude` instalado

### Congelar versao de docs

```bash
git tag v1.0.0
git push origin v1.0.0
# workflow abre PR automatico com freeze documental
# revise e faca merge para publicar com dropdown de versoes
```

### Estrutura de arquivos

```
docusaurus-reviewops/
├── .github/
│   ├── scripts/
│   │   ├── approval_policy.py   # politica de aprovacao (fail-closed)
│   │   └── docs_guardrails.py   # freshness de docs (exige docs junto com codigo)
│   ├── workflows/
│   │   ├── pr-ci.yml            # quality gates (nao privilegiado)
│   │   ├── pr-approval.yml      # aprovacao (privilegiado, sem checkout do PR)
│   │   ├── docs-deploy.yml      # deploy no GitHub Pages
│   │   └── docs-version-pr.yml  # congelamento em releases
│   ├── ISSUE_TEMPLATE/          # templates de issue (bug, feature, config)
│   ├── CODEOWNERS               # revisores por caminho
│   ├── dependabot.yml           # atualizacao automatica de dependencias
│   └── PULL_REQUEST_TEMPLATE.md # checklist para novos PRs
├── docs-site/                   # portal Docusaurus v3
│   ├── docs/                    # conteudo curado em Markdown
│   ├── src/theme/               # componentes swizzled (ESM-only)
│   ├── openapi/                 # schema OpenAPI exportado
│   └── docusaurus.config.ts     # configuracao do portal
├── scripts/
│   ├── docgen/                  # geracao de docs via LLM (6 generators, 5 providers)
│   ├── export_openapi.py        # exporta schema de app FastAPI
│   └── validate_config.py       # verifica prontidao para deploy
├── tests/                       # 182+ testes unitarios
├── .docgen.yml                  # config do sistema docgen
├── .env.example                 # variaveis de ambiente documentadas
├── .pre-commit-config.yaml      # hooks de pre-commit
├── LICENSE                      # MIT
├── SECURITY.md                  # politica de seguranca e reporte de vulnerabilidades
└── pyproject.toml               # dependencias e config de ferramentas
```

### Comandos de referencia

| Comando | O que faz |
|---------|-----------|
| `make setup` | Instala todas as dependencias |
| `make lint` | `ruff check .` |
| `make typecheck` | `mypy src .github/scripts scripts` |
| `make test` | `pytest tests/ -v` |
| `make coverage` | pytest + cobertura >= 80% |
| `make docs` | Export OpenAPI + API docs + build do portal |
| `make docs-dev` | Servidor local em localhost:3000 |
| `make docs-gen` | Gera docs via LLM |
| `make docs-gen-preview` | Preview sem escrever arquivos |
| `make validate` | Verifica placeholders e prontidao |
| `make all` | lint + typecheck + test + docs |
| `make clean` | Remove artefatos de build |

---

## 🇺🇸 English

### What is it

**docusaurus-reviewops** is a Pull Request governance system combined with a live documentation portal for any GitHub repository.

Apply it to a new or existing project and immediately get:

- **Quality gates** on every PR — lint (`ruff`), types (`mypy`), tests (`pytest`), coverage (≥ 80%), portal build
- **Automatic approval** of low-risk PRs after green CI (fail-closed, 11 rejection conditions)
- **Docusaurus v3 portal** automatically published on every merge to `master`
- **Versioned docs** frozen at each release
- **LLM documentation generation** (`make docs-gen`) supporting Ollama, Claude, OpenAI, and Claude Code CLI

### How it works

```
PR opened
 |
 v
pr-ci.yml ─────────── lint + types + tests + coverage + portal build
 |                     Permission: read-only (contents: read)
 |                     No write access
 v
pr-approval.yml ───── If CI passed, evaluates policy and approves via REST API
 |                     Permission: pull-requests: write
 |                     NEVER checks out PR code
 v
Merge to master
 |
 v
docs-deploy.yml ───── Publishes portal to GitHub Pages (< 5 min)
 |
 v
git tag v1.2.0
 |
 v
docs-version-pr.yml ─ Freezes release docs and opens automatic PR
```

### Prerequisites

| Tool | Minimum version | How to install |
|------|----------------|----------------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Poetry | 1.8+ | `pip install poetry` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 9+ | `corepack enable && corepack prepare pnpm@latest --activate` |
| Git | any | [git-scm.com](https://git-scm.com/) |
| GitHub CLI (`gh`) | 2.x | [cli.github.com](https://cli.github.com/) |

### Step-by-step installation

#### Step 1 — Clone the repository

```bash
git clone https://github.com/venysssssssssss/docusaurus-reviewops.git
cd docusaurus-reviewops
```

#### Step 2 — Install dependencies

```bash
make setup
```

This runs:
- `poetry install` — installs all Python dependencies (including dev: ruff, mypy, pytest, pytest-cov)
- `pnpm --dir docs-site install` — installs Node.js dependencies for the Docusaurus portal

> **Troubleshooting:** If `pnpm` is not found, run `corepack enable` first.

#### Step 3 — Configure environment variables (optional)

```bash
cp .env.example .env
# Edit .env with your preferred editor
```

Key variables:

| Variable | Required? | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | No | Doc generation via Claude (`make docs-gen`) |
| `OPENAI_API_KEY` | No | Doc generation via GPT-4o (`make docs-gen`) |
| `DOCGEN_PROVIDER` | No | LLM provider: `ollama` (default), `anthropic`, `openai`, `claude-code` |

> **No API key:** The system works locally with [Ollama](https://ollama.com/) installed. Run `ollama pull llama3.2` before `make docs-gen`.

#### Step 4 — Validate the configuration

```bash
make validate
```

Expected output:
```
[OK] File structure
[OK] CODEOWNERS
[OK] docusaurus.config.ts
[OK] Git initialized

Ready to deploy!
```

> If there are pending placeholders, the command shows exactly what to replace with an example.

#### Step 5 — Run the tests

```bash
make test         # tests only
make coverage     # tests + coverage (fails if < 80%)
make lint         # linting (ruff)
make typecheck    # type checking (mypy)
make all          # everything: lint + types + tests + docs build
```

#### Step 6 — Run the portal locally

```bash
make docs-dev
# Visit http://localhost:3000
```

#### Step 7 — Configure your GitHub repository

**7.1 Enable GitHub Pages**

```
GitHub > Settings > Pages > Source: GitHub Actions
```

**7.2 Workflow permissions**

```
GitHub > Settings > Actions > General > Workflow permissions
  [x] Read and write permissions
  [x] Allow GitHub Actions to create and approve pull requests
```

**7.3 Create operational labels**

```bash
gh label import .github/labels.yml
```

**7.4 Branch protection**

```
GitHub > Settings > Branches > Add rule
  Branch: master
  [x] Require status checks: quality-gates, docs-gates
  [x] Require conversation resolution
  [x] Block force pushes
```

#### Step 8 — Install pre-commit hooks (optional but recommended)

```bash
poetry run pre-commit install
```

Hooks that run automatically before each `git commit`:
- `ruff` — lint and format
- `detect-private-key` — prevents accidental secret commits
- `no-commit-to-branch` — protects the `master` branch
- `mypy` — type checking

### Customizing the approval policy

Edit the constants in [.github/scripts/approval_policy.py](.github/scripts/approval_policy.py):

```python
# Labels that block automatic approval
BLOCKING_LABELS = {'security', 'breaking-change', 'db-migration', 'infra-change', 'needs-human-review'}

# Protected paths — PRs touching these files are never auto-approved
PROTECTED_PATTERNS = [r'^\.github/', r'^infra/', ...]

# Size limits
MAX_CHANGED_FILES = 30     # maximum number of files
MAX_TOTAL_DELTA = 800      # total lines added + removed
MAX_NET_CHANGE = 400       # net change (|additions - deletions|) to detect rewrites
```

### Generating documentation via LLM

```bash
# Preview (writes nothing)
make docs-gen-preview

# Generate and save
make docs-gen

# With a specific provider
DOCGEN_PROVIDER=anthropic make docs-gen

# Advanced options
poetry run python -m scripts.docgen.cli --help
```

Supported providers:
- **Ollama** (default, local, free) — requires `ollama pull llama3.2`
- **Anthropic** — requires `ANTHROPIC_API_KEY`
- **OpenAI** — requires `OPENAI_API_KEY`
- **Claude Code CLI** — requires `claude` CLI installed

### Freezing a docs version

```bash
git tag v1.0.0
git push origin v1.0.0
# workflow opens automatic PR with frozen docs
# review and merge to publish with version dropdown
```

### What the bot never approves

- PRs with labels: `security`, `breaking-change`, `db-migration`, `infra-change`, `needs-human-review`
- PRs touching: `.github/`, `infra/`, `terraform/`, `helm/`, `migrations/`, `Dockerfile`, lockfiles
- Draft PRs, fork PRs, PRs with `CHANGES_REQUESTED`, > 30 files, > 800 lines, or > 400 net change

### Security model

The privileged workflow (`pr-approval.yml`) **never executes code from the PR**. It is triggered by `workflow_run` (after CI completes) and only reads PR metadata via the GitHub REST API. This eliminates the class of attacks where a malicious PR modifies workflows to escalate permissions.

See [SECURITY.md](SECURITY.md) for the full security policy and vulnerability reporting procedure.

### Command reference

| Command | What it does |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make lint` | `ruff check .` |
| `make typecheck` | `mypy src .github/scripts scripts` |
| `make test` | `pytest tests/ -v` |
| `make coverage` | pytest + coverage >= 80% |
| `make docs` | Export OpenAPI + API docs + portal build |
| `make docs-dev` | Local server at localhost:3000 |
| `make docs-gen` | Generate docs via LLM |
| `make docs-gen-preview` | Preview without writing files |
| `make validate` | Check placeholders and readiness |
| `make all` | lint + typecheck + test + docs |
| `make clean` | Remove build artifacts |

---

## 🇪🇸 Espanol

### Que es

**docusaurus-reviewops** es un sistema de gobernanza de Pull Requests combinado con un portal de documentacion viva para cualquier repositorio GitHub.

Aplicalo en un proyecto nuevo o existente y obtendras de inmediato:

- **Quality gates** en cada PR — lint (`ruff`), tipos (`mypy`), pruebas (`pytest`), cobertura (≥ 80%), build del portal
- **Aprobacion automatica** de PRs de bajo riesgo tras CI verde (fail-closed, 11 condiciones de rechazo)
- **Portal Docusaurus v3** publicado automaticamente en cada merge a `master`
- **Versionado de docs** congelado en cada release
- **Generacion de documentacion via LLM** (`make docs-gen`) con soporte para Ollama, Claude, OpenAI y Claude Code CLI

### Como funciona

```
PR abierto
 |
 v
pr-ci.yml ─────────── lint + tipos + pruebas + cobertura + build del portal
 |                     Permiso: solo lectura (contents: read)
 |                     Sin acceso de escritura
 v
pr-approval.yml ───── Si CI paso, evalua politica y aprueba via API REST
 |                     Permiso: pull-requests: write
 |                     NUNCA hace checkout del codigo del PR
 v
Merge a master
 |
 v
docs-deploy.yml ───── Publica portal en GitHub Pages (< 5 min)
 |
 v
git tag v1.2.0
 |
 v
docs-version-pr.yml ─ Congela docs del release y abre PR automatico
```

### Requisitos previos

| Herramienta | Version minima | Como instalar |
|-------------|---------------|---------------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Poetry | 1.8+ | `pip install poetry` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 9+ | `corepack enable && corepack prepare pnpm@latest --activate` |
| Git | cualquiera | [git-scm.com](https://git-scm.com/) |
| GitHub CLI (`gh`) | 2.x | [cli.github.com](https://cli.github.com/) |

### Instalacion paso a paso

#### Paso 1 — Clona el repositorio

```bash
git clone https://github.com/venysssssssssss/docusaurus-reviewops.git
cd docusaurus-reviewops
```

#### Paso 2 — Instala las dependencias

```bash
make setup
```

Esto ejecuta:
- `poetry install` — instala todas las dependencias Python (incluye dev: ruff, mypy, pytest, pytest-cov)
- `pnpm --dir docs-site install` — instala las dependencias Node.js del portal Docusaurus

> **Solucion de problemas:** Si `pnpm` no se encuentra, ejecuta `corepack enable` primero.

#### Paso 3 — Configura las variables de entorno (opcional)

```bash
cp .env.example .env
# Edita .env con tu editor preferido
```

Variables relevantes:

| Variable | Requerida? | Para que sirve |
|----------|-----------|----------------|
| `ANTHROPIC_API_KEY` | No | Generacion de docs via Claude (`make docs-gen`) |
| `OPENAI_API_KEY` | No | Generacion de docs via GPT-4o (`make docs-gen`) |
| `DOCGEN_PROVIDER` | No | Provider LLM: `ollama` (default), `anthropic`, `openai`, `claude-code` |

> **Sin API key:** El sistema funciona localmente con [Ollama](https://ollama.com/) instalado. Ejecuta `ollama pull llama3.2` antes de `make docs-gen`.

#### Paso 4 — Valida la configuracion

```bash
make validate
```

Salida esperada:
```
[OK] Estructura de archivos
[OK] CODEOWNERS
[OK] docusaurus.config.ts
[OK] Git inicializado

Listo para deploy!
```

#### Paso 5 — Ejecuta las pruebas

```bash
make test         # solo pruebas
make coverage     # pruebas + cobertura (falla si < 80%)
make lint         # linting (ruff)
make typecheck    # verificacion de tipos (mypy)
make all          # todo: lint + tipos + pruebas + build de docs
```

#### Paso 6 — Levanta el portal localmente

```bash
make docs-dev
# Visita http://localhost:3000
```

#### Paso 7 — Configura el repositorio GitHub

**7.1 Habilitar GitHub Pages**

```
GitHub > Settings > Pages > Source: GitHub Actions
```

**7.2 Permisos para workflows**

```
GitHub > Settings > Actions > General > Workflow permissions
  [x] Read and write permissions
  [x] Allow GitHub Actions to create and approve pull requests
```

**7.3 Crear labels operacionales**

```bash
gh label import .github/labels.yml
```

**7.4 Proteccion de branch**

```
GitHub > Settings > Branches > Add rule
  Branch: master
  [x] Require status checks: quality-gates, docs-gates
  [x] Require conversation resolution
  [x] Block force pushes
```

#### Paso 8 — Instala los hooks de pre-commit (opcional pero recomendado)

```bash
poetry run pre-commit install
```

Hooks que se ejecutan automaticamente antes de cada `git commit`:
- `ruff` — lint y format
- `detect-private-key` — previene commits accidentales de secrets
- `no-commit-to-branch` — protege el branch `master`
- `mypy` — verificacion de tipos

### Personalizar la politica de aprobacion

Edita las constantes en [.github/scripts/approval_policy.py](.github/scripts/approval_policy.py):

```python
# Labels que bloquean la aprobacion automatica
BLOCKING_LABELS = {'security', 'breaking-change', 'db-migration', 'infra-change', 'needs-human-review'}

# Rutas protegidas — PRs que tocan estos archivos nunca se auto-aprueban
PROTECTED_PATTERNS = [r'^\.github/', r'^infra/', ...]

# Limites de tamano
MAX_CHANGED_FILES = 30     # numero maximo de archivos
MAX_TOTAL_DELTA = 800      # total de lineas anadidas + eliminadas
MAX_NET_CHANGE = 400       # cambio neto (|adiciones - eliminaciones|) para detectar rewrites
```

### Generar documentacion via LLM

```bash
# Vista previa (no escribe nada)
make docs-gen-preview

# Generar y guardar
make docs-gen

# Con un provider especifico
DOCGEN_PROVIDER=anthropic make docs-gen

# Opciones avanzadas
poetry run python -m scripts.docgen.cli --help
```

Providers soportados:
- **Ollama** (default, local, gratuito) — requiere `ollama pull llama3.2`
- **Anthropic** — requiere `ANTHROPIC_API_KEY`
- **OpenAI** — requiere `OPENAI_API_KEY`
- **Claude Code CLI** — requiere CLI `claude` instalado

### Congelar una version de docs

```bash
git tag v1.0.0
git push origin v1.0.0
# el workflow abre un PR automatico con docs congelados
# revisa y haz merge para publicar con dropdown de versiones
```

### Lo que el bot nunca aprueba

- PRs con labels: `security`, `breaking-change`, `db-migration`, `infra-change`, `needs-human-review`
- PRs que tocan: `.github/`, `infra/`, `terraform/`, `helm/`, `migrations/`, `Dockerfile`, lockfiles
- PRs draft, de fork, con `CHANGES_REQUESTED`, > 30 archivos, > 800 lineas, o > 400 net change

### Modelo de seguridad

El workflow privilegiado (`pr-approval.yml`) **nunca ejecuta codigo del PR**. Es disparado por `workflow_run` (tras completar el CI) y solo lee metadatos del PR via la API REST de GitHub. Esto elimina la clase de ataques donde un PR malicioso modifica workflows para escalar permisos.

Ver [SECURITY.md](SECURITY.md) para la politica de seguridad completa y el procedimiento de reporte de vulnerabilidades.

### Referencia de comandos

| Comando | Que hace |
|---------|----------|
| `make setup` | Instala todas las dependencias |
| `make lint` | `ruff check .` |
| `make typecheck` | `mypy src .github/scripts scripts` |
| `make test` | `pytest tests/ -v` |
| `make coverage` | pytest + cobertura >= 80% |
| `make docs` | Export OpenAPI + API docs + build del portal |
| `make docs-dev` | Servidor local en localhost:3000 |
| `make docs-gen` | Genera docs via LLM |
| `make docs-gen-preview` | Vista previa sin escribir archivos |
| `make validate` | Verifica placeholders y estado de preparacion |
| `make all` | lint + typecheck + test + docs |
| `make clean` | Elimina artefactos de build |

---

## Stack

- Python 3.12 + ruff + pytest + pytest-cov + mypy
- GitHub Actions (4 workflows + pre-commit)
- Docusaurus v3.9.2 + TypeScript + pnpm
- Plugins: OpenAPI docs, Mermaid, local search, webpack optimizations
- Deploy: GitHub Pages
- LLM: Ollama / Anthropic Claude / OpenAI GPT-4o / Claude Code CLI

## Licenca / License / Licencia

[MIT](LICENSE) — venysssssssssss
