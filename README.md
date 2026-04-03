# docusaurus-reviewops

**Agente de revisao e aprovacao automatica de PR + portal Docusaurus versionado**

Drop-in de governanca para repositorios GitHub. Funciona em projetos novos e em repositorios ja existentes.

---

## O que este sistema faz

| Capacidade | Descricao |
|---|---|
| **Quality gates** | Lint, sintaxe, tipos, testes e docs validados em todo PR |
| **Auto-approval** | Bot aprova PRs elegiveis sem relaxar a integridade do repo |
| **Docs vivas** | Portal Docusaurus publicado automaticamente a cada merge em main |
| **Versionamento** | Congelamento documental automatico em releases |

### Principio central

> Automacao acelera. Governanca continua no comando.

O bot **nunca** aprova:
- PRs com labels bloqueantes (`security`, `breaking-change`, `db-migration`, `infra-change`, `needs-human-review`)
- PRs que tocam caminhos protegidos (`.github/`, `infra/`, `terraform/`, `migrations/`, etc.)
- PRs draft ou vindos de forks
- PRs com mais de 30 arquivos ou 800 linhas de delta
- PRs com review `CHANGES_REQUESTED` pendente

---

## Inicio rapido — Projeto novo (greenfield)

```bash
# 1. Clone e configure
git clone <este-repo> meu-projeto
cd meu-projeto

# 2. Instale dependencias Python
poetry install

# 3. Instale dependencias do portal
pnpm --dir docs-site install

# 4. Configure o GitHub (veja secao abaixo)
# 5. Substitua os placeholders em CODEOWNERS e docusaurus.config.ts
```

---

## Inserindo em projeto existente (brownfield)

```bash
# 1. Copie este repositorio para um diretorio temporario
git clone <este-repo> /tmp/reviewops

# 2. Execute o script de setup no seu projeto
bash /tmp/reviewops/scripts/setup_reviewops.sh

# 3. Siga as instrucoes do script
```

O script detecta automaticamente:
- Se ja existe `.github/workflows/` (merge seguro)
- Se ja existe `pyproject.toml` (preserva o seu)
- Se ja existe `docs-site/` (nao sobrescreve)

---

## Configuracao do GitHub

### 1. Branch protection em `main`

Ative em Settings > Branches > Branch protection rules:
- [x] Require status checks to pass before merging
  - `quality-gates`
  - `docs-gates`
- [x] Require conversation resolution before merging
- [x] Block force pushes

### 2. Permissao para o bot aprovar PRs

Settings > Actions > General:
- [x] Allow GitHub Actions to create and approve pull requests

### 3. Labels operacionais

```bash
gh label import .github/labels.yml
```

### 4. Substitua os placeholders

| Arquivo | Placeholder | Substituir por |
|---|---|---|
| `.github/CODEOWNERS` | `@org/backend-platform` | Handles reais |
| `docs-site/docusaurus.config.ts` | `example.github.io` | Seu dominio |
| `docs-site/docusaurus.config.ts` | `Example Corp` | Nome da empresa |
| `docs-site/docusaurus.config.ts` | `github.com/example/repo` | URL do seu repo |
| `scripts/export_openapi.py` | `app.main` | Modulo da sua app FastAPI |

---

## Arquitetura do fluxo de PR

```
PR aberto
  └─> pr-ci.yml (quality-gates + docs-gates)  [nao privilegiado, contents: read]
       └─> required status checks = green
  └─> pr-approval.yml (workflow_run)           [privilegiado, pull-requests: write]
       └─> approval_policy.py aplica politica
       └─> APPROVE somente se elegivel
  └─> merge em main
       └─> docs-deploy.yml                     [build + GitHub Pages]
  └─> push tag v*.*.*
       └─> docs-version-pr.yml                 [freeze documental + PR automatico]
```

---

## Metricas esperadas

| Metrica | Meta |
|---|---|
| Tempo medio de feedback do PR CI | < 10 min |
| Taxa de PR elegivel ao auto-approval | 20% a 50% |
| Tempo de publicacao da documentacao apos merge | < 5 min |
| Versoes de docs ativas em producao | 2 a 3 |

---

## Stack

- Python 3.12 + Poetry + pytest + ruff + mypy
- GitHub Actions (4 workflows)
- Docusaurus v3 + TypeScript + pnpm
- Plugin: `docusaurus-plugin-openapi-docs` (PaloAltoNetworks)
- Deploy: GitHub Pages

---

## Licenca

MIT
