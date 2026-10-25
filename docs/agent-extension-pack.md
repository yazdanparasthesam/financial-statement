# Agent Extension Pack

Everything in this pack makes Financial Statement *legible and safe* for coding agents — the Module 5
extension around the product. Components (spec-required directories, all present):

```
agent-capabilities/   reusable workflows + the prompt library (human-readable mirrors)
agent-hooks/          guardrails: PreToolUse command guard, PostToolUse lint/contract
                      reminders, git pre-commit secret scan
mcp-server/           read-only MCP server (10 tools) over the live API
custom-agent/         validation-auditor subagent definition + system prompt
docs/agent-extension-pack.md  (this file)
docs/permissions.md           who/what may do which action, and who approves
```

## How the pieces compose

```
 coding agent (Claude Code / Copilot CLI / MCP client)
   │  reads AGENTS.md + product-spec.md + openapi.yaml   ← context files
   │  guarded by agent-hooks (blocked: rm -rf, .env reads, force-push, prod writes)
   ▼
 MCP client ──stdio──► mcp-server/server.py ──HTTPS+JWT──► FastAPI (RBAC, gates, audit log)
   │                     READ-ONLY tools only                  │
   ▼                                                           ▼
 custom-agent/validation-auditor ──uses──► agent-capabilities/workflows/filing-audit.md
                                   └──► produces: audit memo (human acts on it)
```

## Running each piece

1. **MCP server:** `mcp-server/README.md` (needs a running backend + JWT).
2. **Hooks:** `agent-hooks/README.md` (Claude Code settings merge; git hook copy).
3. **Subagent:** `custom-agent/validation-auditor.md` (system prompt + invocation).
4. **Capabilities/prompts:** `agent-capabilities/README.md` (code is the source of truth;
   these files are the documented mirrors with usage notes).

## Design stance

The pack follows the course principle: **the model reasons; the system observes, authorizes,
verifies, and remembers.** Agents get sight (read-only MCP), guardrails (hooks), language
(prompts/capabilities), and specialists (subagent) — but every mutation still flows through
the authenticated API with RBAC, deterministic gates, and the audit log. Permission matrix:
`docs/permissions.md`; threat model: `security/agent-security.md`.

## Demo evidence (M8 checklist)

- [ ] MCP session transcript: list_filings → get_latest_validation → memo (against compose)
- [ ] guard.sh blocking `cat backend/.env` and allowing `pytest`
- [ ] validation-auditor run recorded in custom-agent/validation-auditor.md
- [ ] pre-commit hook blocking a planted fake key
