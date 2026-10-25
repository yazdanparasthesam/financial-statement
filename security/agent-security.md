# Agent & Extension Security Notes

Covers the agent extension pack: `mcp-server/`, `agent-hooks/`, `custom-agent/`,
`agent-capabilities/`. Permission matrix: `docs/permissions.md`.

## Threat model (agents pointed at this project)

| Threat | Control |
|---|---|
| Agent mutates production data via tools | MCP server exposes **read-only** tools (list/get/latest); no create/update/delete tools exist |
| Stolen/overbroad token used by agent | MCP requires an explicit `FS_TOKEN` env var; use a **reviewer or scoped preparer** account, never an admin-like secret; token can be revoked by deleting the user |
| Agent runs destructive shell commands | `agent-hooks/guard.sh` (PreToolUse) blocks `rm -rf /`, force-push to main, `.env` reads/writes, `docker system prune`, direct prod curls with secrets — hook exits non-zero ⇒ tool call denied |
| Secret exfiltration via commits | `agent-hooks/pre-commit-gitleaks.sh` + gitleaks in CI |
| Prompt injection via statement data | LLM prompts embed only figures/labels (no executable context); outputs are prose that a human reviews; suggestions require explicit PATCH; system prompt forbids echoing identifiers |
| Agent silently drifts the contract | AGENTS.md law 2 + CI contract-drift test make drift loud and red |
| Post-edit regressions | PostToolUse hook runs `ruff` on edited backend files and reminds to `make openapi` |

## MCP server specifics

- Transport: stdio (local agent only; no network listener opened).
- Auth: bearer token from env → forwarded to the backend; the backend's RBAC still applies —
  the MCP server has **no privilege of its own**.
- Data exposure: same categories as the runtime AI policy (aggregates, statuses, prose);
  never credentials.
- Kill switch: unset `FS_TOKEN` / remove the server from agent config.

## Hook specifics

- Hooks are advisory defense-in-depth for *local* agent runs; the authoritative gates remain
  server-side (RBAC, workflow gates) and CI (tests, scans).
- `guard.sh` fails **closed** on unrecognized destructive patterns (deny + reason on stderr).

## Verification evidence (M8)

`mcp-server/README.md` records a live tool-call session against the running API;
`agent-hooks/README.md` records a blocked command and an allowed command;
`custom-agent/validation-auditor.md` contains the run transcript.

## On-call responder agent (`oncall-agent/`)

The responder is the only agent that **executes shell commands at runtime**, so it is
built as the opposite of an LLM agent:

| Threat | Control |
|---|---|
| Arbitrary command execution via crafted alerts | alertname → static `runbooks.yaml`; the alert payload can never inject a command |
| Runbook typo/malicious edit runs destructive shell | Exact token grammar in `agent.py`: safe `docker compose ps|logs|restart backend`, `echo`, `true`; no shell. `docker compose down -v` and `exec` tests are refused with rc=126 `REFUSED` |
| Restart storm / thrashing | Per-fingerprint cooldown (5 min default) + Alertmanager `repeat_interval: 1h` |
| Blind action on ambiguous signals | Warnings (latency, AI errors) have `action: ""` — diagnose + escalate only |
| Silent failure | Every alert produces a markdown incident report with the full command timeline in `ops/incidents/` |
| Webhook abuse (unauthenticated POST :8090) | Compose binds 8090 to 127.0.0.1 only; service webhook is internal. The obs profile mounts Docker socket (high privilege), so local/demo only; exact command grammar and read-only repo/report-only RW mounts constrain the responder |
| Dependency CVEs | stdlib + PyYAML only — the smallest auditable surface of any component |
