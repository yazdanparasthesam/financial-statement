# Implementation Summary

Living build journal — what was built, how it was verified, what the tests caught.
(The AI-assisted development *process* is documented in docs/ai-workflow.md.)

## M0–M2 — Foundation + full-stack core (COMPLETE)

**Backend (FastAPI, 32 endpoints, layered routers → services → domain ← infra):**
JWT auth + RBAC (preparer/reviewer) · companies · filings with statutory deadline math
(period end + 4 months, month-end clamped) · CSV/XLSX trial-balance ingestion with tolerant
header detection · deterministic auto-mapping (prefix chart 11/12/21/22/3/4/5/6/7/8/82 +
keyword fallback) · versioned statement generation (P&L + Balance Sheet; equity includes
current-year profit) · 6-rule validation engine (R001–R006) incl. year-over-year anomaly
detection vs prior-year statements · workflow state machine with deterministic
submit/accept gates (failing error-rules block; warnings don't) · review comments +
events + global audit log · AI endpoints (explain anomaly / draft note / suggest mappings /
grounded chat) behind a provider adapter (Gemini ⇄ deterministic Mock) with `ai_requests`
logging + identifier redaction · PDF/XLSX exports · filing checklist · /healthz · /version.

**Contract:** openapi.yaml generated from the app (`make openapi`); integration test fails
CI on any drift, in both directions.

**Frontend (React 18 + Vite + TS + Tailwind + TanStack Query):** centralized typed API
client (auth header, error mapping, authenticated blob downloads) · auth pages · dashboard
(companies, filings, deadline badges) · 8-tab filing workspace (trial balance + mapping +
AI suggestions, statements, validation report, anomalies, notes editor, chat, review
workflow, exports/checklist) · pure-logic libs (workflow mirror, validation summary,
formatting) each with vitest suites.

**Verification (all green at hand-off):**
- backend: 54 pytest tests (unit + integration + contract) — `cd backend && python -m pytest`
- backend lint: ruff clean with committed ruff.toml
- frontend: 25 vitest tests; `npm run build` (tsc --noEmit + vite) clean; 245 kB bundle
- seed data math: all four CSVs balance-checked; demo story produces +69.2% revenue anomaly

**Bugs the tests caught during the build (the gates earn their keep):**
1. pydantic email-validator rejects `.local` TLD → test fixtures moved to `@example.com`.
2. fpdf2 core fonts are latin-1 → em-dash crashed PDF export → `_safe()` sanitizer + test.
3. Mapping only one leg of a debit/credit pair breaks the balance-sheet identity → R002
   correctly fails → integration test now proves the 422 submit-gate names the rule, then
   proves the human-in-the-loop repair path (map second leg → clean → submit 200).
4. Calendar-dependent deadline assertions → tests derive fiscal years from `date.today()`.
5. "cred" missing from accepted credit-column headers → ingestion test caught it.
6. Contract test compared paths against the whole spec document instead of `spec["paths"]`.

## M2.5 — Formula engine + LangChain/LangGraph agents (COMPLETE)

**Formula engine (the صورت مالی core):** seed story rewritten around a depreciation-consistent
two-year narrative (prior-year loss −120,000 → current turnaround +60,000; trial balances
909,000/839,000 balanced) · **cash-flow statement, indirect method** (`domain/cashflow.py`,
kind `cf`, versioned like pl/bs, generated when a prior-year balance sheet exists) ·
**10 financial ratios** with formula strings + interpretations (`domain/ratios.py`,
`GET /api/filings/{id}/ratios`) · rules **R007** (cash-flow reconciliation, |gap| ≤ 1.0) and
**R008** (current ratio < 1) · frontend Statements tab gained the cash-flow card (with the
R007 reconciliation badge) and the ratios panel (formula shown per row).

**AI layer rebuilt on LangChain + LangGraph (three agent patterns):**
`infra/ai/providers.py` — `MockChatModel` (a real `BaseChatModel`, deterministic per prompt
marker) + `ChatGoogleGenerativeAI` behind `AI_PROVIDER` · `infra/ai/graphs.py` —
**self-criticism** notes loop (draft → critique → bounded revise → finalize; trace recorded
in the audit event), **ReAct** assistant (`langchain.agents.create_agent` over six read-only
filing tools), **ReWOO** audit memo (planner → executor → solver; new endpoint
`POST /api/filings/{id}/audit-memo`, surfaced as a Review-tab action) · every call still
logged to `ai_requests`; failures still degrade to "[AI UNAVAILABLE]".

**Verification (all green at hand-off):** backend 64 pytest tests (54 unit — incl. 14 over
providers/graphs — + 10 integration incl. contract) · ruff clean · frontend 27 vitest +
`tsc --noEmit` + production build clean · openapi.yaml regenerated (34 paths; contract test
green) · live smoke `ops/smoke.sh` **24/24** including cash-flow totals, ratio values and one
call per agent pattern.

**Bugs this round's tests caught (numbering continues from M0–M2):**
7. `StateGraph(dict)` silently drops accumulated state (output = last node's return only) →
   TypedDict state schemas are mandatory; caught by graph unit tests.
8. A critique parser defaulting to `accept=False` on unparsable JSON would spin the revise
   loop to its bound every call → fail-open default ("accept, with a note") + explicit test.
9. Blanket `str.replace` injected the R007/R008 block into BOTH identical `return` statements
   in validators.py (the early-return branch referenced an undefined `bs`) → anchor-based
   surgery; lesson recorded: check every occurrence before a blanket replace.
10. `create_react_agent` moved to `langchain.agents.create_agent` in LangChain v1 (deprecation
    warning under pytest) → prefer the v1 API with an import fallback; pinned
    `langchain>=1.0` in requirements.

## M3–M10 — Roadmap (details in docs/ and the project plan)

M4 live Gemini verification with a real key · M6 docker-compose E2E on the host ·
M7 CI/CD + Render/Neon deployment + public URLs in README · M8 agent extension pack live
demos (MCP against the running API, hook guard demo, validation-auditor transcript) ·
M9 security scan artifacts committed under security/runs/ + PR-audit record ·
M10 README polish, evidence pack, official 12-criterion self-audit (README §Project rubric guide).

## M11 — Observability, alerting & on-call responder (COMPLETE)

- `backend/app/infra/telemetry/` — `tracing.py` (opt-in OTLP via `OTEL_ENABLED`; trace-id
  helper), `metrics.py` (6 `fs_*` business metrics + exemplars), `logging_conf.py`
  (whitelist JSON formatter, OTLP log bridge, request middleware logging route templates).
  Hooks in pipeline/workflow/trial-balance/ai-service. `/metrics` exposed (schema-hidden).
  10 unit tests incl. the PII-whitelist, native OTLP trace/span correlation, and raw-URL redaction guarantees.
- `observability/` + compose `--profile obs` — OTel collector → Tempo (traces) & Loki
  (logs, derived trace_id → Tempo links), Prometheus (10s scrape + rules), Alertmanager
  (10s group_wait → internal responder service webhook), Grafana :3001 (provisioned datasources + 10-panel
  golden-journey dashboard). App-only compose unchanged.
- Alerts (user impact): BackendDown · SubmitFlowErrors (5xx on submit/review) ·
  GoldenJourneyLatencyHigh (p95>2s) · AIUnavailableSpike — ADR 7: Prometheus rules, not
  Grafana-provisioned alerts.
- `oncall-agent/` — deterministic Compose responder: internal webhook :8090, runbooks.yaml, command
  exact command grammar (`docker compose` safe subcommands/`echo`/`true`; else rc=126 REFUSED), cooldown,
  verify loop, incident reports → `ops/incidents/`. 10 engine tests. Verified live:
  webhook → remediated report; no-docker environment → graceful escalation.
- `ops/alert-drill.sh` (full + `--simulate`); smoke.sh 24 → 28 checks (adds /metrics).
- Docs: docs/observability.md · oncall-agent/README.md · security/telemetry-policy.md ·
  docs/agent-team.md · ops/runbooks/{backend-down,submit-flow-errors,high-latency,
  ai-unavailable}.md · ADRs 7–9.

## M12 — CI/CD environments, tracker & docs sweep (COMPLETE)

- `deploy.yml` split: **dev** auto on green CI (`workflow_run`) + **prod** manual
  (`workflow_dispatch` + `environment: production` gate, optional sha input); post-deploy
  smoke per env. `rollback.yml`: revert-by-dispatch (SHA or HEAD) → push/PR fallback +
  Render instant-rollback runbook. `ci.yml` gained the on-call engine test job.
- `tracker/` — 14 issues (acceptance criteria + agent evidence logs) + `import.sh`
  (idempotent GitHub Issues import, `--sync-state` closes completed ones).
- README rubric table rewritten to the official 12 criteria; AGENTS.md doc map;
  .env.example telemetry block; Makefile targets (`obs-up`, `oncall`, `drill`, …).

**Post-M12 verification:** ruff clean; backend pytest **74 passed** (64 unit + 10 integration/contract); on-call agent **10 passed**; frontend vitest 27/27 (unchanged); live smoke **28/28** incl. metrics; compose/YAML parsed. Compose stack and Docker socket remediation require user-side Docker verification (sandbox has no Docker daemon); public repo/Render deployment and hosted CI also remain owner steps.
