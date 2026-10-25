# AGENTS.md — Instructions for coding agents working on Financial Statement

You are operating on a course-project codebase that is graded on structure, contracts, tests,
and documentation. Follow these rules exactly; they encode decisions that must not drift.

## Project in one paragraph

Financial Statement turns trial balances into statutory financial statements (P&L + Balance Sheet),
validates them with deterministic rules, assists with AI (explanations/drafts/suggestions
only), and runs a preparer→reviewer submission workflow with audit trails. FastAPI backend,
React frontend, SQLite/Postgres, LangChain/LangGraph AI layer (Gemini or deterministic mock;
self-criticism, ReAct and ReWOO agents), Docker Compose, GitHub Actions.

## Documentation map (read the module you are touching)

| Doc | Read it when… |
|---|---|
| [product-spec.md](product-spec.md) | touching rules R001–R009, journeys, personas, glossary |
| [docs/architecture.md](docs/architecture.md) | touching layers, data model, ADR-lite decisions (1–9) |
| [docs/ai-workflow.md](docs/ai-workflow.md) | touching prompts, graphs, provider behavior |
| [docs/testing.md](docs/testing.md) | writing/fixing tests, markers, fixtures |
| [docs/deployment.md](docs/deployment.md) | touching CI/CD, Render/Neon, secrets, rollback |
| [docs/observability.md](docs/observability.md) | touching metrics/logs/traces, the obs compose profile, alerts |
| [docs/operations.md](docs/operations.md) | runbooks, diagnostics, drills, data ops |
| [docs/agent-team.md](docs/agent-team.md) | who (which agent) does what; handoff artifacts |
| [docs/agent-extension-pack.md](docs/agent-extension-pack.md) + [docs/permissions.md](docs/permissions.md) | MCP server, hooks, subagent, permission matrix |
| [security/](security/) | telemetry privacy policy, AI data policy, agent security, credentials handling |
| [tracker/](tracker/) | the task queue: issues with acceptance criteria + evidence logs |

## Non-negotiable laws

1. **The AI never computes.** Any number that appears in a statement, validation result,
   checklist, or deadline MUST come from `backend/app/domain/*` (pure functions). LLM output
   is prose only. If a task seems to need model arithmetic, stop and re-read this rule.
2. **The contract is frozen.** `openapi.yaml` at the repo root is the source of truth. After
   ANY router/schema change run `make openapi` and commit the regenerated file. The CI
   contract test fails on drift — never edit the yaml by hand to make a test pass.
3. **Suggestions ≠ mutations.** AI mapping suggestions are returned to the client; only a
   human action (`PATCH .../accounts/{id}`) changes data. Never auto-apply model output.
4. **Every LLM call goes through `services/ai_service`** (`call_ai`, `run_notes_draft`,
   `run_chat`, `run_audit_memo`) — each logs to `ai_requests` and redacts identifiers.
   Do not call providers or graphs directly from routers.
5. **Secrets never enter the repo.** `.env` is gitignored; `.env.example` holds placeholders.
   If you see a real key anywhere, remove it, say so loudly, and advise rotation.
6. **Gates stay deterministic.** Submit/accept blocking logic lives in
   `routers/workflow.py::_gate_errors` + `domain/workflow.py`. Don't soften gates.
7. **Agent loops are bounded; agent tools are read-only.** The self-criticism revise loop is
   capped by `Settings.ai_max_critique_loops` (default 2); the ReWOO executor runs at most
   `max_steps` planned tools and drops unknown names. Tools in `ai_service.tools_registry`
   only serialize deterministic domain output — never add a mutating tool, never let a model
   request one, and never raise the caps to make a failing test pass.

8. **Telemetry describes the system, never the customer.** The log formatter emits only its
   whitelist (`method, route, status, duration_ms, step, rule_id`) — do not add fields
   carrying user data, ids or figures; metric labels come from fixed enumerations only.
   The on-call agent's command allowlist (`oncall-agent/agent.py`) is a security control:
   never extend it to make a drill pass. Both contracts are unit-tested and specified in
   `security/telemetry-policy.md`.

## Layer rules (backend)

```
routers/    HTTP concerns ONLY: parse, authorize (deps), call services, shape responses
services/   orchestration: pipeline.py (generate/validate/checklist), ai_service.py, audit.py
domain/     PURE business logic, no imports from routers/services/infra, no IO
infra/      IO adapters: ingestion (files), ai (providers), exports (pdf/xlsx)
```

Dependency direction is strictly inward: routers → services → domain; infra is used by
services/routers at the edges. `models.py`/`schemas.py`/`db.py`/`deps.py`/`security.py`/
`config.py` are the shared kernel. New validation rule = new R-id in `domain/validators.py`
+ unit test + row in product-spec.md §5.

## Frontend rules

- ALL HTTP goes through `src/api/client.ts` (`api.*` + `download`). Never call `fetch`
  from a component.
- Types in `src/api/types.ts` mirror `openapi.yaml`.
- Pure UI logic lives in `src/lib/*` and gets a vitest suite in `src/lib/__tests__/`.
- The workflow mirror in `src/lib/workflow.ts` is a UI hint; the server always re-checks.
- Styling: Tailwind utilities + the `.card/.btn/.input/.label/.th/.td` classes in `index.css`.

## Definition of done for any change

1. `cd backend && ruff check app tests scripts` → clean.
2. `cd backend && python -m pytest` → all green (unit + integration + contract).
3. `cd frontend && npm test && npm run build` → green.
4. `python -m pytest oncall-agent/tests -q` → green (or `make test`, which includes it).
5. `make openapi` → commit the regenerated file if it changed.
6. Docs touched when behavior changed: product-spec.md (rules/FRs), docs/ai-workflow.md
   (if prompts/AI behavior changed), docs/observability.md (if signals/alerts changed),
   README (if user-visible flow changed).

## Testing conventions

- Unit tests: pure domain only, no DB/HTTP, `@pytest.mark.unit`, in `backend/tests/unit/`.
- Integration: real app + DB via TestClient, `@pytest.mark.integration`, in
  `backend/tests/integration/`. Fixtures in `tests/conftest.py` (env is set BEFORE app import;
  AI is always mock in tests; emails must use `@example.com` — `.local` is rejected by the
  email validator).
- Dates: never hardcode today-relative assertions; derive from `date.today()` (see the
  `CUR_FY` pattern in test_lifecycle.py).
- Frontend: vitest, node environment, stub `fetch` with `vi.stubGlobal`.

## Useful context

- Demo story by design: prior year = loss year, current year = turnaround (+69.2% revenue)
  → R006 anomalies always exist after seeding. Files in `seed/`, seeder in
  `backend/scripts/seed_demo.py`.
- Month-end clamping in `domain/deadlines.py::add_months` is deliberate (Feb-30 class of
  bug) — keep it and its test.
- `ops/smoke.sh` exercises the full lifecycle over HTTP against any deployment.
- Telemetry: metrics on `/metrics` are ALWAYS on; traces/OTLP logs only when
  `OTEL_ENABLED=true` (compose `--profile obs` ships collector/Tempo/Loki/Prometheus/
  Alertmanager/Grafana). Journey hooks live in `app/infra/telemetry/` + service call sites.
- The on-call responder (`oncall-agent/`) is deterministic by design — alertname →
  runbook → allow-listed command → verify → report in `ops/incidents/`. Drill:
  `./ops/alert-drill.sh [--simulate]`.
- Commit style: conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`).
