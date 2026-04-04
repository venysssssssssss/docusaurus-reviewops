# docusaurus-reviewops

Automacao de revisao de PR + portal de documentacao versionado para repositorios GitHub.

Aplique em qualquer repo — novo ou existente — e tenha:
- **Quality gates** em todo PR (lint, tipos, testes, docs)
- **Aprovacao automatica** de PRs de baixo risco
- **Portal Docusaurus** publicado a cada merge em main
- **Versionamento** de docs congelado em cada release

> Automacao acelera. Governanca continua no comando.

---

## Como funciona

```
PR aberto
 |
 v
pr-ci.yml ─────────── Roda lint, testes, mypy, build do portal
 |                     Permissao: somente leitura (contents: read)
 v
pr-approval.yml ───── Se CI passou, avalia politica e aprova
 |                     Permissao: pull-requests: write
 |                     NUNCA faz checkout do codigo do PR
 v
Merge em main
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

### O que o bot nunca aprova

- PRs com labels: `security`, `breaking-change`, `db-migration`, `infra-change`, `needs-human-review`
- PRs que tocam: `.github/`, `infra/`, `terraform/`, `migrations/`, `Dockerfile`, lockfiles
- PRs draft, de fork, com `CHANGES_REQUESTED`, > 30 arquivos ou > 800 linhas

---

## Inicio rapido

### Projeto novo

```bash
git clone <este-repo> meu-projeto && cd meu-projeto
make setup        # instala Python + Node deps
make validate     # verifica se ha placeholders pendentes
make test         # roda lint + testes + build do portal
```

### Projeto existente

```bash
git clone <este-repo> /tmp/reviewops
cd /caminho/do/seu/projeto
bash /tmp/reviewops/scripts/setup_reviewops.sh
```

O script detecta o que ja existe e nunca sobrescreve sem perguntar.
Use `--dry-run` para ver o que seria feito sem alterar nada.

---

## Configuracao do GitHub

Apos copiar os arquivos, configure o repositorio:

**1. Branch protection em `main`**

```
Settings > Branches > Add rule > main
  [x] Require status checks: quality-gates, docs-gates
  [x] Require conversation resolution
  [x] Block force pushes
```

**2. Permitir bot aprovar PRs**

```
Settings > Actions > General
  [x] Allow GitHub Actions to create and approve pull requests
```

**3. Criar labels**

```bash
gh label import .github/labels.yml
```

**4. Substituir placeholders**

Execute `make validate` para ver a lista completa, ou edite manualmente:

| Arquivo | O que substituir |
|---|---|
| `.github/CODEOWNERS` | `@org/team` pelos handles reais |
| `docs-site/docusaurus.config.ts` | URL, nome da org, titulo do portal |
| `scripts/export_openapi.py` | Import da sua app FastAPI |

---

## Comandos

Todos os comandos estao no `Makefile`:

| Comando | O que faz |
|---|---|
| `make setup` | Instala dependencias Python e Node |
| `make lint` | Roda ruff check |
| `make typecheck` | Roda mypy |
| `make test` | Roda pytest |
| `make docs` | Exporta OpenAPI + gera API docs + build do portal |
| `make docs-dev` | Sobe servidor local do portal (localhost:3000) |
| `make validate` | Verifica placeholders pendentes e prontidao para deploy |
| `make all` | lint + typecheck + test + docs (tudo de uma vez) |

---

## Estrutura

```
.github/
  scripts/
    approval_policy.py    # logica de aprovacao (11 condicoes de rejeicao)
    docs_guardrails.py    # falha se codigo publico mudou sem docs
  workflows/
    pr-ci.yml             # quality gates (nao privilegiado)
    pr-approval.yml       # aprovacao (privilegiado, sem checkout do PR)
    docs-deploy.yml       # deploy GitHub Pages
    docs-version-pr.yml   # freeze documental em releases
  CODEOWNERS              # quem revisa o que
  labels.yml              # labels operacionais

docs-site/                # portal Docusaurus v3
  docs/                   # conteudo curado (markdown)
  openapi/                # schema OpenAPI exportado
  docusaurus.config.ts    # configuracao do portal

scripts/
  export_openapi.py       # exporta schema da app FastAPI
  setup_reviewops.sh      # instala em repo existente
  validate_config.py      # verifica prontidao para deploy

tests/                    # testes unitarios dos scripts
```

---

## Customizacao

### Ajustar politica de aprovacao

Edite `.github/scripts/approval_policy.py` — as constantes no topo do arquivo:

```python
BLOCKING_LABELS = {'security', 'breaking-change', ...}  # labels que bloqueiam
PROTECTED_PATTERNS = [r'^\.github/', ...]                # caminhos protegidos
MAX_CHANGED_FILES = 30                                    # limite de arquivos
MAX_TOTAL_DELTA = 800                                     # limite de linhas
```

### Ajustar guardrails de docs

Edite `.github/scripts/docs_guardrails.py`:

```python
PUBLIC_CHANGE_PREFIXES = ['src/', 'app/', 'api/', ...]   # codigo publico
DOC_TOUCH_PREFIXES = ['docs-site/docs/', 'README.md', ...] # docs validos
```

### Congelar versao de docs

O congelamento e automatico ao criar uma tag:

```bash
git tag v1.0.0 && git push origin v1.0.0
# -> workflow abre PR com freeze documental
# -> revise e faca merge para publicar
```

Apos o primeiro freeze, descomente o bloco de versionamento em `docusaurus.config.ts`.

---

## Documentacao do projeto

| Documento | Conteudo |
|-----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura, security model, component map |
| [docs/DESIGN-SYSTEM.md](docs/DESIGN-SYSTEM.md) | Paleta de cores, componentes CSS, assets |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Como contribuir, convencoes de docs |
| [docs/SPRINT-LOG.md](docs/SPRINT-LOG.md) | Log detalhado da sprint de melhorias |
| [CHANGELOG.md](CHANGELOG.md) | Historico de mudancas |

## Stack

- Python 3.12 + ruff + pytest + mypy
- GitHub Actions (4 workflows)
- Docusaurus v3.9.2 + TypeScript + pnpm
- Plugins: OpenAPI docs, Mermaid, busca local, webpack optimizations
- Deploy: GitHub Pages

## Licenca

MIT
