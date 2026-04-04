"""Post-process LLM output for Docusaurus compatibility."""

from __future__ import annotations

import re
from dataclasses import dataclass

import yaml


@dataclass
class DocMetadata:
    """Docusaurus frontmatter fields."""

    id: str
    title: str
    sidebar_label: str
    sidebar_position: int
    description: str
    keywords: list[str]


_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict[str, object], str]:
    """Split YAML frontmatter from markdown body.

    Returns (metadata_dict, body). If no frontmatter found, returns ({}, content).
    """
    match = _FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, content
    body = content[match.end():]
    return metadata, body


def inject_frontmatter(body: str, metadata: DocMetadata) -> str:
    """Prepend YAML frontmatter to markdown body."""
    fm_dict = {
        "id": metadata.id,
        "title": metadata.title,
        "sidebar_label": metadata.sidebar_label,
        "sidebar_position": metadata.sidebar_position,
        "description": metadata.description,
        "keywords": metadata.keywords,
    }
    fm_yaml = yaml.dump(fm_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm_yaml}---\n\n{body.lstrip()}"


def sanitize_llm_output(raw: str) -> str:
    """Strip code fences wrapping entire output and fix common LLM formatting issues."""
    content = raw.strip()

    # Remove wrapping ```markdown ... ``` fences
    if content.startswith("```markdown"):
        content = content[len("```markdown"):].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
    elif content.startswith("```md"):
        content = content[len("```md"):].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
    elif content.startswith("```") and not content.startswith("```mermaid"):
        first_newline = content.index("\n") if "\n" in content else len(content)
        # Only strip if the first line is just ``` or ```<lang>
        first_line = content[:first_newline].strip()
        if len(first_line) <= 15 and content.endswith("```"):
            content = content[first_newline:].strip()
            content = content[:-3].strip()

    return content


def validate_docusaurus_markdown(content: str) -> list[str]:
    """Return list of issues found in the markdown content."""
    issues: list[str] = []

    # Check frontmatter
    metadata, body = parse_frontmatter(content)
    if not metadata:
        issues.append("Missing YAML frontmatter")
    else:
        for field in ("id", "title", "description"):
            if field not in metadata:
                issues.append(f"Missing frontmatter field: {field}")

    # Check unclosed admonitions
    admonition_opens = len(re.findall(r"^:::\w+", body, re.MULTILINE))
    admonition_closes = len(re.findall(r"^:::\s*$", body, re.MULTILINE))
    if admonition_opens != admonition_closes:
        issues.append(
            f"Unclosed admonitions: {admonition_opens} opens vs {admonition_closes} closes"
        )

    # Check unclosed code blocks (includes mermaid)
    code_block_count = len(re.findall(r"```", body))
    if code_block_count % 2 != 0:
        issues.append("Odd number of code fence markers (``` ) — possible unclosed block")

    # Check for TODO/PLACEHOLDER leftovers
    if re.search(r"\bTODO\b", body, re.IGNORECASE):
        issues.append("Contains TODO marker in body")
    if re.search(r"\bPLACEHOLDER\b", body, re.IGNORECASE):
        issues.append("Contains PLACEHOLDER marker in body")

    return issues
