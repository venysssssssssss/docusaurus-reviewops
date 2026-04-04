---
id: 001-docusaurus-reviewops
title: "ADR-001: Adocao do docusaurus-reviewops"
sidebar_label: "ADR-001: docusaurus-reviewops"
sidebar_position: 1
description: "Decisao de adotar o sistema docusaurus-reviewops para automacao de PR e documentacao viva."
keywords: [adr, decisao, automacao, pr-review, docusaurus]
---

# ADR-001: Adocao do docusaurus-reviewops

:::tip Status

**Aceita** — 2026-04-02 — Equipe de plataforma

:::

---

## Contexto

O repositorio nao possuia um sistema formal de revisao de PRs nem documentacao viva. PRs de baixo risco consumiam tempo de revisao manual desnecessario, e a documentacao frequentemente ficava desatualizada em relacao ao codigo.

## Decisao

Adotar o `docusaurus-reviewops` — um sistema de governanca que combina:

1. **Auto-approval bot** — aprova PRs de baixo risco automaticamente apos quality gates passarem
2. **Portal Docusaurus v3** — documentacao viva publicada como produto de engenharia
3. **Versionamento de docs** — congelamento automatico em releases major e minor

## Alternativas consideradas

| Alternativa | Motivo de rejeicao |
|---|---|
| Dependabot auto-merge | Escopo limitado a dependencias |
| Wiki do GitHub | Sem CI, sem versionamento, sem integracao com OpenAPI |
| Confluence | Caro, desacoplado do codigo, nao docs-as-code |
| reviewdog | Apenas comentarios, sem aprovacao formal |

## Consequencias

### Positivas

- PRs de baixo risco fluem sem fricao
- PRs sensiveis desaceleram com intencao (labels bloqueantes)
- Documentacao nasce junto com o codigo (guardrail de freshness)
- Portal versionado com referencia de API automatica

### Negativas / Riscos

- Curva de aprendizado inicial para configuracao de CODEOWNERS e labels
- Necessidade de manter o `approval_policy.py` atualizado com a politica do time

## Principio de seguranca

:::danger fail_closed

O bot segue o principio **fail_closed**: na duvida, nao aprova. Qualquer condicao nao prevista resulta em encerramento silencioso sem aprovacao, preservando a necessidade de revisao humana.

:::

## Referencias

- Blueprint de Excelencia — Agente de revisao e aprovacao automatica + Docusaurus (01/04/2026)
- [GitHub Docs — Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Docusaurus — Versioning](https://docusaurus.io/docs/versioning)

## Veja tambem

- [Architecture Overview](/architecture/overview)
- [Deploy Runbook](/runbooks/deploy)
