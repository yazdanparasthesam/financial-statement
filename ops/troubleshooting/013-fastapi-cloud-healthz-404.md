# 013 — FastAPI Cloud runtime lacked the FastAPI CLI extra

**Date:** 2026-10-27  
**Area:** API deployment / runtime startup  
**Status:** **Resolved.** Commit `009f887` added `fastapi[standard]`; CI run #7 and gated Deploy run #7 passed. FastAPI Cloud shows `fs-dev-api` **Live** and its latest deployment **Ready** at `https://fs-dev-api.fastapicloud.dev` (region `us-east-1`). The green deployment job completed both the `/healthz` check and `ops/smoke.sh` lifecycle smoke.  
**Evidence policy:** Successful deployment screenshots are retained as [`evidence/39-github-fastapi-deploy-7-green.png`](../../evidence/39-github-fastapi-deploy-7-green.png) and [`evidence/40-fastapi-cloud-dev-deployment-live.png`](../../evidence/40-fastapi-cloud-dev-deployment-live.png). The failed-state dashboard/log screenshot is not retained; failure details remain in prose.

## Symptom and diagnosis

After commit `0f1854c` corrected the previous app-directory mismatch (see [episode 012](012-fastapi-cloud-github-auto-deploy-gate.md)), CI passed and the FastAPI Cloud CLI uploaded a deployment. The health check then received repeated HTTP 404 responses for `/healthz`, and the deployment was marked **Verification Failed**.

FastAPI Cloud runtime logs showed that the platform invoked `/app/.venv/bin/fastapi`, which repeatedly exited with:

> RuntimeError: To use the fastapi command, please install `fastapi[standard]`.

The app's `backend/requirements.txt` declared only `fastapi>=0.115`, omitting the optional extra that provides the FastAPI CLI required by the observed platform startup command. The 404s were a consequence of the app process failing to start, not a missing route or wrong hostname.

## Resolution

1. Changed the first line of `backend/requirements.txt` to `fastapi[standard]>=0.115`.
2. The owner committed the change to `main` as `009f887`.
3. CI run #7 passed, then the gated Deploy run #7 passed. FastAPI Cloud shows the API Live/Ready. The workflow only turns green after its health-check loop and `ops/smoke.sh` complete successfully.

No credential rotation or dashboard-side manual deployment was needed. Continue to keep production separate and manually gated; Vercel frontend deployment and production setup remain pending.
