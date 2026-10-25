# Telemetry privacy policy — what leaves the process, and what never does

Applies to metrics (`/metrics`), traces (OTLP → Tempo) and logs (stdout JSON → Loki).
Rule of thumb: **signals describe the system, never the customer.**

## NEVER collected (hard guarantees in code)

| Category | Guarantee |
|---|---|
| Credentials (JWTs, API keys, passwords) | No header/cookie/token is ever logged; the log formatter whitelist has no such field; gitleaks + secret scanning in CI |
| Personal data (emails, national ids, phone numbers) | `JsonFormatter` emits ONLY whitelisted extras (`method, route, status, duration_ms, step, rule_id`) — arbitrary `extra=` fields are dropped, unit-tested (`test_json_formatter_whitelists_extras_only` and `test_trace_privacy_hook_redacts_raw_path_and_query`) |
| Financial figures / statement contents | No amount, account name, or trial-balance row appears in any metric label, log field or span attribute |
| User identifiers | No user id/email in labels; auth context stays inside the request, not in telemetry |
| Raw URL paths | Request logs use the FastAPI route **template** (`/api/filings/{filing_id}/submit`), so ids never become label values or log strings |
| Uploaded file content | Only the byte count and timing of the upload step are observed |

## What IS collected

- **Metrics:** counters/histograms of system events — statements generated (by kind),
  validation outcomes, workflow transitions (by action/status), AI calls (by kind/provider/status),
  journey-step durations, HTTP requests (by route template/method/status class).
  All label values come from fixed enumerations — bounded cardinality, no user data.
- **Traces** (only when `OTEL_ENABLED=true`): span names are route templates and step names;
  attributes are timing/status/kind — no request or response bodies.
- **Logs:** one JSON line per request (template, status, duration, trace_id) plus app events
  (startup, telemetry status, AI fallbacks). Exceptions include stack traces — code paths,
  not payloads.

## Exemplars

Prometheus exemplars attach a **trace id** (32 hex chars) to histogram samples. A trace id
is a random correlation handle — it identifies no person and reveals nothing by itself.

## Storage & access (local demo defaults)

| Store | Retention | Access |
|---|---|---|
| Prometheus TSDB | 15d default (compose volume) | localhost:9090 |
| Loki | 24h index/chunks on disk (compose volume) | via Grafana only |
| Tempo | 24h (`block_retention`) | via Grafana only |
| Grafana :3001 | — | admin/admin + anonymous **local-demo only**; disable anonymous auth in any shared deployment |

The observability UI ports (Grafana, Prometheus, Alertmanager, responder) bind to
127.0.0.1 only; Tempo, Loki and the collector are internal-only. In production, put Grafana
behind auth and drop the anonymous org role. The application ports remain available for the
local app demo.

## Change control

Any new metric/log field/span attribute must be reviewed against this table; the formatter
whitelist and the `fs_*` label sets are the enforcement points (see
`backend/app/infra/telemetry/` + its unit tests).
