---
title: "Trial-balance upload + statutory P&L / BS / cash-flow / ratios engine"
labels: [backend,domain]
milestone: "M2 — Backend"
state: closed
agent: "Arena Agent (implementation + review)"
---

## Goal
CSV/XLSX upload → column mapping → generate profit-loss, balance-sheet, cash-flow (indirect), financial ratios; English statutory layout.

## Acceptance criteria
- [x] Upload accepts CSV/XLSX; debit==credit enforced; half-mapped files rejected with R002 (422 by design)
- [x] Full P&L chain (revenue → COGS → gross → operating → net), BS identity A=L+E, indirect cash flow, ratio pack
- [x] Seed FY2026 TB (909,000 balanced) → PL net 60,000; CF net 70,000; current ratio 4.6429
- [x] `GET /api/filings/{id}/statements/{pl|bs|cf|ratios}` + PDF/XLSX export endpoints
- [x] Unit tests for every formula family

## Agent evidence log
- **Arena Agent** — implemented the domain modules; source files and tests are the verification evidence.
- **Arena Agent** — review pass: fixed rounding policy, ordered P&L chain; added cash-flow reconciliation test.
- Verified: `make test-unit` (green), `bash ops/smoke.sh` upload→generate→export checks.
