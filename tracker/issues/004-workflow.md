---
title: "Submission/review workflow: states, roles, comments, versions, audit trail"
labels: [backend,workflow]
milestone: "M3 — Workflow"
state: closed
agent: "Arena Agent (implementation + review)"
---

## Goal
draft → submitted → in_review → changes_requested → accepted|rejected, with preparer/reviewer roles.

## Acceptance criteria
- [x] State machine rejects illegal transitions (409); every transition persisted to audit trail
- [x] Role enforcement: preparer submits, reviewer transitions (start_review/accept/reject/request_changes)
- [x] Comments on transitions; statement versioning per submit
- [x] Checklist endpoint aggregates progress

## Agent evidence log
- **Arena Agent** — implemented the workflow router and models; integration tests are the verification evidence.
- **Arena Agent** — review: added transition metrics hook, 409-vs-422 semantics, audit actor capture.
- Verified: integration workflow tests; smoke submit→start_review→accept.
