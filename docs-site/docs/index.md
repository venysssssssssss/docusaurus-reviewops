---
id: index
title: Engineering Docs
sidebar_label: Home
sidebar_position: 1
slug: /
description: "Portal de documentacao tecnica — arquitetura, padroes, runbooks e API reference."
keywords: [documentacao, portal, engenharia, docs-as-code]
---

<div className="hero-section">

# Engineering Docs

Portal de documentacao tecnica. Fonte de verdade para arquitetura, padroes, runbooks e API.

</div>

## Navegacao

| Secao | O que voce encontra |
|---|---|
| [Architecture](/architecture/overview) | Visao geral do sistema e decisoes de design |
| [Standards](/standards/coding-standards) | Convencoes de codigo, PRs e commits |
| [Runbooks](/runbooks/deploy) | Procedimentos operacionais passo-a-passo |
| [ADR](/adr/001-docusaurus-reviewops) | Historico de decisoes arquiteturais |
| [API Reference](/api/core/api) | Referencia gerada automaticamente do OpenAPI |

:::tip Busca rapida

Use **Ctrl+K** (ou **Cmd+K** no Mac) para buscar em todo o portal.

:::

## Como este portal funciona

Este portal e **gerado automaticamente** a cada merge em `main`:

1. O CI valida que toda mudanca publica inclui documentacao
2. O schema OpenAPI e exportado e a referencia de API e gerada
3. O Docusaurus builda o site estatico
4. O GitHub Pages publica automaticamente

### Versionamento

Em cada release (tag `v*.*.*`), a documentacao atual e congelada como snapshot.
Versoes anteriores ficam acessiveis pelo dropdown no canto superior direito.

## Como contribuir

:::info Fluxo de contribuicao

1. Abra um PR com codigo **e** docs no mesmo PR
2. O guardrail `docs_guardrails.py` verifica que docs foram tocadas
3. Apos merge, o portal atualiza em < 5 minutos

:::

Documentos seguem o padrao [docs-as-code](https://www.writethedocs.org/guide/docs-as-code/).
Edite diretamente os arquivos `.md` em `docs-site/docs/`.

## Veja tambem

- [ADR-001: Por que adotamos o docusaurus-reviewops](/adr/001-docusaurus-reviewops)
- [Deploy Runbook: Como o portal e publicado](/runbooks/deploy)
- [Coding Standards: Convencoes do time](/standards/coding-standards)
