# Troubleshooting episode 007 — Grafana dashboard loads but business panels show zero

**Date:** 2026-10-26\
**Status:** resolved; Grafana panels populated, Loki returned structured logs with trace IDs, and the TraceID link opened the matching Tempo trace with spans.\
**Evidence handling:** no screenshot retained; the current dashboard view is not a successful metric-population frame.

## Observed

- Grafana home and the provisioned `Financial Statement — golden journey` dashboard load.
- Prometheus reports the `financial-statement-backend` target 1/1 UP.
- The owner reran the telemetry-enabled HTTP smoke: 28/28 passed and `/metrics` contained metric names.
- Dashboard request-rate legends show routes but last values are zero; business panels (statements, failed validations, submits, accepts) also show zero. The 5xx panel's “No data” alone may be normal if there were no 5xx responses.
- No dashboard screenshot is retained as evidence until values are verified.

## Diagnostic next step

Read-only checks show `OTEL_ENABLED=true`; backend exposition has nonzero counters (statements: PL 2, BS 2, cash flow 1; workflow/AI/HTTP counters are also populated). Prometheus reports the target UP, but `sum(increase(fs_statements_generated_total[1h]))` and `sum(increase(http_requests_total[15m]))` return 0. This is consistent with Prometheus first observing already-incremented counters before the smoke traffic, so the `increase()` window has no observed delta yet. The owner reran the 28-check smoke and waited 25 seconds. Prometheus then reported `sum(increase(fs_statements_generated_total[1h])) = 5.1085` and `sum(increase(http_requests_total[15m])) = 26.5663`; the Grafana dashboard displayed request rate, p95 latency, journey p95, statements (5), failed validations (1), submits (1), accepts (1), and AI calls. The 5xx panel’s “No data” is expected when there are no 5xx responses. Loki Explore query `{service_name="financial-statement-backend"}` returned 142 JSON backend request logs with non-empty `trace_id` fields. Evidence: `evidence/05-loki-query-results.png` and `evidence/05-loki-json-trace-ids.png`. The derived TraceID link opened the matching trace in Tempo; metrics/logs/traces are verified. Proceed to the real alert drill. Success captures of the dashboard and counter delta are `evidence/04-observability-counter-delta.png`, `evidence/04-grafana-golden-journey.png`, and `evidence/04-grafana-golden-journey-ai.png`. Do not run the intentional alert drill until dashboard/log/trace verification is complete.
