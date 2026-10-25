# AI Tool & Data Policy

What data leaves this system for AI processing, what never does, and how it is governed.

## 1. Runtime AI (the product's Gemini integration — LangChain providers, LangGraph agents)

**Sent to the provider** (only when `AI_PROVIDER=gemini`):
- statement **aggregates** and section totals (from `statements_summary`);
- validation result messages and rule ids;
- anomaly figures (prior/current/pct) and account code/name;
- unmapped account code/name/debit/credit (mapping suggestions);
- the user's chat question plus the grounded filing context above;
- ReWOO audit-memo prompts: the same aggregates plus the text output of the read-only tools
  (validation lines, anomaly figures, checklist state, ratio values) — all server-generated,
  all already restricted to statement-level data.

**Never sent** (hard rules in code and prompts):
- passwords, password hashes, JWTs, API keys;
- `national_id`, `economic_code`, user emails — stripped by `services/ai_service.redact()`
  before prompt construction;
- full trial balances or raw uploaded files;
- anything from `users`, `audit_log`, `ai_requests` tables.

**Retention & logging:** we store *metadata only* — `ai_requests` keeps kind, provider,
model, a 16-hex SHA-256 prefix of the prompt (for dedup/audit), status, latency. Prompt and
completion bodies are **not persisted**.

**Failure posture:** provider errors degrade to a clear "[AI UNAVAILABLE]" message; all
deterministic features (statements, validation, workflow, exports) are unaffected by design.

**Opt-out:** `AI_PROVIDER=mock` gives a fully functional, fully deterministic system with
zero external AI calls — this is what tests and CI run.

## 2. Development-time AI (coding agents)

- Agents work on the repository and synthetic seed data only; no production data exists in
  this course project.
- Secrets never enter prompts or commits: `.env` is gitignored, `.env.example` has
  placeholders, gitleaks runs in CI and as a pre-commit hook (`agent-hooks/`).
- Agent instructions (`AGENTS.md`) forbid softening gates, auto-applying model suggestions,
  or bypassing the AI call logger.
- Every AI-authored change passes the same gates as human changes: ruff, 74 backend tests,
  27 frontend tests, contract drift check, build (see `docs/ai-workflow.md`).

## 3. Responsibility

The preparer finalizes every AI-drafted note; a human applies every mapping suggestion;
reviewers accept filings — the AI holds no authority over state transitions. This mirrors
the permission model in `docs/permissions.md`.
