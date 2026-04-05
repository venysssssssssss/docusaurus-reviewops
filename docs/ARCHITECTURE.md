# Architecture

## System Overview

docusaurus-reviewops is a drop-in governance system for GitHub repositories. It combines automated PR review with a versioned documentation portal and an LLM-powered doc generation system.

```
PR opened
 │
 ▼
┌─────────────────────────────────────────────────┐
│ pr-ci.yml (unprivileged: contents: read)        │
│  ├─ quality-gates: ruff, mypy, pytest + cov     │
│  └─ docs-gates: guardrails, openapi, docusaurus  │
└─────────────────────────────────────────────────┘
 │ all checks pass
 ▼
┌─────────────────────────────────────────────────┐
│ pr-approval.yml (privileged: pull-requests: write)│
│  └─ approval_policy.py evaluates 11+ conditions  │
│     NEVER checks out PR code (security critical)  │
└─────────────────────────────────────────────────┘
 │ approved
 ▼
merge → master
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

The privileged workflow runs `approval_policy.py` from the `master` branch only. It never executes PR-submitted code. This eliminates the class of attacks where a PR modifies CI to auto-approve itself.

Reference: [GitHub Security Lab — Preventing pwn requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/)

### fail_closed Principle

The approval bot follows `fail_closed`: any unrecognized condition results in silent exit (exit code 0, no approval). The absence of approval IS the governance — it's not a failure state.

`fail_closed()` is typed `-> NoReturn`, enabling mypy type narrowing after calls.

## Component Map

### Python Scripts (.github/scripts/)

| File | Purpose |
|------|---------|
| `approval_policy.py` | 11+ rejection conditions, then APPROVE via REST API |
| `docs_guardrails.py` | Fail CI if public code changed without docs; AREA_DOC_MAP suggests correct doc section |

### Workflows (.github/workflows/)

| File | Trigger | Purpose |
|------|---------|---------|
| `pr-ci.yml` | `pull_request` | Quality gates + docs gates + coverage (≥80%) |
| `pr-approval.yml` | `workflow_run` (after pr-ci) | Auto-approve eligible PRs |
| `docs-deploy.yml` | `push` to `master` | Build + deploy to GitHub Pages |
| `docs-version-pr.yml` | `push` tag `v*.*.*` | Freeze docs + open PR |
| `docs-gen.yml` | `pull_request` (advisory) | Post LLM doc suggestions as PR comment |

### Approval Policy Constants

```python
BLOCKING_LABELS     = {'security', 'breaking-change', ...}   # labels that block approval
PROTECTED_PATTERNS  = [r'^\.github/', r'^infra/', ...]        # path patterns that block approval
MAX_CHANGED_FILES   = 30      # file count limit
MAX_TOTAL_DELTA     = 800     # total lines added + removed
MAX_NET_CHANGE      = 400     # |additions - deletions| — detects rewrites masked as refactors
```

### Docs Guardrails Policy

- **Small PRs** (≤ 3 public files changed): any doc touch satisfies (CHANGELOG, README, docs-site/docs/)
- **Large PRs** (> 3 public files): requires at least 1 file in `docs-site/docs/` or `docs/`
- **AREA_DOC_MAP**: semantic source→docs mapping shown in error messages to guide the developer

### Docgen System (scripts/docgen/)

LLM-powered doc generation with pluggable providers:

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point — `python -m scripts.docgen.cli` |
| `config.py` | Load `.docgen.yml`, resolve env vars |
| `providers/` | Ollama, Anthropic, OpenAI, Claude Code CLI, Mock |
| `generators/` | architecture, standards, runbook, ADR, changelog, API enricher |
| `analyzer/` | File tree, language detection, SHA256 hashing for cache |
| `output/` | Frontmatter, merger (preserve/overwrite/append), writer |
| `cache/` | Incremental generation cache (`.docgen-cache/`) |

Generator return type: `tuple[str, LLMResponse | None]` — threads cost tracking to CLI summary.

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

### Compliance Files

| File | Purpose |
|------|---------|
| `LICENSE` | MIT License |
| `SECURITY.md` | Vulnerability reporting policy |
| `.github/dependabot.yml` | Weekly automated dependency updates |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist |
| `.github/ISSUE_TEMPLATE/` | Bug report, feature request, config |
| `.pre-commit-config.yaml` | Pre-commit hooks (ruff, mypy, detect-private-key) |
| `.env.example` | Environment variable reference |

## Data Flow

1. Developer opens PR with code + docs
2. `pr-ci.yml` runs lint, types, tests (with coverage gate ≥80%), docs build
3. If CI passes, `pr-approval.yml` evaluates the PR via REST API
4. If eligible (11+ conditions), bot posts APPROVE review
5. On merge to `master`, `docs-deploy.yml` builds and deploys portal
6. On tag push, `docs-version-pr.yml` freezes docs for that version
7. Developer can run `make docs-gen` to generate or update docs via LLM

## Tech Stack

- **Python 3.12+**: approval_policy.py, docs_guardrails.py, docgen system
- **Docusaurus 3.9.2**: Static site generator (React, TypeScript)
- **pnpm**: Node package manager (strict mode)
- **GitHub Actions**: CI/CD orchestration
- **GitHub Pages**: Hosting target
- **LLM Providers**: Ollama (local), Anthropic Claude, OpenAI GPT-4o, Claude Code CLI
