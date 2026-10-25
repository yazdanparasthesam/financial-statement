# Runbook: Deploy

Full platform steps live in `docs/deployment.md`. Operator short form:

1. Confirm `main` CI is green (tests + scans): GitHub → Actions → latest CI run.
2. Deploy fires automatically via `deploy.yml` (Render deploy hooks) — watch Render →
   service → Events for the new deploy.
3. Verify: `bash ops/smoke.sh https://<backend>` and open the frontend URL.
4. Save evidence: `bash ops/diagnostics.sh https://<backend> https://<frontend> | tee ops/runs/$(date +%F)-prod-diagnosis.txt`
5. If anything fails → `rollback.md`.
