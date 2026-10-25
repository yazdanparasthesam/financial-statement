# Security & Audit Brief

Scope: the Financial Statement repository, its CI pipeline, its runtime AI usage, and its deployment.
This brief defines *what we scan, how, and how findings are triaged*. Raw outputs live in
`security/runs/<date>-<tool>/` (committed artifacts — criterion 13).

## Toolchain (deterministic scanners)

| Tool | Target | What it catches | Where in CI |
|---|---|---|---|
| `gitleaks` | whole repo | committed secrets/keys | `ci.yml` security job + pre-commit hook (`agent-hooks/`) |
| `bandit` | `backend/app` | Python security smells (exec, asserts, weak crypto, injection patterns) | `ci.yml` |
| `pip-audit` | `backend/requirements.txt` | known-vulnerable dependencies (PyPI advisories) | `ci.yml` |
| `semgrep` | `backend/app`, `frontend/src` | pattern-level bugs (hardcoded secrets, unsafe deserialization, XSS sinks) | `ci.yml` |
| `trivy` | filesystem + built images | CVEs in dependencies and base images | `ci.yml` |
| `npm audit` | `frontend/package-lock.json` | JS dependency advisories | `ci.yml` (non-blocking report) |

Reproduce locally:

```bash
pip install bandit pip-audit semgrep
cd backend
bandit -r app -x tests -f json -o ../security/runs/$(date +%F)-bandit/bandit.json
pip-audit -r requirements.txt --format json > ../security/runs/$(date +%F)-pip-audit/pip-audit.json
semgrep scan --config auto app ../frontend/src --json > ../security/runs/$(date +%F)-semgrep/semgrep.json
gitleaks detect --source .. --report-format json --report-path ../security/runs/$(date +%F)-gitleaks/gitleaks.json
trivy fs .. --format json -o ../security/runs/$(date +%F)-trivy/trivy.json
```

## Triage process

1. Every finding gets a row in the table below with disposition:
   **fix** (patch + test), **mitigate** (compensating control + note), **accept** (reason +
   expiry), or **false-positive** (evidence).
2. `fix` items block merge when severity ≥ HIGH (CI fails on gitleaks/bandit HIGH; trivy
   CRITICAL/HIGH reported, triaged same-day).
3. Dispositions are reviewed at each milestone boundary; the table is the record reviewers see.

## Findings log

| Date | Tool | Severity | Finding | Disposition |
|---|---|---|---|---|
| 2026-10-13 | design review | HIGH | JWT default secret `dev-secret-change-me` could ship to prod | **mitigated**: docs/deployment.md mandates generated secret; compose warns; prod checklist item; Render env is secret-marked |
| 2026-10-13 | design review | MED | CORS `*` acceptable in dev only | **mitigated**: deployment.md requires explicit `CORS_ORIGINS` in prod |
| 2026-10-13 | design review | MED | Uploaded XLSX parsed in-process (zip-bomb class) | **mitigated**: openpyxl read-only mode; 10 MB nginx `client_max_body_size`; documented |
| — | — | — | *(M9 full scan outputs append here)* | — |

## Adjacent policies

- AI data contract: `ai-data-policy.md`
- Agent/extension security: `agent-security.md`
- Secrets handling: `credentials-handling.md`
- PR audit records: `pr-audit/`
