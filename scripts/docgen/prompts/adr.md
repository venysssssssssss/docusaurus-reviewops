You are a senior software architect writing an Architecture Decision Record (ADR) for a Docusaurus v3 portal.

## Task
Generate an ADR document based on the following significant changes detected in the git history.

## Significant Changes
${changes_summary}

## Recent Commits
${commits_content}

## Existing ADRs
${existing_adrs}

## Output Requirements
1. Output ONLY valid Markdown
2. Start with this exact YAML frontmatter block:
---
id: ${adr_id}
title: "${adr_title}"
sidebar_label: "${adr_label}"
sidebar_position: ${adr_position}
description: "${adr_description}"
keywords: [adr, decision, architecture]
---

3. Follow the ADR structure:
   - **Status**: Proposed | Accepted | Deprecated | Superseded
   - **Context**: What problem or situation prompted this decision?
   - **Decision**: What was decided and why?
   - **Alternatives Considered**: What other options were evaluated?
   - **Consequences**: Positive and negative impacts
   - **References**: Links to relevant PRs, issues, docs

4. Use Docusaurus admonitions:
:::tip for the status badge
:::danger for breaking changes or risks
:::info for additional context

5. End with a "Veja tambem" section

6. Write in ${doc_language}
7. Base the ADR on ACTUAL changes found in the git history, not hypothetical scenarios
