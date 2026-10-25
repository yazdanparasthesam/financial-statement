# Observability — metrics, traces, logs on one trace id

The golden user journey (**upload trial balance → generate statements → validate → submit**)
is instrumented end to end. All three signals share the W3C **trace id**, so a slow submit in
Grafana is one click away from its spans (Tempo) and its JSON log lines (Loki).

```
                         ┌────────────────────────── backend ──────────────────────────┐
 user journey ─────────► │ FastAPI + RequestLogMiddleware + FastAPIInstrumentor         │
                         │   metrics  → GET /metrics (Prometheus format, exemplars)     │
                         │   traces   → OTLP/gRPC ┐   (only when OTEL_ENABLED=true)     │
                         │   logs     → stdout JSON + OTLP/gRPC ┘                       │
                         └───────────────────────────┬──────────────────────────────────┘
                                                     │
        Prometheus (:9090) ◄── scrape /metrics       ▼
             │  rules: user-impact.yaml      OTel Collector (:4317/4318)
             ▼                                  │            │
        Alertmanager (:9093) ── webhook ──►  Tempo (:3200)  Loki (:3100)
             │                                  └─────┬──────┘
             ▼                                        ▼
        on-call responder agent (Compose :8090)      Grafana (:3001)
        runbook → fix → verify → ops/incidents/   dashboards + trace↔log links
```

## 1. Metrics (always on — no env needed)

Exposed at `GET /metrics` (hidden from the OpenAPI schema).

| metric | labels | meaning |
|---|---|---|
| `fs_statements_generated_total` | kind=pl/bs/cf | statements produced |
| `fs_validation_runs_total` | outcome=passed/failed | validation runs (submit gate) |
| `fs_workflow_transitions_total` | action, to_status | draft→submitted→…→accepted |
| `fs_ai_requests_total` | kind, provider, status=ok/error | AI calls incl. failures |
| `fs_ai_request_duration_seconds` | kind | AI latency histogram |
| `fs_journey_step_duration_seconds` | step=upload/generate/validate/submit | golden-journey steps |
| `http_requests_total` | handler, method, status=2xx/4xx/5xx | every API request |
| `http_request_duration_seconds` | handler, method | request latency histogram |

The `fs_journey_step_*` and `http_request_duration_*` histograms attach **exemplars**: when
tracing is on, Grafana plots a clickable marker on each bucket that jumps straight to the
exemplar trace.

## 2. Logs (always JSON, one line per request + app events)

```json
{"ts": "2026-10-18T05:47:15", "level": "INFO", "logger": "fs.http",
 "message": "http_request", "method": "POST",
 "route": "/api/filings/{filing_id}/submit", "status": 200, "duration_ms": 12.4,
 "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"}
```

- `route` is the FastAPI **template**, never a raw path — ids stay out of log labels.
- `trace_id` appears whenever a span is active (i.e. when `OTEL_ENABLED=true`).
- uvicorn's own loggers are folded into the same JSON handler; the access log is
  disabled (the middleware is the single source).
- **Privacy:** the formatter only emits a fixed whitelist of extras
  (`method, route, status, duration_ms, step, rule_id`). No emails, no national ids,
  no financial figures, no credentials — ever. Trace instrumentation overwrites concrete
  URL paths and query strings with `[REDACTED]`; only FastAPI route templates remain. See `security/telemetry-policy.md`.

## 3. Traces (opt-in)

Set `OTEL_ENABLED=true` (plus `OTEL_EXPORTER_OTLP_ENDPOINT`, default
`http://otel-collector:4317` in compose). FastAPIInstrumentor spans every request;
the pipeline adds a span per journey step; AI calls get child spans. Unset ⇒ zero
exporters, zero overhead beyond the in-process metrics.

## 4. Running the stack

```bash
# app + full observability stack (one command, everything in compose):
OTEL_ENABLED=true docker compose --profile obs up --build -d

Grafana      http://localhost:3001   (admin/admin; anonymous access on for local demo)
Prometheus   http://localhost:9090   (targets, rules, alert states)
Alertmanager http://localhost:9093   (active alerts)
Tempo/Loki   internal (queried through Grafana datasources)
```

The provisioned dashboard **“Financial Statement — golden journey”** shows: request rate by
route, 5xx rate, p95 latency, per-step journey p95, business counters (generated / failed
validation / submits / accepts), AI call health. The Loki datasource has a derived field:
every log line with `trace_id` renders a **TraceID** link into Tempo.

App-only mode (`docker compose up`) is unchanged — the obs services live behind the
`obs` profile, and `OTEL_ENABLED` defaults to `false` there.

## 5. Alerts (user impact, not host vitals)

Defined in `observability/prometheus/rules/user-impact.yaml`, routed by Alertmanager
(`group_wait: 10s`) as a webhook to the on-call agent.

| alert | fires when | severity | agent response |
|---|---|---|---|
| `BackendDown` | backend unscrapable 30s | critical | **restart + verify /healthz** |
| `SubmitFlowErrors` | 5xx on submit/review routes 1m | critical | **restart + verify** |
| `GoldenJourneyLatencyHigh` | p95 > 2s for 5m | warning | diagnose + escalate |
| `AIUnavailableSpike` | AI error rate sustained | warning | diagnose + escalate |

Alerting is done with Prometheus rules + Alertmanager (not Grafana-provisioned alerts) —
see ADR-lite #7 in `docs/architecture.md`: provisioned Grafana alerts silently stick
in “Normal” when the reduce/threshold expression refIds are misconfigured.

## 6. The drill

```bash
# Starts app + collector + Prometheus + Tempo + Loki + Grafana + Alertmanager + responder:
OTEL_ENABLED=true docker compose --profile obs up --build -d
./ops/alert-drill.sh            # full: really stops backend, responder restarts + verifies
./ops/alert-drill.sh --simulate # no real outage: synthetic payload to responder service
```

Expected: within ~60s the agent receives the webhook, runs the runbook
(`docker compose restart backend`), verifies `/healthz`, and writes an incident report to
`ops/incidents/`. Details: `oncall-agent/README.md`.
