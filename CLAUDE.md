# docusaurus-reviewops

Sistema de governanca de PR + documentacao viva para repositorios GitHub.

## O que e

- **Agente de aprovacao** — aprova PRs de baixo risco apos CI green
- **Portal Docusaurus** — publicado automaticamente, versionado por release

## Comandos

```bash
make setup       # instala deps
make test        # lint + testes
make docs        # build do portal
make validate    # checa placeholders pendentes
make all         # tudo
```

## Arquivos criticos

| Arquivo | Funcao |
|---|---|
| `.github/scripts/approval_policy.py` | Logica de aprovacao (fail_closed) |
| `.github/scripts/docs_guardrails.py` | Freshness de docs |
| `.github/workflows/pr-ci.yml` | Quality gates (nao privilegiado) |
| `.github/workflows/pr-approval.yml` | Aprovacao (privilegiado, sem checkout) |
| `docs-site/docusaurus.config.ts` | Config do portal (tem placeholders TODO) |
| `scripts/export_openapi.py` | Exporta schema FastAPI |
| `scripts/validate_config.py` | Valida prontidao para deploy |

## Regras de seguranca

1. Workflow privilegiado NUNCA faz checkout do PR
2. `fail_closed` — na duvida, nao aprova
3. Labels bloqueantes: security, breaking-change, db-migration, infra-change, needs-human-review
4. Caminhos protegidos: .github/, infra/, terraform/, helm/, migrations/, alembic/
