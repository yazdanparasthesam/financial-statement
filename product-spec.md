# Financial Statement — Product Specification

Version 0.1 · English UI, Iranian statutory context · companion to [README.md](README.md)

## 1. Problem statement

Iranian companies must, every fiscal year:

1. prepare statutory financial statements (P&L — صورت سود و زیان, balance sheet —
   صورت وضعیت مالی, notes — یادداشت‌های توضیحی) in the format published by the Iranian
   National Tax Administration (INTA);
2. file the tax declaration (اظهارنامه مالیاتی) within **4 months of fiscal year-end**
   (Art. 95, Direct Taxes Act — for the common March year-end this lands in July);
3. survive review: internal (senior accountant) and external (auditor/tax officer) questions
   about variances, mappings, and supporting documents.

Today this is spreadsheet work: manual mapping, eyeballed balance checks, notes written from
scratch, review over email, deadlines tracked in someone's head. Errors surface late — at
submission time or during audit — when they are expensive.

## 2. Product vision

Make the **deterministic parts enforced** and the **linguistic parts assisted**:

- The system computes every figure (pure, tested domain code) and refuses to let broken
  statements advance (submit/accept gates).
- The AI explains, drafts, and suggests — never computes — and a human approves every
  suggestion before it affects data.
- Every action and every AI call leaves an audit record.

## 3. Personas

| Persona | Role in system | Goals |
|---|---|---|
| **Pari, preparer** (accountant at an SME / accounting firm) | `preparer` | Turn the client's trial balance into valid statutory statements fast; clear validation; write defensible notes; submit before the deadline |
| **Reza, reviewer** (senior accountant / audit manager) | `reviewer` | See every filing across companies; interrogate variances; leave anchored comments; accept only clean filings |

## 4. Core journeys

### J1 — Prepare a filing (preparer)
create/select company → create filing (fiscal year) → upload trial balance (CSV/XLSX) →
review auto-mapping, fix or request AI suggestions for unmapped accounts → generate
statements → run validation → resolve errors, read warnings → ask AI to explain YoY
anomalies → draft + finalize notes → watch checklist complete → **submit**.

### J2 — Review a filing (reviewer)
open submitted filing → read statements + validation report + anomaly explanations →
comment (optionally anchored to a statement line) → **request changes** or **accept**.
Accept is gated: failing error-level rules block it.

### J3 — Fix and resubmit (preparer)
filing returns `changes_requested` → reopen to draft → re-upload/re-map/regenerate →
re-validate → resubmit. Full history preserved in `review_events` + `audit_log`.

## 5. Functional requirements

### Module A — Preparation
| ID | Requirement |
|---|---|
| A1 | Upload trial balance as CSV or XLSX; tolerant header detection (code/account, name/description, debit/deb, credit/cred); clear errors naming the missing column |
| A2 | Auto-map accounts to the 11 statutory categories by code-prefix chart (11/12/21/22/3/4/5/6/7/8/82) with keyword fallback |
| A3 | Manual re-mapping per account; AI mapping suggestions for unmapped accounts (suggestion ≠ application; human applies) |
| A4 | Generate versioned P&L and Balance Sheet from mapped accounts; equity includes current-year profit from the P&L; when a prior-year balance sheet exists, also generate the versioned **Cash Flow statement** (indirect method, kind `cf`) |
| A5 | Validation rules (deterministic): **R001** debits = credits (error) · **R002** assets = liabilities + equity (error) · **R003** all accounts mapped (warning) · **R004** revenue present (error) · **R005** equity positive (warning) · **R006** YoY movement vs prior-year statements > threshold (warning, creates anomalies) · **R007** cash-flow reconciliation — indirect-method net change must equal the balance-sheet cash movement, tolerance 1.0 (warning; info-skip when no cf statement) · **R008** short-term liquidity — current ratio < 1 warns (info when no current liabilities) |
| A6 | AI explanations for anomalies; AI drafts for notes sections; human finalizes note text |
| A7 | Grounded chat assistant scoped to one filing; identifiers redacted before leaving the server |
| A8 | Deadline = fiscal period end + configurable months (default 4); days-remaining surfaced everywhere |
| A9 | Filing checklist (8 items) computed from real state |
| A10 | Exports: P&L and Balance Sheet as PDF + XLSX; checklist PDF; authenticated downloads (cash flow is view-only in v1) |
| A11 | Financial ratios computed deterministically, each carrying its formula string and an interpretation: current, quick, debt-to-equity, gross/operating/net margin, ROE, ROA, asset turnover, EBITDA — `GET /api/filings/{id}/ratios` |
| A12 | Every statement figure the UI shows is reproducible from the mapped trial balance by pure functions in `backend/app/domain/` (see docs/architecture.md §Formula reference) |

### Module B — Submission & review workflow
| ID | Requirement |
|---|---|
| B1 | Roles: `preparer`, `reviewer` (JWT, RBAC enforced server-side) |
| B2 | Lifecycle: `draft → submitted → in_review → {changes_requested → draft …} → accepted | rejected` |
| B3 | Transition table enforced by a pure state machine; role checked per action; every transition recorded with actor, from/to, optional comment |
| B4 | Gates: **submit** and **accept** require a validation run with zero failing *error*-level rules and generated statements |
| B5 | Editable only in `draft`/`changes_requested` (uploads, mapping, regeneration locked otherwise) |
| B6 | Comments with optional anchor (e.g. `pl:revenue`), resolve flag |
| B7 | Reviewers read all filings; preparers only their own companies' |
| B8 | Global `audit_log` for state-changing actions |

### AI requirements
| ID | Requirement |
|---|---|
| C1 | LangChain provider abstraction: `AI_PROVIDER=gemini|mock`; the mock is a deterministic LangChain chat model, so identical LangGraph code runs offline (tests, CI, key-less demos) |
| C2 | The AI never computes figures shown in statements/validation — only prose over given numbers |
| C3 | Every call logged: kind, provider, model, prompt hash, status, latency (`ai_requests`) |
| C4 | Redaction: national IDs, economic codes, emails never sent to external models |
| C5 | Provider failure degrades gracefully (clear message; deterministic features unaffected) |
| C6 | Notes drafting runs a **self-criticism** LangGraph loop (draft → critique → revise → finalize), bounded by `AI_MAX_CRITIQUE_LOOPS` (default 2); the trace (steps + loops) is recorded in the audit event |
| C7 | The chat assistant is a **ReAct** agent (LangChain/LangGraph) over strictly read-only filing tools: statements summary, validation report, anomalies, checklist, deadline, ratios |
| C8 | `POST /api/filings/{id}/audit-memo` runs a **ReWOO** graph — planner emits a tool plan (≤ 8 steps, unknown tools dropped), executor runs the read-only tools, solver writes the memo; response includes memo + plan + observation count |

## 6. Non-functional requirements

- **Reproducible**: `docker compose up --build` → full stack; no manual steps.
- **Tested**: unit (pure domain), integration (API+DB workflows), contract (OpenAPI drift),
  frontend (core logic), E2E smoke script.
- **Portable data layer**: identical code on SQLite and Postgres via `DATABASE_URL`.
- **Observable ops**: `/healthz`, `/version`, `ops/diagnostics.sh`.
- **Secretless repo**: `.env.example` only; scanners in CI (gitleaks).

## 7. Non-goals (v1)

- No e-filing to the INTA portal itself (we prepare and gate; a human files).
- Cash flow uses the **indirect method only**; no direct-method statement, and no cf PDF/XLSX export in v1.
- No multi-currency, no consolidation, no Jalali calendar UI (deadlines use Gregorian dates;
  the FY-end-month setting covers the March year-end pattern).
- No billing/tenancy isolation beyond ownership + roles.

## 8. Glossary

| Persian | English | In Financial Statement |
|---|---|---|
| صورت مالی | financial statement | `statements` (pl / bs / cf) |
| صورت سود و زیان | profit & loss statement | kind `pl` |
| صورت وضعیت مالی | balance sheet | kind `bs` |
| صورت جریان وجوه نقد | cash-flow statement | kind `cf` (indirect method) |
| اظهارنامه مالیاتی | tax declaration | the `filing` lifecycle |
| تراز آزمایشی | trial balance | uploaded CSV/XLSX → `tb_accounts` |
| یادداشت‌های توضیحی | explanatory notes | `statement_notes` |
| سال مالی | fiscal year | `filings.fiscal_year` |
| کد اقتصادی | economic code | company field (redacted from AI calls) |
