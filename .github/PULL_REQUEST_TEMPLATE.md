## Tipo de mudanca

<!-- Marque todos que se aplicam -->

- [ ] `feat` — nova funcionalidade
- [ ] `fix` — correcao de bug
- [ ] `docs` — apenas documentacao
- [ ] `refactor` — refatoracao sem mudanca de comportamento
- [ ] `test` — adicao ou correcao de testes
- [ ] `chore` — build, deps, CI, configuracao
- [ ] `perf` — melhoria de performance
- [ ] `security` — correcao de vulnerabilidade

## Descricao

<!-- O que foi mudado e por que? Seja conciso mas completo. -->

## Como testar

<!-- Passos para verificar que a mudanca funciona corretamente. -->

1. 
2. 

## Checklist

<!-- Nao abra o PR sem marcar todos os itens aplicaveis -->

### Qualidade
- [ ] `make lint` passa sem erros (`ruff check .`)
- [ ] `make typecheck` passa sem erros (`mypy`)
- [ ] `make test` passa (todos os testes existentes continuam passando)
- [ ] Novos testes cobrem o comportamento adicionado ou modificado

### Documentacao
- [ ] Documentacao atualizada se comportamento publico mudou
- [ ] CHANGELOG.md atualizado (se for feature ou fix relevante)
- [ ] Comentarios de codigo adicionados onde a logica nao e auto-evidente

### Seguranca
- [ ] Nenhum secret, token ou credencial no codigo
- [ ] Se toca `.github/`, `infra/`, `migrations/` ou lockfiles: label `needs-human-review` aplicada
- [ ] Se introduz mudanca breaking: label `breaking-change` aplicada

### Convencoes
- [ ] Titulo do PR segue Conventional Commits: `tipo(escopo): descricao`
- [ ] PR e pequeno e coeso (< 30 arquivos, < 800 linhas delta)
- [ ] Branch nomeada: `tipo/descricao-curta` (ex: `feat/llm-provider-cache`)

## Referencias

<!-- Issues relacionadas, ADRs, documentacao externa -->

Closes #
