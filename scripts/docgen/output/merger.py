"""Merge generated documentation with existing content."""

from __future__ import annotations

from scripts.docgen.output.formatter import parse_frontmatter


def _extract_sections(body: str) -> dict[str, str]:
    """Extract top-level sections (## Heading) from markdown body."""
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in body.splitlines():
        if line.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def merge_docs(existing: str, generated: str, strategy: str) -> str:
    """Merge existing doc with generated content.

    Strategies:
    - 'preserve': keep existing, append sections from generated that are new
    - 'overwrite': replace entirely with generated
    - 'append': append generated content after existing
    """
    if strategy == "overwrite":
        return generated

    if strategy == "append":
        return f"{existing.rstrip()}\n\n---\n\n{generated.lstrip()}"

    # strategy == "preserve" (default)
    if not existing.strip():
        return generated

    existing_meta, existing_body = parse_frontmatter(existing)
    generated_meta, generated_body = parse_frontmatter(generated)

    # Keep existing frontmatter, enriched with missing fields from generated
    merged_meta = dict(generated_meta)
    merged_meta.update(existing_meta)  # existing wins

    existing_sections = _extract_sections(existing_body)
    generated_sections = _extract_sections(generated_body)

    # Find sections in generated that don't exist in existing
    existing_headings_lower = {h.lower() for h in existing_sections}
    new_sections: list[str] = []
    for heading, content in generated_sections.items():
        if heading.lower() not in existing_headings_lower:
            new_sections.append(f"{heading}\n\n{content}")

    if not new_sections:
        return existing  # nothing new to add

    # Build result: existing content + new sections
    import yaml

    fm_yaml = yaml.dump(merged_meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    result = f"---\n{fm_yaml}---\n\n{existing_body.strip()}"

    for section in new_sections:
        result += f"\n\n{section}"

    return result.rstrip() + "\n"
