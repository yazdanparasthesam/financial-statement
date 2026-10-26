# Testing

## Pyramid

| Level | Where | Runs against | Current count |
|---|---|---|---|
| Unit (domain + AI graphs + telemetry) | `backend/tests/unit/` | pure functions, graphs, telemetry helpers/PII guard — no DB, no HTTP | 64 |
| Integration (API+DB) | `backend/tests/integration/` | real FastAPI app via TestClient + SQLite (local) / Postgres 16 (CI) | 10 |
| Contract | `backend/tests/integration/test_contract.py` | committed `openapi.yaml` ⇄ live app spec, both directions | 2 |
| Frontend core logic | `frontend/src/**/__tests__/` | vitest (node env): api client, workflow mirror, validation summary, formatters | 27 |
| E2E smoke | `ops/smoke.sh` | any running deployment over HTTP (curl) | 1 script |

Separation is physical (different directories) and by pytest markers (`unit`,
`integration`) — criterion 9 asks for exactly this.

## Running

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/unit           # fast, pure
python -m pytest tests/integration    # API + DB
python -m pytest                      # everything
ruff check app tests scripts          # lint gate

cd frontend
npm install
npm test                              # vitest run
npm run build                         # tsc --noEmit + vite build

bash ops/smoke.sh http://localhost:8000   # against compose stack or prod
```

## What integration covers (the lifecycle test)

register/login → company → two filings (deadline math asserted) → prior-year upload →
generate → validate → current-year upload (20 accounts auto-mapped, totals asserted) →
generate (net profit 60,000; identity 480,000; cash-flow operating 70,000 with gap 0;
current ratio 4.6429, EBITDA 92,000) → validate (R001–R005 + R007/R008 pass, R006 flags
+69.2% revenue anomaly) → AI explain (mock, deterministic) → note draft+finalize → chat →
audit memo (ReWOO plan/observations asserted) →
checklist state → RBAC (reviewer reads, cannot upload: 403) → submit (warning-only failures
don't block) → TB locked after submit (422) → review loop (start_review → comment →
request_changes → reopen → resubmit → accept; preparer cannot accept: 403) → full event
sequence asserted → exports (xlsx content-type, `%PDF` magic bytes, bad extension 400) →
reviewer global scoping.

Plus dedicated tests: unbalanced TB blocks submit naming R001 · unmapped accounts get AI
suggestions → applying one leg fails R002 → gate blocks (422) → applying the second leg →
clean → submit succeeds · auth edge cases (409 duplicate, 401 bad creds, 422 short password,
400 bad role, token enforcement) · contract drift both directions · graph-level unit tests
for the three agent patterns (critique-JSON parsing incl. fail-open, bounded revise loops
via a StrictCritic double, ReWOO plan filtering + gate wording, ReAct mock invocation).

## Conventions (also in AGENTS.md)

- Test env is configured in `tests/conftest.py` **before** app import (settings are cached);
  AI is always `mock`; emails use `@example.com` (the email validator rejects `.local`).
- Never hardcode today-relative dates — derive fiscal years from `date.today()` (`CUR_FY`).
- Frontend tests stub `fetch` with `vi.stubGlobal`; no network, no DOM required.
- New rule ⇒ new R-id + unit test + product-spec row. New endpoint ⇒ `make openapi`.


## On-call responder tests (separate executable)

`python -m pytest oncall-agent/tests -q` runs 10 offline engine tests (exact command grammar,
webhook parsing, cooldown, verify/escalate paths, incident reports). CI runs them in the
`oncall-agent` job; `make test` runs both backend and responder suites (79 backend tests + 10 responder tests).
