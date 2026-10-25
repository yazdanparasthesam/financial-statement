---
title: "User-impact alerts: 4 rules + Alertmanager → responder webhook"
labels: [observability,alerting]
milestone: "M7 — Ship"
state: closed
agent: "Arena Agent"
---

## Goal
Rubric criterion 11: at least one alert on user impact, wired to a responder.

## Acceptance criteria
- [x] `user-impact.yaml`: BackendDown (critical), SubmitFlowErrors (5xx on submit/review, critical), GoldenJourneyLatencyHigh (warning), AIUnavailableSpike (warning)
- [x] Annotations carry user impact + runbook pointer
- [x] Alertmanager groups by alertname, 10s group_wait, webhook → host on-call agent, send_resolved
- [x] Prometheus-rule alerting chosen over Grafana-provisioned alerts (ADR 7 — FAQ #440 trap)

## Agent evidence log
- **Arena Agent** — wrote rules from the ACTUAL metric labels verified live (status="5xx" grouping).
- Verified: promtool-style YAML validation + drill script.
