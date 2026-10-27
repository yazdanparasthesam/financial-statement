# Runbook: Deploy

Full provider setup lives in `docs/deployment.md`. Operator short form:

1. Confirm the pushed commit's **CI** run is green (backend, frontend, responder, security).
2. After CI completes successfully on `main`, the `deploy.yml` dev job deploys the exact tested SHA to FastAPI Cloud. Watch GitHub Actions → **Deploy** and the FastAPI Cloud app's Deployments/Logs.
3. Verify `GET /healthz`, then run `bash ops/smoke.sh https://<confirmed-dev-api-host>` and open the Vercel dev frontend.
4. Save successful, redacted evidence and diagnostics: `bash ops/diagnostics.sh https://<api> | tee ops/runs/$(date +%F)-dev-diagnosis.txt`.
5. Production is manual: dispatch Deploy with `prod`, choose a CI-green SHA, then approve the protected `production` environment. If anything fails, follow `rollback.md`.
