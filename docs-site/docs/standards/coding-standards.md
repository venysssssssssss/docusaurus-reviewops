---
id: coding-standards
title: Coding Standards
sidebar_label: Coding Standards
sidebar_position: 1
description: "Convencoes de codigo, linting, testes e padroes de PR do docusaurus-reviewops — baseados na configuracao real do pyproject.toml."
keywords: [padroes, codigo, lint, ruff, mypy, python, testes, cobertura, conventional-commits, pre-commit]
---

# Coding Standards

Este documento descreve as convencoes de qualidade adotadas neste projeto. Todos os valores sao extraidos diretamente da configuracao em `pyproject.toml` e `.pre-commit-config.yaml`.

:::tip Automatizado

A maior parte dessas convencoes e verificada automaticamente pelo CI (`pr-ci.yml`) e pelos hooks de pre-commit. Voce nao precisa memorizar regras — as ferramentas avisam quando algo esta errado.

:::

## Stack de qualidade

| Ferramenta | Versao | Funcao |
|-----------|--------|--------|
| Python | 3.12+ | Linguagem principal |
| [Ruff](https://docs.astral.sh/ruff/) | `^0.9` | Lint + format (substitui flake8, isort, pyupgrade, black) |
| [mypy](https://mypy.readthedocs.io/) | `^1.15` | Type checking estatico |
| [pytest](https://docs.pytest.org/) | `^8.3` | Testes unitarios |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | `^6.0` | Cobertura de testes |
| [pre-commit](https://pre-commit.com/) | — | Git hooks automatizados |

## Configuracao do Ruff

```toml title="pyproject.toml"
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
ignore = ["E501"]
```

**Regras ativas:**
- `E`, `F`, `W` — erros, avisos e alertas de pycodestyle/pyflakes
- `I` — ordenacao de imports (isort)
- `UP` — pyupgrade (modernizacao de sintaxe Python)
- `B` — bugbear (anti-patterns comuns)
- `SIM` — simplificacao de codigo desnecessariamente complexo

## Configuracao do mypy

```toml title="pyproject.toml"
[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true
disallow_untyped_defs = true
```

:::warning Type hints obrigatorios

`disallow_untyped_defs = true` significa que **toda funcao deve ter anotacoes de tipo** — tanto nos parametros quanto no retorno. O CI falha se qualquer funcao nova nao tiver type hints.

:::

## Convencoes de nomenclatura

- Variaveis e funcoes: `snake_case`
- Classes: `PascalCase`
- Constantes de modulo: `UPPER_SNAKE_CASE`
- Modulos e pacotes: `snake_case`
- Dataclasses `frozen=True` para objetos imutaveis de dominio

## Estrutura de imports

```python
# 1. stdlib
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# 2. third-party
import httpx
import yaml

# 3. local
from scripts.docgen.providers.base import LLMProvider

# 4. TYPE_CHECKING — imports somente para tipagem (evita import circular)
if TYPE_CHECKING:
    from scripts.docgen.providers.base import LLMResponse
```

Ruff (`I` rules) enforce automaticamente essa ordem. Nunca use `from module import *`.

## Convencoes de codigo

### Dataclasses para configuracao e respostas

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int | None
    output_tokens: int | None
    duration_ms: int
```

Prefira `frozen=True` para objetos que nao devem ser mutados apos criacao.

### Tipagem de retorno explicita

```python
# Correto — retorno explicito
def load_config(path: Path | None = None) -> DocgenConfig: ...

# Errado — mypy nao aceita
def load_config(path=None): ...
```

### Fail-closed em scripts de seguranca

```python
from typing import NoReturn

def fail_closed(reason: str) -> NoReturn:
    """Encerra sem registrar aprovacao. NoReturn permite narrowing de tipo pelo mypy."""
    print(f"[policy] nao elegivel: {reason}")
    sys.exit(0)
```

Use `NoReturn` para funcoes que terminam o processo — isso permite ao mypy fazer type narrowing
correto apos a chamada.

## Testes

### Configuracao

```toml title="pyproject.toml"
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"

[tool.coverage.run]
source = ["scripts", ".github/scripts"]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = 80
```

### Gate de cobertura

O CI falha se a cobertura cair abaixo de **80%**. Rode localmente:

```bash
make coverage
```

### Convencoes de testes

```python
# Fixture padrao — modulo importado dinamicamente (evita execucao no import)
@pytest.fixture()
def validator() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("validate_config", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.CHECKS.clear()   # limpa estado global entre testes
    return mod

# Nomeie testes com o que eles verificam, nao como
def test_missing_file_detected_in_empty_dir() -> None: ...    # bom
def test_check_file_structure_2() -> None: ...                 # ruim

# Use pytest.raises para testar sys.exit
with pytest.raises(SystemExit) as exc:
    module.main()
assert exc.value.code == 1
```

## Pull Requests

### Tamanho

- **Maximo:** 30 arquivos alterados, 800 linhas de delta
- **Ideal:** um assunto coeso por PR
- PRs maiores devem ter label `needs-human-review` e serao revisados manualmente

### Titulo (Conventional Commits)

```
tipo(escopo): descricao imperativa em minusculo

feat(docgen): adiciona provider Anthropic com retry exponencial
fix(guardrails): corrige deteccao de PRs grandes sem docs especificos
docs(runbook): atualiza URL do portal para producao
chore(deps): bump ruff 0.9.0 -> 0.9.10
test(approval): adiciona caso de PR de fork rejeitado
refactor(cli): extrai calculo de custo para funcao separada
```

Tipos validos: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `perf`, `security`

### Checklist antes de abrir PR

```bash
make lint       # ruff check . — deve passar sem erros
make typecheck  # mypy — deve reportar 0 errors
make test       # pytest — todos os testes devem passar
make coverage   # cobertura >= 80%
```

## Seguranca

:::danger Regras inegociaveis

- **Jamais** commite secrets, tokens ou API keys — use variaveis de ambiente
- **Jamais** pule os hooks do pre-commit (`git commit --no-verify`)
- Se tocar `.github/`, aplique a label `needs-human-review` no PR
- Inputs externos (API REST, arquivos de usuario) devem ser validados antes de usar
- Logs nunca devem conter dados sensiveis (tokens, PII)

:::

Veja [SECURITY.md](https://github.com/venysssssssssss/docusaurus-reviewops/blob/master/SECURITY.md)
para o procedimento de reporte de vulnerabilidades.

## Hooks de pre-commit

Instale os hooks apos o setup:

```bash
poetry run pre-commit install
```

Os hooks rodam automaticamente em `git commit`:
- `ruff` — lint + format
- `trailing-whitespace`, `end-of-file-fixer` — normalizacao de whitespace
- `check-yaml`, `check-toml`, `check-json` — validacao de arquivos de config
- `detect-private-key` — detecta chaves privadas acidentalmente adicionadas
- `no-commit-to-branch` — protege o branch `master` de commits diretos
- `mypy` — type checking

## Veja tambem

- [Architecture Overview](/architecture/overview)
- [Deploy Runbook](/runbooks/deploy)
- [ADR-001: docusaurus-reviewops](/adr/001-docusaurus-reviewops)
