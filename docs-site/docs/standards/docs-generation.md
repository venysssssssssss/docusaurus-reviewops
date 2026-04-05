---
id: docs-generation
title: Geração de Documentação via LLM
sidebar_label: Geração LLM
sidebar_position: 2
description: "Como usar o sistema docgen para gerar e atualizar documentação automaticamente com LLMs locais ou na nuvem."
keywords: [docgen, llm, ollama, anthropic, openai, documentação, automação]
---

# Geração de Documentação via LLM

O sistema `docgen` analisa o código-fonte e gera documentação Docusaurus-compatível usando LLMs. Ele suporta múltiplos backends — de modelos locais gratuitos (Ollama) a APIs na nuvem (Anthropic, OpenAI).

:::tip Princípio fundamental
O sistema gera **drafts para revisão humana** — nunca sobrescreve conteúdo existente por padrão (`merge_strategy: preserve`). Você revisa, edita, e só então faz commit.
:::

## Uso rápido

```bash title="Gerar documentação"
make docs-gen                # usa o provider configurado em .docgen.yml
make docs-gen-preview        # gera para stdout, sem escrever arquivos
```

```bash title="Com provider específico"
DOCGEN_PROVIDER=anthropic make docs-gen
DOCGEN_PROVIDER=openai make docs-gen
```

## Providers disponíveis

| Provider | Custo | Requer | Melhor para |
|----------|-------|--------|-------------|
| **Ollama** | Gratuito | Ollama local rodando | Desenvolvimento local, privacidade |
| **Anthropic** | Pago (ver tabela) | `ANTHROPIC_API_KEY` | Qualidade de produção, português fluente |
| **OpenAI** | Pago (ver tabela) | `OPENAI_API_KEY` | Alternativa cloud |
| **Claude Code CLI** | Depende da conta | CLI `claude` instalada | Integração com Claude.ai |
| **Mock** | Gratuito | Nenhum | Testes, CI sem API key |

### Configuração do provider

```yaml title=".docgen.yml"
provider: ollama            # ollama | anthropic | openai | claude-code | mock

anthropic:
  api_key: ${ANTHROPIC_API_KEY}    # interpolação automática de env vars
  model: claude-sonnet-4-20250514

ollama:
  base_url: http://localhost:11434
  model: llama3.2
  timeout: 120
```

## Generators disponíveis

| Generator | Arquivo gerado | Analisa |
|-----------|---------------|---------|
| `architecture` | `architecture/overview.md` | Estrutura do projeto, entry points, configs |
| `standards` | `standards/coding-standards.md` | `pyproject.toml`, `tsconfig.json`, `.editorconfig` |
| `runbook` | `runbooks/deploy.md` | Workflows, Makefile, Dockerfile |
| `adr` | `adr/00N-auto-generated.md` | Git history, commits significativos |
| `changelog` | `CHANGELOG.md` | Git log entre tags, Conventional Commits |
| `api_enricher` | `openapi.json` (enriquece) | OpenAPI schema, endpoints sem descrição |

```yaml title="Ativar/desativar generators em .docgen.yml"
generators:
  architecture: true
  standards: true
  runbook: true
  adr: true
  changelog: true
  api_enricher: true    # auto-skip se não houver schema configurado
```

## Estratégias de merge

| Estratégia | Comportamento | Quando usar |
|------------|--------------|-------------|
| `preserve` | (**padrão**) Mantém conteúdo existente, adiciona apenas seções novas | Protege edições manuais |
| `overwrite` | Substitui completamente o arquivo | Quando o LLM deve ter controle total |
| `append` | Adiciona o conteúdo gerado ao final do arquivo existente | Logs, changelogs incrementais |

## Cache incremental

O docgen evita chamadas LLM desnecessárias usando um cache por SHA256:

```
.docgen-cache/
  architecture.hash        # hash dos arquivos analisados
  architecture.meta.json   # timestamp, provider, modelo, custo
  standards.hash
  ...
```

Se o código-fonte não mudou desde a última execução, o generator é pulado com `[cached, skipping]`.

```bash title="Forçar regeneração ignorando cache"
make docs-gen -- --no-cache
```

## Estimativa de custo

O custo é calculado após cada execução e exibido no sumário. A tabela de preços fica em `scripts/docgen/providers/base.py` (constante `PRICING`).

### Preços por provider (por 1M tokens, aprox. 2026)

| Provider | Modelo | Input | Output | Geração típica* |
|----------|--------|-------|--------|----------------|
| Anthropic | claude-sonnet-4-20250514 | $3.00 | $15.00 | ~$0.03–0.08 |
| Anthropic | claude-haiku-4-5-20251001 | $0.25 | $1.25 | ~$0.003–0.01 |
| Anthropic | claude-opus-4-6 | $15.00 | $75.00 | ~$0.15–0.40 |
| OpenAI | gpt-4o | $2.50 | $10.00 | ~$0.02–0.06 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | ~$0.001–0.005 |
| Ollama | qualquer modelo local | $0 | $0 | Gratuito |
| Claude Code CLI | depende da conta | — | — | Sem rastreamento |

*\*Estimativa para gerar 1 documento de arquitetura (~3k tokens entrada, ~1k saída).*

:::info Como atualizar os preços
Se os preços mudaram, edite a constante `PRICING` em [scripts/docgen/providers/base.py](../../scripts/docgen/providers/base.py).
:::

## Modo dry-run e diff

```bash title="Ver o que seria gerado sem escrever"
python -m scripts.docgen.cli --dry-run

# Resultado: diff unificado para cada arquivo que mudaria
```

```bash title="Usar em CI para detectar docs desatualizados"
python -m scripts.docgen.cli --diff-only
# Retorna exit code 1 se algum arquivo mudaria
```

## Validação do output

Todo conteúdo gerado é validado antes de ser escrito:

- Frontmatter Docusaurus válido (campos obrigatórios: `id`, `title`, `sidebar_label`)
- Blocos Mermaid fechados corretamente
- Admonitions (`:::`) fechadas
- Ausência de `TODO:` ou `PLACEHOLDER` no output
- HTML raw que quebre o Docusaurus é removido

## Veja também

- [Contribuindo](/docs/contributing) — como rodar o sistema localmente
- [Runbook de Deploy](/docs/runbooks/deploy) — deploy do portal
- [Padrões de Código](/docs/standards/coding-standards) — convenções do projeto
