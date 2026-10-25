---
title: "Frontend golden journey: React+Vite+TS+Tailwind+TanStack Query"
labels: [frontend]
milestone: "M5 — Frontend"
state: closed
agent: "Arena Agent (implementation + review)"
---

## Goal
Full UI for the journey: auth, upload+mapping, statements viewer, validation panel, workflow actions, AI assist, exports.

## Acceptance criteria
- [x] Vite + TS + Tailwind + TanStack Query; role-aware UI (preparer vs reviewer)
- [x] Statements rendered from API (no duplicated formula logic in FE — single source of truth)
- [x] Vitest core-logic suite green in CI; production build < 300 kB
- [x] nginx serves build + proxies /api (compose single-command)

## Agent evidence log
- **Arena Agent** — implemented the frontend components; Vitest/build output is the verification evidence.
- **Arena Agent** — review: query-key discipline, error-state handling, extracted pure logic for tests.
- Verified: `npm test` (27), `npm run build` (250 kB).
