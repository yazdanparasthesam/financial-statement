# Permissions Model

Who — human or agent — may do what, through which surface, and what gates the action.

## Human roles (enforced server-side, JWT claim `role`)

| Action | preparer (owner) | reviewer | Enforcement point |
|---|---|---|---|
| Register/login | ✓ | ✓ | `routers/auth.py` |
| Create company / filing | ✓ (own) | ✗ | `routers/companies.py`, `routers/filings.py` (owner check) |
| Upload TB / map accounts / generate / validate | ✓ (own filings, status draft or changes_requested) | ✗ (403) | `deps.ensure_access(write=True)` + status locks |
| Read any filing | own only | **all** | `deps.ensure_access` |
| Submit / reopen | ✓ | ✗ | state machine role check |
| start_review / request_changes / accept / reject | ✗ (403) | ✓ | state machine role check |
| Submit gate | failing **error**-rule or missing statements ⇒ 422 | same on accept | `routers/workflow.py::_gate_errors` |
| Comments (add/resolve) | ✓ | ✓ | access-checked |
| Exports/checklist | ✓ | ✓ | access-checked, Bearer-authenticated download |

## AI components (runtime)

| Component | May do | May NOT do | Gate/approval |
|---|---|---|---|
| Gemini provider + LangGraph graphs (via `ai_service`) | produce prose over server-provided figures; call the read-only agent tools; log own call metadata | compute statement figures; mutate any row; see redacted identifiers | every output is stored as *draft/explanation/memo*; humans finalize notes and apply mappings |
| Agent tools (ReAct/ReWOO registry) | serialize deterministic reads: statements, validation, anomalies, checklist, deadline, ratios | any write — no mutating tool exists | tools are zero-arg closures over service reads; RBAC of the calling user still applies |
| MockChatModel | identical LangChain surface, deterministic replies | — | same |

## Agent extension pack

| Component | Permission | Scope | Revocation |
|---|---|---|---|
| MCP server tools | **read-only** GETs | whatever FS_TOKEN's user may read (RBAC still applies) | unset token / delete user |
| `guard.sh` (PreToolUse) | block/allow agent shell commands | local dev machine | remove hooks.json entry |
| `post_edit_check.sh` | lint + reminders (non-mutating) | edited files | remove hooks.json entry |
| pre-commit gitleaks | block commits containing secrets | staged git changes | `.git/hooks/pre-commit` removal (not advised) |
| validation-auditor subagent | MCP read tools + memo writing | one filing per run | host agent config |

## Principles

1. **Least privilege:** agents get read; writes require an authenticated human action.
2. **Gates are deterministic:** no AI output can open a workflow gate.
3. **Everything is remembered:** `audit_log` (state changes) + `ai_requests` (LLM calls) +
   `review_events` (transitions) reconstruct any decision after the fact.
4. **Fail closed:** missing token ⇒ MCP refuses; unrecognized dangerous pattern ⇒ guard blocks.
