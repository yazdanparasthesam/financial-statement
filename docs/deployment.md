# Deployment — FastAPI Cloud + Vercel + Neon (in progress)

## Current state (2026-10-28)

The selected no-card route is **FastAPI Cloud for the API, Vercel for the frontend, and Neon for PostgreSQL**. Dev services are live. Production FastAPI Cloud `fs-prod-api` and Vercel `fs-prod-web` are created but not deployed. Neon production settings and rotated password are owner-confirmed; API connectivity has not been tested. GitHub `production` approval protection is configured. Vercel `fs-prod-web` is confirmed Git-unconnected in Settings, with CLI-verified root `frontend`, preset `Other`, install `npm ci`, build `npm run build`, and output `dist`; its Production `VITE_API_URL` and `https://fs-prod-web.vercel.app` domain are set, and FastAPI Cloud CORS allows that origin. Project ID: `prj_kd9wWSZ1WLYM8IClegKwMTRQyl44`; Vercel team ID is `team_HpUqb7I7uxT4kKNDP7yMLOQg`. GitHub production has the project-scoped `VERCEL_PROD_TOKEN`, currently non-expiring (rotation deferred by user; required before production dispatch). The manual API+frontend production path is pushed on `main` at `efb3596`; the CI/dev chain is green, but the production job was not dispatched. No production deployment has occurred.

- FastAPI Cloud `fs-dev-api` is **Live** at `https://fs-dev-api.fastapicloud.dev` (region `us-east-1`). CI-gated API Deploy runs #8 and #9 succeeded after the CORS origin was saved. `/healthz` and the API lifecycle smoke are green.
- `DATABASE_URL` and `JWT_SECRET` are configured as FastAPI Cloud secrets for the dev API. `AI_PROVIDER` remains the code default `mock`. `CORS_ORIGINS=https://fs-dev-web.vercel.app` was saved and applied by a later gated API deployment.
- GitHub repository secrets `FASTAPI_CLOUD_TOKEN` and `FASTAPI_CLOUD_APP_ID` are configured; values are not documented. Neon `dev` is a child of `production`; the successful API lifecycle smoke confirms the dev database path works.
- Vercel Hobby project `fs-dev-web` is live at `https://fs-dev-web.vercel.app` and remains Git-unconnected, preserving the CI gate. The local `frontend/` folder is linked to team `hesam2`; Vercel CLI created an ignored `.env.local` containing a local `VERCEL_OIDC_TOKEN`—never commit or share it. Settings are root `frontend`, install `npm ci`, build `npm run build`, output `dist`; Framework Preset is `Other`. `frontend/vercel.json` supplies the Vite SPA rewrite for deep links.
- GitHub Actions secret names `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, and `VERCEL_TOKEN` are present; values are hidden. The project-scoped Vercel token was set to expire 2026-11-26. `VITE_API_URL` remains masked; successful browser registration, filing creation, upload, statement generation, and validation functionally confirm the frontend/API connection without disclosing the value.
- Latest confirmed dev commit `efb3596` has CI #32, API Deploy #32, and Deploy Vercel Web #25 green. The Vercel workflow checks out the triggering API deployment's exact SHA, builds/deploys the dev web project, then checks `/` and `/login`. Independent public checks returned HTTP 200 for the frontend root, `/login`, and API `/healthz`. Browser testing reached the Review page with a clear mock audit memo, but the filing remains Draft; Submit for review is still pending. Evidence #91 captures the current green dev chain for `efb3596`; the earlier #31/#24 sequence is historical. Deploy #32 shows the production job skipped on the automatic `workflow_run` event (evidence 93).
- The initial npm registry DNS failures are resolved; see [troubleshooting episode 014](../ops/troubleshooting/014-vercel-cli-npm-registry-dns.md). Earlier FastAPI Cloud runtime failures were resolved; see [episode 013](../ops/troubleshooting/013-fastapi-cloud-healthz-404.md). Do not deploy from the FastAPI Cloud dashboard or connect Vercel Git integration.

## Deployment guardrails

1. **CI must pass before dev deploys.** Dev deployment is triggered only by the successful `CI` workflow completing on `main`, and the deployment job checks out that exact tested SHA.
2. **Production is manual.** The production job uses the protected GitHub `production` environment with required reviewers and verifies CI succeeded for the selected SHA.
3. **No native FastAPI Cloud GitHub auto-deploy.** The repo source is disconnected. Use the FastAPI Cloud deploy token from GitHub Actions only.
4. **No credentials in Git, chat, screenshots, or this document.** Keep database URL, JWT secret, and deploy tokens in secret stores. Do not use `Import .env` in the provider dashboard.
5. **No card entry.** Stop if any provider asks for payment details.

## 1. Neon PostgreSQL

The existing `financial-statement` Neon project has `production` and `dev` branches; `dev` is a child of `production`. The temporary `neon-smoke` branch expires and is not for a long-lived deployment.

- The application reads `DATABASE_URL` and normalizes generic `postgresql://` / `postgres://` strings for its psycopg 3 SQLAlchemy driver.
- Use the **pooled** `dev` connection for the FastAPI Cloud app. Confirm the hostname contains `-pooler` and the Connect modal is set to branch `dev`, database `neondb`, role `neondb_owner`, and pooling on. Neon recommends pooled connections for serverless request workloads ([connection-string docs](https://neon.com/docs/connect/connect-from-any-app)).
- The dev role password was reset after a connection string was exposed in an earlier screenshot. The user saved the new pooled connection string privately and configured it as the encrypted `DATABASE_URL` secret; successful CI-gated API lifecycle smoke has since verified the dev database connection.
- If the earlier exposed URL may have referenced `production`, rotate that branch's role password separately before creating the production app. Use distinct dev/prod secrets.
- Do not run the end-to-end smoke against production. Local `ops/neon-e2e-smoke.py` previously passed against temporary Neon test data and cleans up its temporary user.

Official Neon references: [role password reset](https://neon.com/docs/manage/roles), [pooled connections](https://neon.com/docs/connect/connection-pooling).

## 2. FastAPI Cloud API

### Dev app

- App name: `fs-dev-api`.
- Repository: `yazdanparasthesam/financial-statement`; **disconnected** from the app's Source/Repository settings to prevent un-gated pushes.
- Application root: `backend` (`requirements.txt`, `app/main.py`, and `Dockerfile` are in this directory).
- The dev app is **Live** at `https://fs-dev-api.fastapicloud.dev`; GitHub's successful gated deploy runs #8 and #9 are recorded in the runbook/evidence index. Do not use the dashboard's manual deployment control.
- App secrets: `DATABASE_URL`, `JWT_SECRET`, and `CORS_ORIGINS=https://fs-dev-web.vercel.app`. The app uses the deterministic `mock` AI provider for the course demo.
- The FastAPI Cloud deploy-token value is stored outside the repository. GitHub repository Actions secret names are `FASTAPI_CLOUD_TOKEN` and `FASTAPI_CLOUD_APP_ID`; values are not documented.

The default hostname is derived from the app name, e.g. `fs-dev-api.fastapicloud.dev`. Confirm the actual URL on the app after deployment; if it differs, set GitHub Actions variable `FS_DEV_BACKEND_URL` before the next deployment. FastAPI Cloud documents app-name-to-hostname conversion [here](https://fastapicloud.com/docs/other-resources/how-app-urls-are-generated/).

### Production app (created, not deployed)

FastAPI Cloud `fs-prod-api` has been created and the dashboard showed **Not deployed**. The Settings screenshot confirms application root `backend` and source/repository integration **Not Connected**. Keep it that way; the current environment-variable screenshot does not prove database connectivity. Neon `production` is the default persistent branch; the owner-provided Connect capture selects database `neondb`, role `neondb_owner`, pooling enabled, password masked; credential rotation is not confirmed. If the prior production password may have been exposed, rotate it on the `production` branch before use. This is settings evidence only—the app has not connected to this branch. `DATABASE_URL` and a distinct `JWT_SECRET` have been saved as masked FastAPI Cloud secrets; this does not yet verify database connectivity. FastAPI Cloud `CORS_ORIGINS=https://fs-prod-web.vercel.app` is now set. The protected GitHub `production` environment contains `FASTAPI_CLOUD_PROD_TOKEN` and `FASTAPI_CLOUD_PROD_APP_ID`; duplicate repository-level copies have been removed. Retain dev token/app-ID at repository scope. Never paste credential values into chat or screenshots.

## 3. GitHub Actions deployment gate

`.github/workflows/ci.yml` runs backend unit/integration tests, frontend tests/build, on-call tests, and security scans. `.github/workflows/deploy.yml` is the controlled deploy workflow:

- **Dev:** `workflow_run` listens for the `CI` workflow. It deploys only when CI concludes `success`, the branch is `main`, and the run belongs to this repository. It checks out `workflow_run.head_sha` so the deployed code is exactly what CI tested. It uses `uvx` with `fastapi[standard]` and `FASTAPI_CLOUD_TOKEN` / `FASTAPI_CLOUD_APP_ID`, then checks `/healthz` and runs `ops/smoke.sh` against the dev URL.
- **Production:** `deploy.yml` on `main` at `efb3596` has a manual `workflow_dispatch` path attached to GitHub Environment `production` (required reviewer). It verifies the selected full SHA is on `main` and has successful CI, deploys/health-checks the API, then pulls/builds/deploys and verifies the production frontend. This API-first order can leave a partial API-only rollout if later Vercel preparation fails; the user deferred reordering until final preflight. The Vercel team ID `team_HpUqb7I7uxT4kKNDP7yMLOQg` and project ID `prj_kd9wWSZ1WLYM8IClegKwMTRQyl44` are saved in GitHub environment `production` as `VERCEL_PROD_ORG_ID` and `VERCEL_PROD_PROJECT_ID`. The ordinary CI-triggered Deploy #32 run shows `deploy-prod` skipped; the manual production path has not been dispatched. Rotate the non-expiring Vercel project token before any production dispatch. No production deployment has occurred.
- **Dev web:** `.github/workflows/deploy-vercel.yml` listens for successful completion of the API `Deploy` workflow, filters to its trusted `main`-branch CI-triggered run, and checks out `workflow_run.head_sha`. It pulls the Vercel project's Production-target settings, builds, deploys prebuilt output, and verifies `/` plus `/login`.
- Do not use FastAPI Cloud's direct GitHub integration or connect the Vercel project to Git; either would bypass these gates.

The provider-adapted workflows are present and the latest CI/API/Vercel chain is green. Preserve the existing CI and deploy gates; do not overwrite `.github/workflows/deploy.yml` with a platform-generated push-to-deploy template.

## 4. Vercel frontend

- Dev project `fs-dev-web` is a Vercel Hobby project, Git-unconnected, and live at `https://fs-dev-web.vercel.app`. Keep it unconnected so Vercel cannot bypass the GitHub CI gate. The local `frontend/` directory is linked to team `hesam2`; its ignored `.env.local` contains a local OIDC token and must not be committed or shared.
- Build settings: root `frontend`, install `npm ci`, build `npm run build`, output `dist` (Framework Preset `Other`). `frontend/vercel.json` rewrites SPA paths to `/index.html`, allowing direct navigation to `/login`.
- Vercel project `VITE_API_URL` is set for the dev project's Production target and remains masked. Successful live browser registration and API-backed data operations functionally confirm the configured dev frontend/API connection; do not reveal the value in evidence.
- GitHub repository secrets `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, and `VERCEL_TOKEN` are configured. The token is project-scoped to `fs-dev-web`, expires 2026-11-26, and its value must remain private.
- `.github/workflows/deploy-vercel.yml` performs `vercel pull`, `vercel build --prod`, and `vercel deploy --prebuilt --prod` only after successful CI-gated API deployment. Its post-deploy smoke checks `/` and `/login`. Latest Deploy Vercel Web #3 is green.
- Production frontend `fs-prod-web` is configured but undeployed; Settings explicitly confirms Git is disconnected. CLI confirms root `frontend`, preset `Other`, install `npm ci`, build `npm run build`, output `dist`; Production `VITE_API_URL=https://fs-prod-api.fastapicloud.dev` and assigned domain `https://fs-prod-web.vercel.app` are set. FastAPI Cloud CORS matches the domain. Project ID is `prj_kd9wWSZ1WLYM8IClegKwMTRQyl44`. The Vercel project-scoped token is stored in GitHub `production` but never expires; rotate before production dispatch. Verify the existing `VERCEL_PROD_ORG_ID` and `VERCEL_PROD_PROJECT_ID` production environment secrets remain configured. Do not enter payment details if a provider requests a card.

The API currently defaults to mock AI; no `GEMINI_API_KEY` is needed for this deterministic course demo.

## 5. Verification and evidence

The latest confirmed dev CI/API/Vercel chain is green for `efb3596`: CI #32, API Deploy #32, Deploy Vercel Web #25. These are dev pipeline runs, not production deployment. Public HTTP checks returned 200 for the dev frontend `/`, frontend `/login`, and API `/healthz`; the API lifecycle smoke also passed during its gated dev deploy. The owner tested registration/login, company and filing creation, a balanced 20-account upload, generated statements, 8/8 validation, mock notes, and an audit memo in the browser.

The Export checklist shows that the Revenue note is not yet finalized, and the filing has not been submitted. First open **Notes (AI)** and click **Save final text**; verify the notes item is checked on Export. Then return to **Review**, click **Submit for review**, and capture the resulting status. Preserve redacted evidence only; do not expose account email, National ID, passwords, or provider secrets. Production reviewer protection is configured, the projects, environment secrets, and frontend/API settings are configured, but the apps remain undeployed and API-to-Neon connectivity is unverified. The Vercel token rotation and workflow ordering review are deferred until final preflight; do not dispatch production until completed and explicitly approved.
