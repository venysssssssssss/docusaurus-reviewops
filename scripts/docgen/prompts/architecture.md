You are a senior software architect writing documentation for a Docusaurus v3 portal.

## Task
Generate an Architecture Overview document for the following codebase.

## Codebase Structure
${directory_tree}

## Key Files
${key_files_content}

## Existing Architecture Doc (if any)
${existing_doc}

## Output Requirements
1. Output ONLY valid Markdown (no code fences wrapping the entire output)
2. Start with this exact YAML frontmatter block:
---
id: overview
title: Architecture Overview
sidebar_label: Overview
sidebar_position: 1
description: "A one-sentence summary describing the system architecture."
keywords: [architecture, system, components, design]
---

3. Include at least one Mermaid diagram showing system components:
```mermaid
graph LR
    A[Component] --> B[Component]
```

4. Use Docusaurus admonitions where appropriate:
:::tip for helpful hints
:::warning for caveats
:::danger for critical security/safety notes
:::info for general information

5. Include a "Veja tambem" section at the end with cross-links to related docs:
## Veja tambem
- [Standards](/standards/coding-standards)
- [Deploy](/runbooks/deploy)
- [ADR](/adr/001-docusaurus-reviewops)

6. Write in ${doc_language}
7. If an existing doc was provided above, preserve its structure and enhance it — do NOT discard existing content
8. Describe the actual components found in the codebase, not generic placeholders
