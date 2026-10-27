# Runbook: BackendDown

**Alert:** `up{job="financial-statement-backend"} == 0` for 30s (critical)
**User impact:** every journey is broken — upload, generate, validate, review, export.

## Automated response (on-call agent)
The responder agent (oncall-agent/) receives the Alertmanager webhook and runs:
1. `docker compose ps backend` (diagnose) and `docker compose logs --tail 40 backend`
2. `docker compose restart backend` (action — allow-listed)
3. Verifies `http://localhost:8000/healthz` (12 attempts × 5s)
4. Writes an incident report to `ops/incidents/` — remediated or escalated.

## Manual escalation checklist
1. `docker compose ps` — is `db` healthy? Backend cannot start without Postgres.
2. `docker compose logs backend --tail 100` — look for the JSON log with `"level": "ERROR"`.
3. Common causes:
   - **DB down / wrong DATABASE_URL** → `docker compose up -d db`, wait for healthy, restart backend.
   - **Missing secret** (JWT_SECRET) → check `.env`; redeploy.
   - **Bad migration / model change** → roll back to the last good image (`ops/runbooks/rollback.md`).
4. Cloud (FastAPI Cloud): inspect deployment/runtime logs; a failed rollout keeps the last successful deployment live. For a bad successful API deploy, run the GitHub Actions **Rollback** workflow with a previously CI-green SHA; production waits for approval.
5. After recovery, confirm in Grafana (:3001) that `up == 1` and the 5xx panel is flat.
