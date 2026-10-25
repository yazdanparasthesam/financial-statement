# Financial Statement (صورت مالی) — AI-Assisted Financial Statements & Tax Filing Platform

**Financial Statement** helps accountants and small companies turn a raw
trial balance into statutory financial statements, validate them against filing rules, get
AI-drafted explanations and notes, and run a proper **submit → review → accept** workflow with a
full audit trail — instead of juggling spreadsheets and email.

> Built for the [DataTalksClub AI Dev Tools Zoomcamp 2026](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp) final project.
> English UI, Iranian statutory context (اظهارنامه مالیاتی / صورت‌های مالی).

---

## The problem

Every Iranian company must prepare annual financial statements — profit & loss
(صورت سود و زیان), balance sheet (صورت وضعیت مالی), and explanatory notes — and file its tax
declaration with the Iranian National Tax Administration within **4 months of fiscal year-end**
(Art. 95 of the Direct Taxes Act; statutory formats published by the INTA).

In practice this happens in spreadsheets:

- mapping a trial balance to the statutory layout is manual and error-prone;
- balance checks (debits = credits, assets = liabilities + equity) are eyeballed, not enforced;
- large year-over-year movements go unexplained until an auditor asks;
- notes to the accounts are written from scratch every year;
- the hand-off between preparer and reviewer has no trail — no statuses, no comments, no history;
- deadlines slip.

**Financial Statement** makes the deterministic parts *enforced* (generation, validation, workflow gates,
deadline tracking) and the linguistic parts *assisted* (anomaly explanations, notes drafts,
mapping suggestions, a grounded filing assistant) — with every AI call logged and every number
computed by code, never by a model.

## What the system does

| Module | Capability |
|---|---|
| **Preparation** | Upload trial balance (CSV/XLSX) → auto-map accounts to statutory categories → generate P&L + Balance Sheet + **Cash Flow (indirect method)** — all versioned → compute **10 financial ratios**, each with its auditable formula → run **8 deterministic validation rules** → year-over-year anomaly detection |
| **AI assist** | **LangChain + LangGraph agents**: notes drafted by a *self-criticism* loop (draft → critique → bounded revise), a *ReAct* chat assistant over read-only filing tools, a *ReWOO* audit memo (plan → execute tools → solve), plus anomaly explanations and mapping suggestions (human applies) — Gemini or deterministic mock provider |
| **Workflow** | Roles `preparer`/`reviewer`; lifecycle `draft → submitted → in_review → changes_requested ⇄ … → accepted / rejected`; line-anchored comments; submit/accept gates blocked by failing error-rules; complete audit trail |
| **Filing ops** | Statutory deadline computed per company fiscal calendar; filing checklist; PDF/XLSX exports of statements and checklist |

## Architecture

```
        Browser — React 18 + Vite + TypeScript + Tailwind + TanStack Query
        └── src/api/client.ts   ← ALL backend traffic (centralized, typed)
                        │  REST/JSON — contract: openapi.yaml (CI fails on drift)
        FastAPI backend (Python 3.12)
        ├── routers/    thin HTTP layer (auth, filings, TB, statements, validation, AI, workflow, exports)
        ├── services/   orchestration + AI call logging + audit trail
        ├── domain/     PURE logic: mapping · generator · cashflow · ratios · validators · workflow · deadlines
        └── infra/      IO: ingestion (CSV/XLSX) · AI providers + LangGraph graphs (Gemini ⇄ Mock) · exports
                        │
        SQLAlchemy 2 — SQLite (dev/test) ⇄ Postgres (compose/prod), env-driven
        Gemini API — LangChain provider behind LangGraph agent graphs;
        AI_PROVIDER=mock makes everything work without keys (same graphs, deterministic model)

        Telemetry — /metrics (Prometheus) + JSON logs + OTLP traces (opt-in), one trace id
        └── collector → Tempo/Loki/Prometheus → Grafana :3001 → Alertmanager → on-call agent
```

**Design law (see [AGENTS.md](AGENTS.md)):** *the model reasons, the system computes, the human
decides.* All arithmetic lives in `backend/app/domain/` (pure functions, unit-tested). The LLM
never produces a number that reaches a statement; it only explains, drafts, or suggests — and a
human applies every suggestion. Agent loops are bounded (config-capped critique rounds, a plan
of at most 8 tool calls) and agent tools are strictly **read-only** serializations of domain
output. Every LLM call is logged to the `ai_requests` table
([AI data policy](security/ai-data-policy.md)).

### Technologies

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query | SPA; centralized typed API client; component-level state via query cache |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 | Contract-first REST API; validation; ORM |
| Database | SQLite (dev/test) / PostgreSQL 16 (compose/prod) | Env-driven persistence; same code both environments |
| AI | LangChain + LangGraph; Google Gemini (`gemini-2.0-flash`) or deterministic `MockChatModel` | Self-criticism notes loop · ReAct assistant · ReWOO audit memo · explanations · mapping suggestions |
| Exports | openpyxl, fpdf2 | XLSX/PDF statements & checklist |
| Containers | Docker, docker compose, nginx | One-command full stack |
| CI/CD | GitHub Actions → Render deploy hooks | Tests + security scans gate deployment |
| Deploy | Render (web service + static site) + Neon Postgres | Public URLs (see [docs/deployment.md](docs/deployment.md)) |
| Observability | Prometheus, Grafana, Tempo, Loki, OTel Collector, Alertmanager | Metrics/traces/logs on one trace id; user-impact alerts wake the on-call agent ([docs/observability.md](docs/observability.md)) |

## Quickstart (one command)

```bash
git clone https://github.com/<your-user>/financial-statement.git && cd financial-statement
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs (Swagger): http://localhost:8000/docs
- Health: `curl -i http://localhost:8000/healthz`

Seed the demo story (two fiscal years, YoY anomalies, drafted note):

```bash
pip install httpx   # once, on your host
python backend/scripts/seed_demo.py http://localhost:8000
```

Demo logins after seeding: `preparer@fsapp.dev` / `reviewer@fsapp.dev` — password `financial-statement-demo-123`.

With the full observability stack (Grafana :3001, Prometheus :9090, Tempo, Loki, Alertmanager):

```bash
OTEL_ENABLED=true docker compose --profile obs up --build -d
# The on-call responder starts inside Compose and is reached at localhost:8090.
./ops/alert-drill.sh                # stop backend → alert → responder fixes it → report
```

### Without Docker (local dev)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env            # defaults: SQLite + mock AI — runs with zero keys
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev                        # http://localhost:3000, proxies /api → :8000
```

## Tests

```bash
# backend — unit (pure domain) + integration (API + DB), clearly separated
cd backend && pip install -r requirements-dev.txt
python -m pytest tests/unit            # no DB, no HTTP
python -m pytest tests/integration     # full workflows incl. the contract-drift gate
python -m pytest                       # everything

# frontend — core logic (api client, workflow mirror, validation summary, formatting)
cd frontend && npm install
npm test
npm run build                          # type-check + production build

# on-call responder agent (allowlist, cooldown, escalation, incident reports)
python -m pytest oncall-agent/tests -q

# end-to-end smoke against a running stack (28 checks incl. /metrics)
bash ops/smoke.sh http://localhost:8000
```

Details: [docs/testing.md](docs/testing.md).

## The demo story (5 minutes)

1. Register as **preparer**; create a company (FY end month = 3, the Iranian year-end pattern).
2. Create filings for **two consecutive fiscal years**.
3. Prior year: upload `seed/trial_balance_prior_year.csv` → Generate → Validate.
4. Current year: upload `seed/trial_balance_clean.csv` → watch auto-mapping classify all 20
   accounts → **Generate statements**: P&L (net profit 60,000), Balance Sheet (assets = L+E =
   480,000), **Cash Flow** (indirect: operating 70,000 = 60,000 profit + 10,000 depreciation
   add-back, reconciliation gap 0) and **10 ratios** with formulas → **Validate**: R001–R005,
   R007 (cash-flow reconciliation) and R008 (liquidity) pass, **R006 flags year-over-year
   anomalies** (revenue +69.2%; net-profit swing −120,000 → +60,000).
5. **Statements tab** → cash-flow card (R007 badge) + ratios panel; **Anomalies tab** →
   *Explain (AI)*; **Notes tab** → *Draft with AI* (self-criticism loop) → edit → save final text.
6. Try `seed/trial_balance_unmapped.csv` on another filing: AI **suggests** categories; applying
   only one leg of the pair makes R002 **fail** → submission is **blocked** (422, names the rule)
   → map the second leg → clean → submit works. Deterministic gate, AI-assisted repair.
7. Register a second user with role **reviewer**: start review, generate the **AI audit memo**
   (ReWOO: plan → read-only tools → solve), comment on `pl:revenue`, request changes; preparer
   reopens, fixes, resubmits; reviewer **accepts**.
8. **Export tab**: checklist + P&L/Balance Sheet as PDF and XLSX.

Without any API key the AI runs in deterministic **mock mode** (`AI_PROVIDER=mock`); set
`AI_PROVIDER=gemini` + `GEMINI_API_KEY` for live responses. Same endpoints, same logging.

## Repository map

```
├── frontend/            React SPA (src/api centralized client, vitest tests)
├── backend/             FastAPI (app/{routers,services,domain,infra}, tests/{unit,integration})
├── openapi.yaml         THE API contract — regenerated via `make openapi`, drift fails CI
├── docker-compose.yml   db + backend + frontend, one command
├── product-spec.md      personas, journeys, functional spec, rule table, glossary
├── AGENTS.md            instructions for coding agents working on this repo
├── seed/                demo trial balances (clean, prior-year, unbalanced, unmapped)
├── docs/                architecture · ai-workflow · testing · deployment · operations
│                        observability · agent-team · course-submission-runbook · agent-extension-pack · permissions
├── security/            audit brief · AI data policy · agent security · telemetry policy
│                        credentials handling · scan artifacts (runs/)
├── observability/       otel-collector · prometheus (+rules) · alertmanager · tempo · loki
│                        grafana provisioning (datasources + golden-journey dashboard)
├── oncall-agent/        responder agent (webhook :8090) · runbooks.yaml · tests · example report
├── tracker/             GitHub-Issues source of truth (14 prepared issues) · import.sh
├── evidence/            submission evidence index + success-only screenshot slots
├── ops/                 smoke.sh · alert-drill.sh · diagnostics.sh · runbooks/ · incidents/
├── agent-capabilities/  reusable workflows + prompt library
├── agent-hooks/         guardrails (tool-use guard, pre-commit secret scan)
├── mcp-server/          read-only MCP server exposing filing tools to coding agents
├── custom-agent/        "validation-auditor" subagent definition
└── .github/workflows/   ci.yml · deploy.yml (dev auto / prod manual) · rollback.yml
```

## AI-assisted development

This project was built AI-first and documented as such: task decomposition, prompt log,
context files (AGENTS.md, product-spec.md, openapi.yaml), manual review checkpoints, and
verification evidence live in **[docs/ai-workflow.md](docs/ai-workflow.md)**. The agent
extension pack (MCP server, hooks, subagent, capabilities) is documented in
**[docs/agent-extension-pack.md](docs/agent-extension-pack.md)** with its permission model in
**[docs/permissions.md](docs/permissions.md)**.

## Observability, alerting & on-call

The golden journey (upload → generate → validate → submit) is instrumented with **metrics,
traces and structured JSON logs sharing one trace id** — no customer data or credentials in
any signal ([security/telemetry-policy.md](security/telemetry-policy.md)). Four **user-impact
alerts** (backend down, 5xx on the submit flow, p95 latency, AI failures) route through
Alertmanager to the **on-call responder agent**, which wakes up, runs an allow-listed
runbook command, verifies recovery and writes an incident report to `ops/incidents/`.
Full guide + drill instructions: [docs/observability.md](docs/observability.md) ·
[oncall-agent/README.md](oncall-agent/README.md). The agent team and its handoff process:
[docs/agent-team.md](docs/agent-team.md); the public task tracker lives in GitHub Issues,
generated from [tracker/](tracker/).

## Security & hardening

Deterministic scans (semgrep, bandit, pip-audit, trivy, gitleaks) run in CI; artifacts are
committed under `security/runs/`. Read: [security/audit-brief.md](security/audit-brief.md) ·
[security/ai-data-policy.md](security/ai-data-policy.md) ·
[security/agent-security.md](security/agent-security.md) ·
[security/credentials-handling.md](security/credentials-handling.md).

## Evidence & submission runbook

Owner-side screenshots are indexed in [evidence/README.md](evidence/README.md) (successful
frames only). The complete step-by-step path—public repo/issues, Docker verification,
observability/alert drill, Render dev/prod, CI/CD, evidence, and mandatory peer reviews—is
in [docs/course-submission-runbook.md](docs/course-submission-runbook.md).

## Deployment — owner setup pending

**The repository currently contains the deploy/CD configuration, but public services have not
been created from this workspace.** Deployment URLs and live workflow evidence must be added
by the owner following [docs/deployment.md](docs/deployment.md).

- Dev backend/frontend: Render services + Neon dev database — URLs pending owner setup
- Production backend/frontend: separate Render services + Neon production database — URLs pending
- CI/CD: GitHub Actions workflows prepared (auto dev after green CI; manually approved prod;
  rollback workflow). Deploy hooks/secrets and green hosted runs still need owner configuration.

## Project rubric guide (for reviewers)

Official final-project criteria → where each one is satisfied:

| # | Criterion | Where to look |
|---|---|---|
| 1 | Problem & functionality described | README §The problem / §What the system does + [product-spec.md](product-spec.md) |
| 2 | Spec + public task tracker with acceptance criteria | [product-spec.md](product-spec.md) · GitHub Issues (prepared under [tracker/](tracker/); publish/import and attach issue URLs before claiming top band) |
| 3 | Agent team & how it works together | [docs/agent-team.md](docs/agent-team.md) (roster, process diagram, handoff contracts) |
| 4 | AGENTS.md → modular docs | [AGENTS.md](AGENTS.md) + `docs/*` (architecture, ai-workflow, testing, deployment, operations, observability, permissions) |
| 5 | Full-stack E2E, one-command local run | README §Quickstart (`docker compose up --build`) + §The demo story |
| 6 | Unit + integration tests, single command | `make test` (backend pytest incl. on-call engine) · `cd frontend && npm test` · [docs/testing.md](docs/testing.md) |
| 7 | Full system incl. DB via compose | [docker-compose.yml](docker-compose.yml) (db+backend+frontend; `--profile obs` adds the telemetry stack) |
| 8 | Deployed / deployment demo | README §Deployment + [docs/deployment.md](docs/deployment.md) (public URLs and successful smoke runs pending owner setup) |
| 9 | CI tests + CD (dev auto, prod manual) + rollback | [.github/workflows/](.github/workflows/): ci.yml · deploy.yml (workflow_run → dev; dispatch + `environment: production` → prod) · rollback.yml |
| 10 | Journey instrumented: metrics+traces+logs, one trace id, no PII, viewable | [docs/observability.md](docs/observability.md) · Grafana :3001 golden-journey dashboard · [security/telemetry-policy.md](security/telemetry-policy.md) · `backend/tests/unit/test_telemetry.py` |
| 11 | Alert on user impact | `observability/prometheus/rules/user-impact.yaml` (4 rules) + Alertmanager routing |
| 12 | On-call agent wakes & fixes | [oncall-agent/](oncall-agent/) + `./ops/alert-drill.sh` → incident reports in `ops/incidents/` |

## License

MIT © 2026 — see [LICENSE](LICENSE).
