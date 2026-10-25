# Operations

## Health & version

- `GET /healthz` → `{"status":"ok"}` (liveness; Render health-check path).
- `GET /version` → `{app, version, ai_provider}` — confirms which build and AI mode is live
  without exposing internals.

## Diagnostics

```bash
bash ops/diagnostics.sh [BASE_URL]        # default http://localhost:8000
# → latency of /healthz & /version, AI mode, compose container states (if docker present),
#   DB port reachability. Tee into ops/runs/<date>-diagnosis.txt for the audit trail.
```

## Smoke (full lifecycle over HTTP)

```bash
bash ops/smoke.sh [BASE_URL]              # exercises register→upload→generate→validate→
                                          # submit→review→accept→exports with seed CSVs
```
Run after every deploy; output is the operational evidence for criterion 13.

## Logs

- **All logs are single-line JSON** (`ts, level, logger, message, trace_id?, method, route,
  status, duration_ms`) — the request middleware is the only access-log source
  (uvicorn's own access log is disabled, its loggers fold into the JSON handler).
- Compose: `docker compose logs -f backend`; with `--profile obs`, query them in Grafana
  → Explore → Loki: `{service_name="financial-statement-backend"} | json` — every line
  with `trace_id` renders a jump-to-trace link (Tempo).
- Render: service → Logs tab; free tier keeps 7 days.
- The app logs to stdout (12-factor); no log files inside containers.
- Privacy contract for every signal: `security/telemetry-policy.md`.

## Observability stack & on-call (compose `--profile obs`)

```bash
OTEL_ENABLED=true docker compose --profile obs up --build -d   # app + collector/Prom/Tempo/Loki/Grafana/AM
# responder service is started automatically by --profile obs (:8090)
./ops/alert-drill.sh            # full drill: stops backend → alert → agent fixes → report
./ops/alert-drill.sh --simulate # no docker: synthetic Alertmanager payload → same pipeline
```

Grafana :3001 (admin/admin) → “Financial Statement — golden journey” dashboard.
Alerts/rules: `observability/prometheus/rules/user-impact.yaml`; agent runbooks:
`oncall-agent/runbooks.yaml`; incident reports land in `ops/incidents/`.
Full guide: `docs/observability.md`.

## Data operations

- **Backup (Neon):** automated PITR on paid plans; manual: `pg_dump "$DATABASE_URL" -Fc -f
  backup.dump` (see `ops/runbooks/backup.md`).
- **Restore:** `pg_restore -d "$DATABASE_URL" --clean backup.dump`.
- **Compose dev data:** named volume `fs_pgdata`; `docker compose down -v` destroys it.

## Incident-ish situations

| Symptom | First check | Runbook |
|---|---|---|
| 502/slow first request on Render | free-tier cold start (~1 min) | wait, re-curl `/healthz` |
| `/version` shows `ai_provider: mock` in prod | `AI_PROVIDER`/`GEMINI_API_KEY` env | fix env → manual deploy |
| AI endpoints return "[AI UNAVAILABLE]" text | provider outage/key quota; deterministic features unaffected by design | check Render logs; `ai_requests.status='error'` rows confirm |
| Backend down in compose | `up == 0` in Prometheus → BackendDown alert → agent restarts + verifies | `ops/runbooks/backend-down.md` |
| Contract test red in CI | someone changed routes without `make openapi` | run `make openapi`, commit |
| Submit returns 422 naming R-ids | working as intended (gate) | fix data, re-validate |

Runbooks: `ops/runbooks/deploy.md` · `rollback.md` · `backup.md` · `backend-down.md` ·
`submit-flow-errors.md` · `high-latency.md` · `ai-unavailable.md` (the last four are
executed automatically — in allow-listed form — by `oncall-agent/`).
