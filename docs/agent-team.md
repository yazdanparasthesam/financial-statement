# The agent team — who does what, and how they hand off

This project is built and operated by a **team of agents** around one human owner.
The team is defined by *artifacts*, not by chat: every handoff is a file in the repo,
which keeps the process reproducible and auditable.

## Roster

| Agent | Role | Where it lives | Scope of power |
|---|---|---|---|
| **Arena Agent** | Architect & reviewer — spec, design, rubric audits, complex implementations, review passes | this conversation + commits authored by the owner | full repo (human-in-the-loop per step) |
| **GitHub Copilot CLI** | Designated headless implementer — invoke for batch code generation from AGENTS.md | `custom-agent/`, invoked via `gh copilot` / CLI | repo files; guarded by `agent-hooks/guard.sh` |
| **CI scanners** | Automated reviewer — ruff, pytest, vitest, gitleaks, bandit, pip-audit, semgrep, trivy, contract-drift gate | `.github/workflows/ci.yml` | read + block merge |
| **MCP server** | Read-only data plane for any external agent (list/get filings & statements) | `mcp-server/` | GET-equivalent only, user-scoped token |
| **On-call responder** | Runtime operator — wakes on Alertmanager webhooks, runs allow-listed runbook commands, writes incident reports | `oncall-agent/` | exact runbook command grammar ONLY (rc=126 otherwise) |
| **Human owner** | Decisions, secrets, deploys to prod, escalations | — | everything |

## The working process (spec → ship → respond)

```
 product-spec.md ──► tracker/issues/*.md ──► implementation ──► verification
   (Arena Agent)          (acceptance criteria)    (Copilot CLI /     (pytest, ruff,
                        ▲   │                  Arena Agent)            vitest, smoke)
                        │   ▼                                        │
                   evidence log  ◄──── review (Arena Agent + CI scanners) ◄┘
                        │                                            │
                        ▼                                            ▼
                 gh issue close ──────────────────────► CI green ──► deploy dev (auto)
                                                                     deploy prod (manual)
                                                                            │
                     ┌──────────────────────────────────────────────────────┘
                     ▼
   runtime: metrics/traces/logs ──► Prometheus rules ──► Alertmanager ──► ON-CALL AGENT
                     ▲                                                       │
                     └──── Grafana dashboard ◄── ops/incidents/*.md ◄────────┘
                                              (fix + verify, or escalate to human)
```

**Handoff contracts** (files as the interface between agents):

1. `AGENTS.md` — the constitution every coding agent reads first (stack laws, doc map).
2. `tracker/issues/*.md` — acceptance criteria + per-issue **agent evidence log**
   (which agent did what, how it was verified). Imported to GitHub Issues via
   `tracker/import.sh` — the public tracker.
3. `docs/*` + `security/*` — modular deep docs AGENTS.md points to (never duplicated).
4. `ops/incidents/*.md` — the responder agent's output; the human's input.
5. `agent-capabilities/prompts/*` — the exact prompts used for the headless runs.

## Working agreements (the laws)

- **One source of truth:** formulas live in `backend/app/domain/`, never in the frontend.
- **Contract first:** `openapi.yaml` regenerated + drift-gated in CI; agents may not
  silently change the API.
- **Everything verified on disk:** no deliverable is declared done until tests/scripts
  were actually run (this caught real defects — e.g. the telemetry status-label audit).
- **Agents don't touch secrets or prod:** deploy hooks and the prod gate belong to the
  human; the responder's command allowlist enforces the same principle at runtime.
- **Incidents are evidence:** every alert produces a report, even when suppressed or
  escalated — the drill (`ops/alert-drill.sh`) is part of the definition of done.

## Evidence the team was actually used

- Per-issue agent logs in `tracker/issues/` (all 14).
- Dev log D1–D6 (AI-layer iterations) in `IMPLEMENTATION_SUMMARY.md`.
- `security-audit/pr-audit/` — review of agent-produced PRs.
- Incident reports from drills in `ops/incidents/` (+ `oncall-agent/example-incident.md`).
- CI runs exercising the scanner + on-call test jobs.
