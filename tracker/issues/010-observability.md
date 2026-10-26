---
title: "Observability: metrics + traces + structured logs sharing one trace id"
labels: [observability]
milestone: "M7 — Ship"
state: closed
agent: "Arena Agent"
---

## Goal
Rubric criterion 10: golden journey instrumented; signals stored and viewable in Grafana; zero PII.

## Acceptance criteria
- [x] `app/infra/telemetry/` package: JsonFormatter logs, OTLP tracing (opt-in `OTEL_ENABLED`), 6 `fs_*` business metrics + exemplars
- [x] Middleware logs route TEMPLATE + status + duration; uvicorn folded into JSON; /metrics hidden from OpenAPI
- [x] Compose `--profile obs`: collector → Tempo (traces) + Loki (logs, derived trace_id field) + Prometheus (scrape, rules) + Grafana :3001 provisioned dashboard
- [x] One trace id joins log line ↔ span ↔ exemplar
- [x] No customer data / credentials in any signal (whitelisted extras; security/telemetry-policy.md)
- [x] Unit tests: formatter whitelist, severity map, metrics move, opt-in gating, native log trace linkage, raw URL redaction

## Agent evidence log
- **Arena Agent** — full implementation + live verification (journey run against :8793, metrics deltas checked, 10 JSON log lines captured).
- Defects found & fixed in-session: missing status label (used `http_requests_total` grouped 5xx), non-JSON uvicorn lines.
- Verified: `pytest tests/unit/test_telemetry.py` (10), `curl :8000/metrics | grep fs_`.


## Verified completion (2026-10-26)
- Compose obs profile: Prometheus backend target UP; Grafana dashboard populated metrics.
- Loki returned 142 structured backend request logs with trace IDs.
- Grafana TraceID derived link opened a matching Tempo trace with spans.
- Evidence: `evidence/04-grafana-golden-journey.png`, `evidence/05-loki-json-trace-ids.png`, `evidence/05-trace-log-correlation.png`.
