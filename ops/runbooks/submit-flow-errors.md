# Runbook: SubmitFlowErrors

**Alert:** 5xx rate > 0 on `/api/filings/*/submit` or `/api/filings/*/review/transition` for 1m (critical)
**User impact:** users cannot submit filings or move them through review — the deadline-critical path (Art. 95, 4-month window) is blocked.

## Automated response (on-call agent)
Diagnose + `docker compose restart backend` + `/healthz` verification, same as BackendDown,
then an incident report in `ops/incidents/`. A restart clears crash-loops and stuck workers.

## Manual escalation checklist
1. Grafana (:3001) → golden-journey dashboard → "5xx rate" panel: which handler?
2. Loki explore: `{service_name="financial-statement-backend"} | json | status >= 500`
   — each line carries `trace_id`; click through to Tempo for the exact failing span.
3. Typical causes:
   - **Validation gate bug** (submit with failing rules must be 422, never 500) → reproduce with
     `ops/smoke.sh`, fix, redeploy.
   - **DB lock/connection exhaustion** → check `docker compose logs db`.
   - **Bad deploy** → `ops/runbooks/rollback.md`.
4. Verify the fix by re-running the smoke journey (submit → start_review → accept).
