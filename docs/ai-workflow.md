# AI-Assisted Development Workflow

How this project was built with AI tools, and how every AI contribution was reviewed and
verified. (Rubric criterion 2 — prompts/delegation, context files, manual review, verification.)

## Tooling

| Tool | Role |
|---|---|
| Arena.ai Agent Mode (coding agent) | Architecture, implementation, test authoring, debugging, docs — working in a sandbox workspace with shell access |
| GitHub Copilot CLI (host machine) | Interactive checks, live-run assistance during milestone verification (M4+) |
| Google Gemini 2.0 Flash | The product's runtime AI — a LangChain provider behind three LangGraph agent patterns (self-criticism, ReAct, ReWOO) with a deterministic mock chat model |

## Context files (what the agent reads before touching code)

1. `AGENTS.md` — non-negotiable laws (AI never computes; contract frozen; suggestions ≠
   mutations; call logging; secrets; gates) + layer rules + definition of done.
2. `product-spec.md` — personas, journeys, FR/R-rule tables, non-goals, glossary.
3. `openapi.yaml` — the API contract (generated, drift-gated).
4. `docs/architecture.md` — layers, data model, ADR-lite decisions.

These files are *inputs to the agent*, not afterthoughts: each milestone starts by updating
them, then implementing against them.

## Delegation pattern (per milestone)

```
human: goal + constraints (scope decision, e.g. "hybrid prepare+review", "Render", "Gemini")
agent: plan → implement in small batches → self-review (lint/type/test gates) → report evidence
human: run it live (docker compose / uvicorn / npm), screenshot results, accept or reject
agent: document episode (what broke, why, fix) in IMPLEMENTATION_SUMMARY.md
```

## Manual review & verification checkpoints (what already happened)

Every batch passed through these gates **before** being handed over:

- `ruff check` clean (committed `ruff.toml`; FastAPI `Depends` idiom whitelisted explicitly);
- backend `pytest`: 79 tests — unit (pure domain + AI providers/graphs) + integration (API+DB)
  + contract drift;
- frontend `vitest`: 27 tests on the api client + pure libs; `tsc --noEmit` + production build;
- seed-data arithmetic hand-checked (trial balances balance; anomaly percentages recomputed);
- tests caught six real defects during the build — each is logged with cause and fix in
  `IMPLEMENTATION_SUMMARY.md` §"Bugs the tests caught" (latin-1 PDF crash, half-mapped pair
  breaking the balance-sheet identity + the 422 gate proving it, `.local` TLD rejection,
  calendar-dependent assertions, missing "cred" header alias, contract-test bug).

## Prompt log

Representative prompts/delegations from the build (full history lives in the conversation
log and commit messages):

1. *"Scope: hybrid — preparation engine PLUS submission/review workflow; React+Vite+TS;
   Render; Gemini key available."* → produced `PROJECT-PLAN.md` → milestone plan.
2. *"Build M0–M2 now, in the style of deedeepratiwi/ai-data-cleaning-assistant: FastAPI +
   agents layer + prompt files + CI/deploy workflows + comprehensive README."* → this repo.
3. System-prompt content for the runtime AI (`backend/app/infra/ai/prompts.py`): hard rules
   "never compute or invent numbers", "never echo credentials/national IDs", auditor-friendly
   concision — mirrored for humans in `agent-capabilities/prompts/`.
4. *"Rebuild the AI layer on LangChain/LangGraph with self-criticism, ReAct and ReWOO
   patterns; keep the mock deterministic and every loop bounded."* → `infra/ai/providers.py`,
   `infra/ai/graphs.py`, the audit-memo endpoint, and 14 unit tests over providers + graphs
   (including loop-bounding and plan-filtering behaviour).

## Runtime AI governance (the product's own AI usage)

- LangChain provider abstraction + deterministic mock (`AI_PROVIDER=mock` ⇒ zero external
  calls); the mock is a real `BaseChatModel`, so the LangGraph code path is identical;
- three agent patterns, all bounded and read-only: **self-criticism** notes loop
  (`AI_MAX_CRITIQUE_LOOPS`, default 2), **ReAct** assistant (six read-only filing tools),
  **ReWOO** audit memo (plan ≤ 8 tool calls, unknown tools dropped);
- every call logged to `ai_requests` (kind, provider, model, prompt hash, status, latency);
- identifier redaction before prompt construction;
- human-in-the-loop: mapping suggestions require an explicit PATCH; note drafts require an
  explicit finalize; AI text never mutates statements, validations, or workflow state.

See `security/ai-data-policy.md` for the data contract, `docs/permissions.md` for the agent
extension pack's permission model.

## Appended per milestone (living log)

- **M0–M2 (this commit):** full-stack core built and verified as above.
- **M4:** live Gemini verification (one real call per AI kind, logged) — pending.
- **M7:** Neon Postgres branch + app API smoke passed. FastAPI Cloud `fs-dev-api` is Live at `https://fs-dev-api.fastapicloud.dev`; its GitHub source remains disconnected, Neon/JWT secrets are configured, and CI-gated Deploy #7 passed. Vercel frontend and production deployment remain pending.
- **M2.5 (formula engine + LangChain/LangGraph agents):** cash-flow statement (indirect
  method) + rules R007/R008 + 10 ratios with formula strings; AI layer rebuilt on
  LangChain/LangGraph — self-criticism notes loop, ReAct assistant, ReWOO audit memo
  (new endpoint); final local verification: backend 79, frontend 27, live smoke 28/28.
- **M8:** agent-pack demo transcripts (MCP session, hook guard blocking a dangerous command,
  validation-auditor run) — pending.
- **M11–M12 (local/hosted evidence verified; public deployment pending):** Prometheus/OTel/Grafana/Loki/Tempo
  configs, privacy-redacted traces, user-impact alerts, in-Compose responder, alert drill,
  public issue importer, dev/prod CD and rollback workflow. Owner-side local Compose, telemetry,
  alert/remediation, and hosted CI evidence are verified; public FastAPI Cloud/Vercel deployment and live CD
  remain pending. Provider credentials are stored in provider/GitHub secret stores and never in the sandbox.
