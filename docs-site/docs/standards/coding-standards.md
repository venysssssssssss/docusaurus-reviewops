---
id: coding-standards
title: Coding Standards
sidebar_label: Coding Standards
sidebar_position: 1
description: "Convencoes de codigo, linting, testes e padroes de PR do time."
keywords: [padroes, codigo, lint, ruff, mypy, python, convencoes]
---

# Coding Standards

:::note Personalize

Adapte estas convencoes ao stack real do seu projeto. Os valores abaixo sao defaults razoaveis para projetos Python.

:::

## Stack assumida

- Python 3.12+ com type hints obrigatorios
- Linter: Ruff (substituindo flake8 + isort + pyupgrade)
- Type checker: mypy (strict = false, disallow_untyped_defs = true)
- Formatter: Ruff format

## Convencoes gerais

### Nomenclatura

- Variaveis e funcoes: `snake_case`
- Classes: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`
- Modulos: `snake_case`

### Estrutura de modulos

```text title="Estrutura de diretorios"
src/
  domain/       # entidades e logica de negocio pura
  application/  # casos de uso e servicos de aplicacao
  adapters/     # integracao com mundo externo (DB, APIs, filas)
  api/          # endpoints HTTP (FastAPI routers)
```

### Imports

- Ordem: stdlib > third-party > local (enforced pelo Ruff)
- Imports absolutos sempre que possivel
- Sem wildcards (`from module import *`)

## Qualidade

### Cobertura de testes

- Minimo: 80% em `src/`
- Testes unitarios em `tests/unit/`
- Testes de integracao em `tests/integration/`

### Pull Requests

- PRs pequenos e coesos (< 30 arquivos, < 800 linhas)
- Um assunto por PR
- Titulo no formato: `tipo(escopo): descricao` (Conventional Commits)

### Commits

```text title="Exemplos de Conventional Commits"
feat(api): adiciona endpoint de export
fix(worker): corrige race condition no processamento
docs(runbook): atualiza procedimento de rollback
```

## Seguranca

:::danger Regras inegociaveis

- Nunca commitar secrets, tokens ou credenciais
- Validar inputs em todos os endpoints publicos
- SQL: sempre usar parameterized queries
- Logs: nunca logar dados sensiveis (PII, tokens)

:::

## Revisao de codigo

:::warning Checklist obrigatorio antes de abrir PR

- [ ] `ruff check .` passa sem erros
- [ ] `mypy src` passa
- [ ] Testes novos cobrem o comportamento adicionado/modificado
- [ ] Documentacao atualizada se comportamento publico mudou

:::

## Veja tambem

- [Architecture Overview](/architecture/overview)
- [Deploy Runbook](/runbooks/deploy)
- [ADR-001: docusaurus-reviewops](/adr/001-docusaurus-reviewops)
