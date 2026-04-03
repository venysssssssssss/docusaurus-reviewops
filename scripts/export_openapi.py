"""
Exporta o schema OpenAPI da aplicacao FastAPI para docs-site/openapi/openapi.json.

Este script e executado pelo PR CI (docs-gates) e pelo workflow de deploy.
Ajuste o import abaixo para apontar para o modulo correto da sua aplicacao.

Uso:
  poetry run python scripts/export_openapi.py

Customizacao:
  Substitua `from app.main import app` pelo caminho real da sua aplicacao FastAPI.
  Se a sua app usa lifespan ou dependencias complexas, use o helper
  `get_openapi()` do FastAPI para exportar sem inicializar a app completa.
"""

from __future__ import annotations

import json
from pathlib import Path

OUTPUT_PATH = Path("docs-site/openapi/openapi.json")


def _get_schema() -> dict:
    """
    Importa a app FastAPI e retorna o schema OpenAPI.

    TODO: Substitua pelo import correto da sua aplicacao:
      from app.main import app
      return app.openapi()

    Se ainda nao houver app FastAPI neste repositorio, este script
    retorna um schema minimo de placeholder para que o portal possa ser
    construido sem erro.
    """
    try:
        # Tentativa de import da app real
        from app.main import app  # type: ignore[import-not-found]

        return app.openapi()
    except ImportError:
        # Placeholder para repositorios sem app FastAPI configurada
        return {
            "openapi": "3.1.0",
            "info": {
                "title": "API",
                "description": (
                    "Schema placeholder. Substitua scripts/export_openapi.py "
                    "pelo import real da sua aplicacao FastAPI."
                ),
                "version": "0.0.0",
            },
            "paths": {},
        }


def main() -> None:
    schema = _get_schema()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OpenAPI exported to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
