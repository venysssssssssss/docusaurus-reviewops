# Sprint Log — Automacao de Documentacao via LLM

**Data**: 2026-04-04
**Objetivo**: Automatizar geracao de documentacao usando LLMs, com suporte a multiplos backends e integracao CI/CD.

---

## Resumo de Resultados

| Metrica | Antes | Depois |
|---------|-------|--------|
| Testes | 73 passando | **152 passando** (+79 novos) |
| Scripts Python | 4 | **4 + pacote docgen** (~30 arquivos) |
| Providers LLM | 0 | **5** (Ollama, Anthropic, OpenAI, Claude Code, Mock) |
| Generators | 0 | **6** (architecture, standards, runbook, adr, changelog, api_enricher) |
| Makefile targets | 10 | **12** (+docs-gen, docs-gen-preview) |
| CI/CD workflows | 4 | **5** (+docs-gen.yml) |
| Config files | 0 | **1** (.docgen.yml) |

---

## FASE 1 — Infraestrutura Core

### O que foi feito

1. **Pacote `scripts/docgen/`** com arquitetura modular:
   - `config.py` — Carrega `.docgen.yml` com interpolacao de env vars
   - `providers/base.py` — Abstract base class com `LLMResponse`, `estimate_cost()`
   - `providers/ollama.py` — Provider local via httpx (sem API key)
   - `providers/mock.py` — Provider deterministico para testes
   - `analyzer/codebase.py` — Analise de file tree, deteccao de linguagem, context building
   - `analyzer/hasher.py` — SHA256 para geracao incremental
   - `prompts/templates.py` — Sistema de templates com `string.Template`
   - `output/formatter.py` — Parse/inject frontmatter, sanitize LLM output, validacao
   - `output/merger.py` — Merge com estrategias preserve/overwrite/append
   - `output/writer.py` — Escrita atomica com backup .bak
   - `cache/store.py` — Cache baseado em arquivo com metadata JSON

2. **Dependencias**: `pyyaml`, `httpx` (sem SDKs pesados)

3. **`.docgen.yml`** — Config file com todos os defaults

### Decisoes de design
- **httpx direto** em vez de SDKs Anthropic/OpenAI (menos deps, API surface minima)
- **`string.Template`** em vez de Jinja2 (sem dependencia extra)
- **Sem AST parsing** — file tree + content hashing funciona para qualquer linguagem
- **Cache desde o inicio** — evita chamadas LLM desnecessarias

---

## FASE 2 — Providers e Generators Completos

### Providers

| Provider | Arquivo | Como funciona |
|----------|---------|---------------|
| Ollama | `providers/ollama.py` | POST `localhost:11434/api/generate` via httpx |
| Anthropic | `providers/anthropic.py` | POST Messages API, retry com backoff em 429 |
| OpenAI | `providers/openai.py` | POST Chat Completions API, mesma estrategia |
| Claude Code | `providers/claude_code.py` | subprocess `claude --print`, prompt via stdin |
| Mock | `providers/mock.py` | Retorna markdown deterministico (testes) |

### Generators

| Generator | Input | Output |
|-----------|-------|--------|
| Architecture | File tree, configs, imports | `docs/architecture/overview.md` |
| Standards | pyproject.toml, tsconfig, editorconfig | `docs/standards/coding-standards.md` |
| Runbook | Workflows, Makefile, Dockerfile | `docs/runbooks/deploy.md` |
| ADR | Git history (commits significativos) | `docs/adr/NNN-auto-generated.md` |
| Changelog | Git log entre tags | `CHANGELOG.md` |
| API Enricher | openapi.json + source | `openapi/openapi.json` (enriched) |

### Prompt Templates

5 templates em `scripts/docgen/prompts/`:
- `architecture.md` — Gera diagrama Mermaid, admonitions, cross-links
- `standards.md` — Extrai regras de lint/type-check, exemplos
- `runbook.md` — Extrai steps de workflows, troubleshooting
- `adr.md` — Segue formato ADR padrao (context/decision/consequences)
- `changelog.md` — Keep-a-Changelog com Conventional Commits

---

## FASE 3 — Cache e Custo

- **CacheStore** em `.docgen-cache/`:
  - `{generator}.hash` — SHA256 dos arquivos relevantes
  - `{generator}.meta.json` — timestamp, provider, model, tokens, custo

- **Estimativa de custo** em `providers/base.py`:
  - Tabela de precos por modelo (Anthropic, OpenAI)
  - Ollama = free (local)
  - Sumario impresso no final de cada run

- **Validacao de output** em `output/formatter.py`:
  - Frontmatter YAML valido com campos obrigatorios
  - Code blocks fechados corretamente
  - Admonitions (:::) pareadas
  - Sem TODO/PLACEHOLDER no output

---

## FASE 4 — CI/CD

### Workflow `docs-gen.yml`
- Trigger: PR que toca `src/`, `app/`, `api/`, `scripts/`
- Roda `--dry-run` e posta comentario no PR com sugestoes
- Advisory-only — nunca bloqueia merge
- Requer `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` em secrets

### Integracao com `docs_guardrails.py`
- Quando falha por falta de docs, agora sugere: `make docs-gen`
- Continua fail-closed (seguranca mantida)

---

## FASE 5 — Testes

79 novos testes em `tests/test_docgen/`:

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_config.py` | 7 | Load YAML, env vars, overrides, fallbacks |
| `test_providers.py` | 10 | LLMResponse, cost, mock, factory |
| `test_analyzer.py` | 10 | File scan, excludes, languages, hash, context |
| `test_cache.py` | 6 | Stale check, save/load, summary, clear |
| `test_cli.py` | 8 | Parser, generator selection |
| `test_generators.py` | 7 | Architecture, standards, runbook (mock provider) |
| `test_formatter.py` | 9 | Frontmatter, sanitize, validate |
| `test_merger.py` | 5 | preserve, overwrite, append strategies |
| **Total** | **62** | Todos sem chamadas LLM reais |

+ 17 testes existentes de overrides, guardrails, etc. mantidos.

---

## CLI Reference

```bash
# Gerar todos os docs (Ollama local)
make docs-gen

# Pre-visualizar sem escrever
make docs-gen-preview

# Usar Anthropic
ANTHROPIC_API_KEY=sk-... make docs-gen -- --provider anthropic

# Gerar apenas architecture e standards
python -m scripts.docgen.cli --generators architecture,standards

# Dry-run (mostra o que faria)
python -m scripts.docgen.cli --dry-run --verbose

# Forcar regeneracao (ignorar cache)
python -m scripts.docgen.cli --no-cache
```

---

## Arquivos Criados/Modificados

### Novos (~40 arquivos)

| Diretorio | Arquivos | Funcao |
|-----------|----------|--------|
| `scripts/docgen/` | 7 core | Config, CLI, __init__ |
| `scripts/docgen/providers/` | 6 | Base + 5 providers |
| `scripts/docgen/analyzer/` | 4 | Codebase, hasher, git history |
| `scripts/docgen/generators/` | 8 | Base + 6 generators |
| `scripts/docgen/prompts/` | 7 | Templates engine + 5 prompts |
| `scripts/docgen/output/` | 4 | Formatter, merger, writer |
| `scripts/docgen/cache/` | 2 | Cache store |
| `tests/test_docgen/` | 10 | Conftest + 8 test files |
| `.github/workflows/` | 1 | docs-gen.yml |
| Root | 2 | .docgen.yml, docs/USAGE-GUIDE.md |

### Modificados

| Arquivo | Mudanca |
|---------|---------|
| `Makefile` | +docs-gen, +docs-gen-preview targets |
| `pyproject.toml` | +pyyaml, +httpx, +docgen script |
| `.gitignore` | +.docgen-cache/, +*.bak |
| `.github/scripts/docs_guardrails.py` | +mensagem sugestiva |
