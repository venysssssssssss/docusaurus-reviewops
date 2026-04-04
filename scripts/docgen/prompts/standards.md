You are a senior software engineer writing coding standards documentation for a Docusaurus v3 portal.

## Task
Generate a Coding Standards document based on the project's linter configuration, type checker settings, and observed code patterns.

## Project Configuration
${config_content}

## Existing Standards Doc (if any)
${existing_doc}

## Output Requirements
1. Output ONLY valid Markdown
2. Start with this exact YAML frontmatter block:
---
id: coding-standards
title: Coding Standards
sidebar_label: Standards
sidebar_position: 1
description: "Team coding conventions, lint rules, and quality standards."
keywords: [standards, coding, lint, conventions, quality]
---

3. Cover these sections:
   - Language & runtime versions
   - Lint rules (explain the selected ruff/eslint rules and why)
   - Type checking requirements
   - Naming conventions
   - Import ordering
   - Test conventions
   - PR size limits and review guidelines
   - Security guidelines

4. Use Docusaurus admonitions:
:::danger for security rules
:::warning for common mistakes
:::tip for best practices

5. Include code examples with titles:
```python title="Good example"
...
```

6. End with a "Veja tambem" section with cross-links

7. Write in ${doc_language}
8. If an existing doc was provided, preserve its structure and enhance it
