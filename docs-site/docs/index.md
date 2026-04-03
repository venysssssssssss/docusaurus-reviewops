---
id: index
title: Engineering Docs
sidebar_label: Home
slug: /
---

# Engineering Docs

Bem-vindo ao portal de documentacao tecnica. Esta e a fonte de verdade para arquitetura, padroes de engenharia, runbooks operacionais e referencia de API.

## Navegacao rapida

| Secao | Descricao |
|---|---|
| [Architecture](/architecture/overview) | Visao geral da arquitetura do sistema |
| [Standards](/standards/coding-standards) | Padroes de codigo e engenharia |
| [Runbooks](/runbooks/deploy) | Procedimentos operacionais |
| [ADR](/adr) | Registros de decisao arquitetural |
| [API Reference](/api/core) | Referencia completa da API |

## Principios editoriais

- **Docs como codigo**: toda mudanca publica exige atualizacao documental no mesmo PR
- **Fonte de verdade unica**: API reference gerada automaticamente do schema OpenAPI
- **Versionamento explicito**: versoes congeladas em releases major e minor
- **Auditabilidade**: `showLastUpdateTime` e `showLastUpdateAuthor` ativados em todas as paginas

## Como contribuir

1. Abra um PR com a mudanca de codigo **e** a documentacao correspondente
2. O CI valida que docs foram tocadas junto com codigo publico
3. Apos merge, o portal e publicado automaticamente

> Documentacao desatualizada e divida tecnica. Este portal elimina esse debt na origem.
