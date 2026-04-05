# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (`master`) | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

To report a security vulnerability, open a [GitHub Security Advisory](https://github.com/venysssssssssss/docusaurus-reviewops/security/advisories/new).

Include:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (optional)

You will receive a response within **72 hours**. If the issue is confirmed, a patch will be released as soon as possible, typically within 7 days for critical issues.

## Security Model

### Workflow privilege separation

This project uses a two-workflow model designed to prevent privilege escalation:

| Workflow | Trigger | Permissions | Checks out PR code? |
|----------|---------|-------------|---------------------|
| `pr-ci.yml` | `pull_request` | `contents: read` | Yes — but with no write permissions |
| `pr-approval.yml` | `workflow_run` (after CI) | `pull-requests: write` | **No** — reads only API metadata |

The privileged workflow (`pr-approval.yml`) **never executes code from the PR**. It only reads PR metadata via the GitHub REST API. This eliminates the class of attacks where a malicious PR modifies workflows to escalate permissions.

Reference: [GitHub Docs — Secure use of `workflow_run`](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/)

### Fail-closed approval policy

The auto-approval bot (`approval_policy.py`) uses a fail-closed design:

- Any unexpected API response → **no approval**
- Any matching blocking label → **no approval**
- Any protected path touched → **no approval**
- Any error during evaluation → **no approval**

If in doubt, the bot does **not** approve. Human review is always the safe fallback.

### Blocking labels

PRs with the following labels are **never** auto-approved:

- `security`
- `breaking-change`
- `db-migration`
- `infra-change`
- `needs-human-review`

### Protected paths

PRs touching any of the following paths require human review:

- `.github/` — workflow and policy changes
- `infra/`, `terraform/`, `helm/` — infrastructure
- `migrations/`, `alembic/` — database schema
- `Dockerfile` — container definition
- `pyproject.toml`, `poetry.lock`, `package.json`, `pnpm-lock.yaml` — dependency manifests
- `docs-site/docusaurus.config.ts`, `docs-site/sidebars.ts` — portal configuration

## Dependency Security

Dependencies are monitored automatically by [Dependabot](.github/dependabot.yml):

- Python dependencies (pip) — weekly
- Node.js dependencies (npm) — weekly
- GitHub Actions — weekly

Dependabot PRs that touch `pyproject.toml` or `pnpm-lock.yaml` will **not** be auto-approved (protected paths). They require human review and merge.
