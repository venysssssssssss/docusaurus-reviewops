# Estendendo o Docgen — Como criar um Generator customizado

Guia para desenvolvedores que querem adicionar um novo tipo de documento ao sistema `docgen`.

---

## Visão geral

O sistema docgen é composto por:

```
scripts/docgen/
  generators/     ← cada arquivo é um generator concreto
    base.py       ← classe abstrata DocGenerator
    architecture.py
    standards.py
    ...
  prompts/        ← templates de prompt (.md com ${variáveis})
    architecture.md
    ...
  providers/      ← adapters para LLMs
    base.py       ← LLMProvider + LLMResponse
    ollama.py
    anthropic.py
    ...
```

Para adicionar um novo generator, você precisa:
1. Criar um arquivo em `scripts/docgen/generators/`
2. Criar um template em `scripts/docgen/prompts/`
3. Registrar no dicionário `_GENERATORS` de `cli.py`
4. Adicionar a chave em `.docgen.yml`
5. Escrever testes

---

## Passo 1 — Criar o generator

```python title="scripts/docgen/generators/my_generator.py"
"""Generator para documentação XYZ."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.docgen.generators.base import DocGenerator
from scripts.docgen.output.formatter import sanitize_llm_output
from scripts.docgen.prompts.templates import render_template

if TYPE_CHECKING:
    from scripts.docgen.analyzer.codebase import CodebaseSnapshot
    from scripts.docgen.providers.base import LLMResponse

_SYSTEM_PROMPT = (
    "You are a technical writer. Generate clear documentation in "
    "valid Docusaurus-compatible Markdown."
)


class MyGenerator(DocGenerator):
    """Documenta XYZ a partir do código-fonte."""

    @property
    def name(self) -> str:
        return "my_generator"

    @property
    def output_filename(self) -> str:
        # Caminho relativo a config.output_dir
        return "xyz/my-doc.md"

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        """Retorna arquivos que este generator analisa (afeta cache)."""
        return [
            f.path for f in snapshot.files
            if f.language == "python" and "xyz" in str(f.path)
        ]

    def generate(self, snapshot: CodebaseSnapshot) -> tuple[str, LLMResponse | None]:
        # Colete informações do codebase
        relevant = self.relevant_paths(snapshot)
        files_summary = "\n".join(str(p.relative_to(snapshot.root)) for p in relevant)

        prompt = render_template(
            "my_generator",        # → scripts/docgen/prompts/my_generator.md
            files_list=files_summary,
            doc_language="Portuguese (pt-BR)",
        )

        response = self.provider.generate(prompt, system_prompt=_SYSTEM_PROMPT)
        return sanitize_llm_output(response.content), response
```

### Interface `DocGenerator`

```python title="scripts/docgen/generators/base.py (interface)"
class DocGenerator(ABC):
    def __init__(self, provider: LLMProvider, config: DocgenConfig) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def output_filename(self) -> str: ...

    def output_path(self) -> Path:
        """Caminho absoluto do arquivo de saída."""
        return self.config.output_dir / self.output_filename

    def relevant_paths(self, snapshot: CodebaseSnapshot) -> list[Path]:
        """Arquivos que este generator analisa. Afeta o cache."""
        return []

    def existing_content(self) -> str | None:
        """Conteúdo atual do arquivo de saída (para merge)."""
        path = self.output_path()
        return path.read_text(encoding="utf-8") if path.exists() else None

    @abstractmethod
    def generate(self, snapshot: CodebaseSnapshot) -> tuple[str, LLMResponse | None]:
        """Gera o documento. Retorna (conteúdo_markdown, resposta_llm|None)."""
```

**Por que `tuple[str, LLMResponse | None]`?** O segundo elemento propaga os metadados de tokens/custo até o sumário do CLI. Retorne `None` quando não houver chamada LLM (ex: conteúdo vazio, cache hit dentro do generator).

---

## Passo 2 — Criar o template de prompt

```markdown title="scripts/docgen/prompts/my_generator.md"
You are a technical writer specializing in software documentation.

## Task
Generate a document describing the XYZ subsystem.

## Files analyzed
${files_list}

## Output Requirements
1. Output ONLY valid Markdown
2. Start with Docusaurus frontmatter (id, title, sidebar_label, sidebar_position, description, keywords)
3. Include at least one mermaid diagram if applicable
4. Use Docusaurus admonitions (:::tip, :::warning, :::danger, :::info)
5. End with a "Veja também" section with cross-links
6. Write in ${doc_language}
```

**Variáveis** são substituídas via `string.Template.safe_substitute`. Use `${nome}` para variáveis obrigatórias e `${nome:-default}` não é suportado — sempre passe todas as variáveis no `render_template(...)`.

---

## Passo 3 — Registrar no CLI

```python title="scripts/docgen/cli.py — adicionar ao dicionário _GENERATORS"
from scripts.docgen.generators.my_generator import MyGenerator

_GENERATORS: dict[str, type[DocGenerator]] = {
    "architecture": ArchitectureGenerator,
    "standards": StandardsGenerator,
    # ...
    "my_generator": MyGenerator,   # ← adicionar aqui
}
```

---

## Passo 4 — Adicionar ao .docgen.yml

```yaml title=".docgen.yml"
generators:
  architecture: true
  standards: true
  # ...
  my_generator: true    # ← habilitar
```

---

## Passo 5 — Escrever testes

Use o `MockProvider` para evitar chamadas LLM reais nos testes:

```python title="tests/test_docgen/test_my_generator.py"
from __future__ import annotations

from pathlib import Path
from scripts.docgen.analyzer.codebase import analyze_codebase
from scripts.docgen.generators.my_generator import MyGenerator
from scripts.docgen.providers.mock import MockProvider


class TestMyGenerator:
    def test_name(self, mock_provider, sample_config):
        gen = MyGenerator(mock_provider, sample_config)
        assert gen.name == "my_generator"

    def test_output_filename(self, mock_provider, sample_config):
        gen = MyGenerator(mock_provider, sample_config)
        assert gen.output_filename == "xyz/my-doc.md"

    def test_generate_returns_content(self, mock_provider, sample_config, sample_codebase):
        snapshot = analyze_codebase(sample_codebase, [], [])
        gen = MyGenerator(mock_provider, sample_config)
        content, response = gen.generate(snapshot)
        assert len(content) > 0
        assert response is not None

    def test_generate_returns_empty_when_no_relevant_files(
        self, mock_provider, sample_config, tmp_path
    ):
        """Se não há arquivos XYZ, retorne ("", None) em vez de chamar o LLM."""
        snapshot = analyze_codebase(tmp_path, [], [])
        gen = MyGenerator(mock_provider, sample_config)
        # Implemente esse comportamento no generator se fizer sentido
        content, _ = gen.generate(snapshot)
        assert isinstance(content, str)
```

### Fixtures disponíveis em `conftest.py`

| Fixture | Tipo | Descrição |
|---------|------|-----------|
| `mock_provider` | `MockProvider` | Retorna markdown determinístico sem chamar LLM |
| `sample_config` | `DocgenConfig` | Config apontando para `tmp_path` |
| `sample_codebase` | `Path` | Codebase fake mínimo em `tmp_path` |

---

## Dicas e armadilhas

:::tip Retorne cedo quando não há conteúdo
Se o codebase não tem arquivos relevantes, retorne `("", None)` antes de chamar o LLM. Isso mantém o sumário limpo e evita custo desnecessário.
:::

:::warning Não mute o snapshot
O `CodebaseSnapshot` é imutável (`frozen=True`). Não tente adicionar ou remover arquivos — crie estruturas locais.
:::

:::danger Não itere e mute dicts simultaneamente
Se você acumula mudanças em um `dict` durante `generate()`, use o padrão **dois passes**: primeiro colete as mudanças em uma lista, depois aplique. Veja `api_enricher.py` como exemplo.
:::

:::info Estratégia de merge
O CLI aplica `merge_docs(existing, generated, strategy)` antes de escrever. Seu generator não precisa lidar com merge — apenas retorne o conteúdo completo do documento.
:::

---

## Veja também

- [CONTRIBUTING.md](CONTRIBUTING.md) — setup de desenvolvimento
- [ARCHITECTURE.md](ARCHITECTURE.md) — visão geral do sistema
- [USAGE-GUIDE.md](USAGE-GUIDE.md) — como usar o docgen
