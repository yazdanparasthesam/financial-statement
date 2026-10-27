# Architecture

## System context

```
┌─────────────────────┐  HTTPS/REST   ┌───────────────────────────┐
│ Browser SPA         │ ────────────► │ FastAPI Cloud API         │
│ Vercel static build │ ◄──────────── │ routers → services        │
│ React 18 + TypeScript│               │ → domain (pure) / infra   │
└─────────────────────┘               └─────────────┬───────┬─────┘
                                                    │       │
                                      ┌─────────────▼──┐ ┌──▼─────────────┐
                                      │ Neon Postgres  │ │ Gemini API     │
                                      │ (SQLite local) │ │ (or Mock model)│
                                      └────────────────┘ └────────────────┘
```

All frontend API calls flow through **one** module (`frontend/src/api/client.ts`). Local Vite
uses its development server configuration; the app-only Compose deployment uses nginx.
For the selected split hosting route, the production build targets the FastAPI Cloud API through
`VITE_API_URL`, and FastAPI CORS is restricted to the exact Vercel origin. No browser code uses
hardcoded `localhost` in production builds.

## Backend layers (dependency direction is inward)

| Layer | Contents | Rules |
|---|---|---|
| `app/routers/` | auth, companies, filings, trial_balance, statements, validations, ai, workflow, exports, ops | HTTP only: parse → authorize (`deps.py`) → call service → shape response |
| `app/services/` | `pipeline.py` (generate/validate/checklist orchestration), `ai_service.py` (LangChain providers, LangGraph agent graphs, redaction, `ai_requests` logging), `audit.py` | Own transactions; the only layer that talks to both domain and infra |
| `app/domain/` | `mapping.py`, `generator.py`, `cashflow.py`, `ratios.py`, `validators.py`, `workflow.py`, `deadlines.py` | **Pure functions, zero IO, zero framework imports** — this is where every number is born |
| `app/infra/` | `ingestion.py` (CSV/XLSX), `ai/providers.py` + `ai/prompts.py` + `ai/graphs.py`, `exports.py` (PDF/XLSX) | Swappable adapters; failures raise typed errors |
| shared kernel | `config.py`, `db.py`, `models.py`, `schemas.py`, `security.py`, `deps.py` | Settings are env-driven (`pydantic-settings`) |

## Data model

`users ─< companies ─< filings ─< {trial_balances ─< tb_accounts, statements, validation_runs ─< validation_results, anomalies, statement_notes, review_events, review_comments}` plus global `ai_requests` (LLM call log) and `audit_log` (state-change journal). Details and column lists: `backend/app/models.py` (documented inline).

Key invariants enforced in code, not just docs:
- one trial balance per filing (re-upload replaces rows; statement **versions** keep history);
- statements are versioned (`version` increments per regeneration);
- equity in the balance sheet **includes current-year profit** from the P&L (generator);
- `filing.status` only changes through the state machine (`domain/workflow.py`);
- submit/accept require a validation run with zero failing **error**-severity rules.

## Design decisions (ADR-lite)

1. **Contract generated, drift-gated.** `openapi.yaml` is produced from the app
   (`make openapi`) and an integration test fails if file and app disagree in either
   direction. Rationale: the spec is graded as *the* contract; hand-maintained specs rot.
2. **AI as LangChain providers + LangGraph agent graphs, with a deterministic mock.**
   `AI_PROVIDER=gemini|mock`; the mock is a real LangChain `BaseChatModel`, so all three
   agent patterns (self-criticism notes loop, ReAct assistant, ReWOO audit memo) execute the
   identical graph code offline. Rationale: tests/CI/reviewers must work without keys, and
   the patterns stay verifiable — bounded loops, read-only tools, logged calls.
3. **SQLite ⇄ Postgres via `DATABASE_URL` only.** No environment-specific code. Tests run
   SQLite (fast), CI integration runs Postgres 16 service (real), compose/prod run Postgres.
   Schema management is `create_all` for v1; Alembic migrations land when the schema freezes
   (post-M7) — tracked, deliberate, documented.
4. **Deterministic gates, assisted repairs.** The workflow blocks submission on failing
   error-rules (server-side); AI helps a human *fix* the cause; a human re-runs validation.
   This is the course principle made literal: model reasons, system verifies.
5. **Redaction at the AI boundary.** `ai_service.redact()` strips national IDs, economic
   codes and emails before prompt construction; only hashes of prompts are stored.
6. **Static + API split for deployment.** Vercel static frontend + FastAPI Cloud API + Neon Postgres. Local Compose/nginx remains for one-command development and observability. The public route uses CI-gated deploy tokens; native default-branch auto-deploy is disabled to preserve the CI gate.
7. **Alerting via Prometheus rules + Alertmanager, not Grafana-provisioned alerts.**
   Provisioned Grafana alerts silently stick in *Normal* when the reduce/threshold
   expression refIds are misconfigured (`execErrState: OK` masks the evaluator error —
   a documented course FAQ trap). Prometheus rules are version-controlled next to the
   scrape config, testable with `promtool`, and Alertmanager owns routing/dedup and the
   webhook to the on-call agent.
8. **The on-call responder is deterministic, not an LLM.** It executes runbooks:
   alertname → allow-listed command → verify → incident report. An LLM in the
   remediation path would turn every alert into an unauditable improvisation; the
   exact command grammar (safe `docker compose ps|logs|restart backend`, stdout-only `echo`, `true`) caps the blast radius and every
   action is written to `ops/incidents/`. Warnings escalate instead of acting.
9. **Metrics are always on; tracing/OTLP logs are opt-in (`OTEL_ENABLED`).** A course
   project must start with one command on a small laptop — Prometheus scraping `/metrics`
   costs nothing, while span/log exporters only initialize when a collector exists.

## Sequence: the golden path

```
preparer: upload TB ─► parse+auto-map ─► generate v1 (pl+bs[+cf]) ─► validate (R001..R008)
             │                                 │
             │            anomalies ◄──────────┘ (R006, needs prior-year statements)
             ▼
        AI explain anomaly ─► ai_requests log ─► prose stored on anomaly
        AI draft note      ─► self-criticism loop (draft→critique→revise ≤2) ─► human edits
        AI audit memo      ─► ReWOO (plan → read-only tools → solve) ─► reviewer prose
             ▼
        submit ──gate──► reviewer: start_review ─► comment(pl:revenue) ─► request_changes
             ▲                                                              │
             └────────────── preparer: reopen ─► fix ─► re-validate ◄─────────┘
                                     ▼
                             submit ─► start_review ─► accept (gate re-checked)
                                     ▼
                        exports: pl.pdf / bs.xlsx / checklist.pdf
```

## Formula reference (the deterministic core)

Every number the product shows is produced by these formulas — pure functions in
`backend/app/domain/`, unit-tested, and mirrored in the UI (the ratios panel prints each
formula next to its value). The AI never computes any of them.

**P&L chain (`generator.py`):**

```text
gross_profit      = revenue − cogs
operating_profit  = gross_profit − operating_expenses
profit_before_tax = operating_profit + other_income − other_expenses
net_profit        = profit_before_tax − tax_expense
```

**Balance sheet (`generator.py`):**

```text
total_assets      = current_assets + non_current_assets        (contra accounts netted)
total_liabilities = current_liabilities + non_current_liabilities
total_equity      = equity + net_profit                        (current year, from the P&L)
rule R002         : total_assets = total_liabilities + total_equity   (error if not)
rule R001         : Σ trial-balance debits = Σ credits                  (error if not)
```

**Cash flow — indirect method (`cashflow.py`; requires a prior-year balance sheet):**

```text
operating          = net_profit + depreciation_addback − Δreceivables − Δinventory + Δpayables
investing          = −equipment_purchases      (Δ gross non-current assets, contra excluded)
financing          = Δnon_current_liabilities + Δshare_capital
net_change_in_cash = operating + investing + financing
rule R007          : |net_change_in_cash − (cash_end − cash_begin)| ≤ 1.0   (warning; info-skip w/o cf)
depreciation_addback = |accumulated_depreciation|current − |accumulated_depreciation|prior
```

**Ratios (`ratios.py`) — each row ships its formula string + interpretation to the API/UI:**

```text
current_ratio    = current_assets ÷ current_liabilities          (rule R008 warns when < 1)
quick_ratio      = (current_assets − inventory) ÷ current_liabilities
debt_to_equity   = total_liabilities ÷ total_equity
gross_margin     = gross_profit ÷ revenue × 100
operating_margin = operating_profit ÷ revenue × 100
net_margin       = net_profit ÷ revenue × 100
roe              = net_profit ÷ total_equity × 100
roa              = net_profit ÷ total_assets × 100
asset_turnover   = revenue ÷ total_assets
ebitda           = operating_profit + depreciation expense
```

Division by zero yields `null` ("n/a") instead of an error; percentage ratios are scaled ×100
and rounded to 2 dp at the API boundary (`scale_percentages`).

## AI agent graphs (LangChain + LangGraph)

Three patterns in `infra/ai/graphs.py`, all provider-agnostic (Gemini or the deterministic
mock) and all logged to `ai_requests`:

```text
1) Self-criticism — notes drafting            2) ReAct — assistant chat
   draft ─► critique ─┐                          human message ─► agent loop
      ▲               │ accept OR loops≥max         (langchain create_agent)
      └── revise ◄────┘                             ├─► read-only tools: statements,
   bound: AI_MAX_CRITIQUE_LOOPS (default 2)         │   validation, anomalies, checklist,
   finalize ─► note draft + step trace              │   deadline, ratios
                                                    └─► grounded answer

3) ReWOO — audit memo (POST /api/filings/{id}/audit-memo)
   planner ─► numbered tool plan ("1. #get_statements_summary …")
           ─► executor loop: one read-only tool per step (≤ max_steps=8,
              unknown tool names dropped, tool errors become observations)
           ─► solver ─► memo + plan + observation count
```

Invariants: tools are zero-arg closures over deterministic service reads (read-only by
construction — no write tool exists); loops are bounded by config, not by model goodwill;
any exception degrades to "[AI UNAVAILABLE]" prose — never a 500, never a state change.
