# Agent Hooks (guardrails)

Three hooks, two protocols:

| File | Protocol | When | Effect |
|---|---|---|---|
| `hooks.json` + `guard.sh` | Claude Code `PreToolUse` (matcher: Bash) | before any agent shell command | **Blocks** destructive deletes, force-pushes, `.env` reads, destructive SQL, prod mutations over HTTP (exit 2 ⇒ denied, reason fed back) |
| `post_edit_check.sh` | Claude Code `PostToolUse` (matcher: Edit/Write) | after any file edit | Runs `ruff` on edited backend files (errors fed back); reminds `make openapi` on contract-relevant edits; reminds frontend tests |
| `pre-commit-gitleaks.sh` | git `pre-commit` | at commit time | Blocks staged secrets (gitleaks, with dependency-free fallback) |

Install (Claude Code): merge `hooks.json` into `.claude/settings.json` (or project
`.claude/settings.local.json`). Install (git): copy `pre-commit-gitleaks.sh` to
`.git/hooks/pre-commit` and `chmod +x`.

For agents without hook support (e.g. Copilot CLI), the same rules are stated in `AGENTS.md`
§Non-negotiable laws — hooks are defense-in-depth, the server-side gates remain the
authoritative control.

**Demo evidence (M8):** one blocked command (`cat backend/.env` → deny message) and one
allowed command, recorded here.
