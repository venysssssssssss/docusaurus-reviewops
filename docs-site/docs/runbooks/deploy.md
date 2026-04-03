---
id: deploy
title: Deploy Runbook
sidebar_label: Deploy
---

# Deploy Runbook

<!-- TODO: Substitua pelos procedimentos reais do seu sistema -->

## Pre-requisitos

- [ ] Acesso ao ambiente de producao
- [ ] Branch `main` com todos os testes passando
- [ ] Aprovacao do time relevante (se aplicavel)

## Deploy normal (via CI)

O deploy em producao e automatizado via GitHub Actions. Todo merge em `main` dispara o pipeline:

```
merge em main
  └─> pr-ci.yml passou (quality-gates + docs-gates)
  └─> docs-deploy.yml publica portal Docusaurus
  └─> seu pipeline de deploy da aplicacao (configure aqui)
```

### Verificacao pos-deploy

1. Verifique o status do workflow em Actions
2. Valide a URL de producao
3. Execute smoke tests se disponivel

## Rollback

### Rollback via revert de commit

```bash
git revert <sha-do-commit-problematico>
git push origin main
```

O CI automaticamente fara o deploy da versao revertida.

### Rollback manual de emergencia

<!-- TODO: Documente o procedimento de rollback especifico do seu sistema -->

## Releases e versionamento

Para congelar uma versao documental junto com uma release:

```bash
# Cria a tag — o workflow docs-version-pr.yml dispara automaticamente
git tag v1.2.0
git push origin v1.2.0
```

O workflow abre um PR automatico com o freeze da documentacao. Revise e faca o merge.

## Monitoramento

<!-- TODO: Links para dashboards de monitoramento -->

| Metrica | Ferramenta | Link |
|---|---|---|
| Latencia | <!-- ferramenta --> | <!-- link --> |
| Taxa de erro | <!-- ferramenta --> | <!-- link --> |
| Disponibilidade | <!-- ferramenta --> | <!-- link --> |

## Contatos de emergencia

<!-- TODO: Substitua pelos contatos reais -->

| Papel | Contato |
|---|---|
| On-call engineer | @on-call-channel |
| Tech lead | @tech-lead |
| Platform engineering | @platform-engineering |
