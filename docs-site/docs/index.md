---
id: index
title: Engineering Docs
sidebar_label: Home
slug: /
---

# Engineering Docs

Portal de documentacao tecnica. Fonte de verdade para arquitetura, padroes, runbooks e API.

## Navegacao

| Secao | O que voce encontra |
|---|---|
| [Architecture](/architecture/overview) | Visao geral do sistema e decisoes de design |
| [Standards](/standards/coding-standards) | Convencoes de codigo, PRs e commits |
| [Runbooks](/runbooks/deploy) | Procedimentos operacionais passo-a-passo |
| [ADR](/adr/001-docusaurus-reviewops) | Historico de decisoes arquiteturais |
| [API Reference](/api/core/api) | Referencia gerada automaticamente do OpenAPI |

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

1. Abra um PR com codigo **e** docs no mesmo PR
2. O guardrail `docs_guardrails.py` verifica que docs foram tocadas
3. Apos merge, o portal atualiza em < 5 minutos

Documentos seguem o padrao [docs-as-code](https://www.writethedocs.org/guide/docs-as-code/).
Edite diretamente os arquivos `.md` em `docs-site/docs/`.
