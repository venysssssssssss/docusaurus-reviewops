"""Prompt template loading and rendering using string.Template."""

from __future__ import annotations

from pathlib import Path
from string import Template

_TEMPLATES_DIR = Path(__file__).parent


def load_template(template_name: str) -> str:
    """Load a .md template from the prompts/ directory."""
    path = _TEMPLATES_DIR / f"{template_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template_name: str, **variables: str) -> str:
    """Load and render a template with variable substitution.

    Uses safe_substitute so missing variables don't raise errors.
    """
    raw = load_template(template_name)
    tmpl = Template(raw)
    return tmpl.safe_substitute(**variables)
