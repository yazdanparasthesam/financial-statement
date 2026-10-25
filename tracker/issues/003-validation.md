---
title: "Deterministic validation engine (R001–R009) + submit gate"
labels: [backend,quality]
milestone: "M2 — Backend"
state: closed
agent: "Arena Agent"
---

## Goal
Rule engine that must PASS before a filing can be submitted; each rule reports id/severity/message.

## Acceptance criteria
- [x] Rules R001–R009 implemented (balance identity, PL/BS articulation, cash-flow reconciliation, ratio sanity, required mappings…)
- [x] Submit with failing rules → 422 with rule details (never 500)
- [x] `POST /api/filings/{id}/validate` returns per-rule results; metrics counter per outcome
- [x] Integration tests cover pass + fail + gate

## Agent evidence log
- **Arena Agent** — wrote rule catalog in product-spec, implemented engine, tests.
- Verified: `pytest tests/integration -q` (gate tests green), smoke `validate` check.
