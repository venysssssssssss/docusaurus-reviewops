# Architecture

## System Overview

docusaurus-reviewops is a drop-in governance system for GitHub repositories. It combines automated PR review with a versioned documentation portal.

```
PR opened
 │
 ▼
┌─────────────────────────────────────────────────┐
│ pr-ci.yml (unprivileged: contents: read)        │
│  ├─ quality-gates: ruff, mypy, pytest, compileall│
│  └─ docs-gates: guardrails, openapi, docusaurus  │
└─────────────────────────────────────────────────┘
 │ all checks pass
 ▼
┌─────────────────────────────────────────────────┐
│ pr-approval.yml (privileged: pull-requests: write)│
│  └─ approval_policy.py evaluates 11 conditions   │
│     NEVER checks out PR code (security critical)  │
└─────────────────────────────────────────────────┘
 │ approved
 ▼
merge → main
 │
 ▼
┌─────────────────────────────────────────────────┐
│ docs-deploy.yml → GitHub Pages (< 5 min)        │
└─────────────────────────────────────────────────┘
 │
 ▼
git tag v*.*.* →
┌─────────────────────────────────────────────────┐
│ docs-version-pr.yml → freeze docs + open PR     │
└─────────────────────────────────────────────────┘
```

## Security Model

The two-workflow split is the architectural cornerstone:

| Workflow | Trigger | Permissions | Checks out PR code? |
|----------|---------|-------------|---------------------|
| pr-ci.yml | `pull_request` | `contents: read` | Yes (must, to lint/test) |
| pr-approval.yml | `workflow_run` | `pull-requests: write` | **Never** |

The privileged workflow runs `approval_policy.py` from `main` branch only. It never executes PR-submitted code. This eliminates the class of attacks where a PR modifies CI to auto-approve itself.

### fail_closed Principle

The approval bot follows `fail_closed`: any unrecognized condition results in silent exit (exit code 0, no approval). The absence of approval IS the governance — it's not a failure state.

## Component Map

### Python Scripts (.github/scripts/)

| File | Purpose | Lines |
|------|---------|-------|
| `approval_policy.py` | 11 rejection conditions, then APPROVE | ~120 |
| `docs_guardrails.py` | Fail CI if public code changed without docs | ~50 |

### Workflows (.github/workflows/)

| File | Trigger | Purpose |
|------|---------|---------|
| `pr-ci.yml` | `pull_request` | Quality gates + docs gates |
| `pr-approval.yml` | `workflow_run` (after pr-ci) | Auto-approve eligible PRs |
| `docs-deploy.yml` | `push` to main | Build + deploy to GitHub Pages |
| `docs-version-pr.yml` | `push` tag v*.*.* | Freeze docs + open PR |

### Docusaurus Portal (docs-site/)

| File | Purpose |
|------|---------|
| `docusaurus.config.ts` | Portal config (plugins, themes, navbar) |
| `sidebars.ts` | Sidebar structure |
| `src/css/custom.css` | Visual customization (~200 lines) |
| `src/webpack-fallback-plugin.js` | CJS/ESM compat + Node fallbacks + splitChunks |
| `src/theme/` | 6 swizzled components (ESM wrappers for CJS upstream) |
| `src/pages/404.tsx` | Custom 404 page |
| `docs/` | Markdown content |

### Utility Scripts (scripts/)

| File | Purpose |
|------|---------|
| `export_openapi.py` | Export FastAPI OpenAPI schema to JSON |
| `validate_config.py` | Check for TODO placeholders before deploy |
| `setup_reviewops.sh` | Install into existing repo (--dry-run, --yes) |

## Data Flow

1. Developer opens PR with code + docs
2. `pr-ci.yml` runs lint, types, tests, docs build
3. If CI passes, `pr-approval.yml` evaluates the PR via REST API
4. If eligible, bot posts APPROVE review
5. On merge to main, `docs-deploy.yml` builds and deploys portal
6. On tag push, `docs-version-pr.yml` freezes docs for that version

## Tech Stack

- **Python 3.12+**: approval_policy.py, docs_guardrails.py, export_openapi.py
- **Docusaurus 3.9.2**: Static site generator (React, TypeScript)
- **pnpm**: Node package manager (strict mode)
- **GitHub Actions**: CI/CD orchestration
- **GitHub Pages**: Hosting target
