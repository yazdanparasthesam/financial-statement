# Deployment — FastAPI Cloud + Vercel + Neon (in progress)

## Current state (2026-10-27)

The selected no-card route is **FastAPI Cloud for the API, Vercel for the frontend, and Neon for PostgreSQL**. The dev API and dev frontend are live; production resources, approval gate, and in-browser end-to-end validation remain pending.

- FastAPI Cloud `fs-dev-api` is **Live** at `https://fs-dev-api.fastapicloud.dev` (region `us-east-1`). CI-gated API Deploy runs #8 and #9 succeeded after the CORS origin was saved. `/healthz` and the API lifecycle smoke are green.
- `DATABASE_URL` and `JWT_SECRET` are configured as FastAPI Cloud secrets for the dev API. `AI_PROVIDER` remains the code default `mock`. `CORS_ORIGINS=https://fs-dev-web.vercel.app` was saved and applied by a later gated API deployment.
- GitHub repository secrets `FASTAPI_CLOUD_TOKEN` and `FASTAPI_CLOUD_APP_ID` are configured; values are not documented. Neon `dev` is a child of `production`; the successful API lifecycle smoke confirms the dev database path works.
- Vercel Hobby project `fs-dev-web` is live at `https://fs-dev-web.vercel.app` and remains Git-unconnected, preserving the CI gate. The local `frontend/` folder is linked to team `hesam2`; Vercel CLI created an ignored `.env.local` containing a local `VERCEL_OIDC_TOKEN`—never commit or share it. Settings are root `frontend`, install `npm ci`, build `npm run build`, output `dist`; Framework Preset is `Other`. `frontend/vercel.json` supplies the Vite SPA rewrite for deep links.
- GitHub Actions secret names `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, and `VERCEL_TOKEN` are present; values are hidden. The project-scoped Vercel token was set to expire 2026-11-26. `VITE_API_URL` remains masked; successful browser registration, filing creation, upload, statement generation, and validation functionally confirm the frontend/API connection without disclosing the value.
- Latest CI #10 for commit `10f7387`, API Deploy #10, and Deploy Vercel Web #3 are green. The Vercel workflow checks out the triggering API deployment's exact SHA, builds/deploys the dev web project, then checks `/` and `/login`. Independent public checks returned HTTP 200 for the frontend root, `/login`, and API `/healthz`. Browser testing reached the Review page with a clear mock audit memo, but the filing remains Draft; Submit for review is still pending. Evidence #57 captures the latest green workflow sequence.
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

### Production app (not created yet)

Create `fs-prod-api` as a separate FastAPI Cloud app with application root `backend`, using **Empty/manual deployment** (not GitHub Repo). Configure the production Neon connection and a distinct JWT secret before deployment. Add deploy-token and app-ID secrets as `FASTAPI_CLOUD_PROD_TOKEN` and `FASTAPI_CLOUD_PROD_APP_ID` in the protected GitHub `production` environment. Do not create it until the production Neon credential has been checked/rotated as needed.

## 3. GitHub Actions deployment gate

`.github/workflows/ci.yml` runs backend unit/integration tests, frontend tests/build, on-call tests, and security scans. `.github/workflows/deploy.yml` is the controlled deploy workflow:

- **Dev:** `workflow_run` listens for the `CI` workflow. It deploys only when CI concludes `success`, the branch is `main`, and the run belongs to this repository. It checks out `workflow_run.head_sha` so the deployed code is exactly what CI tested. It uses `uvx` with `fastapi[standard]` and `FASTAPI_CLOUD_TOKEN` / `FASTAPI_CLOUD_APP_ID`, then checks `/healthz` and runs `ops/smoke.sh` against the dev URL.
- **Production:** `workflow_dispatch` only; attached to GitHub Environment `production` (required reviewers). The selected full commit SHA must have a successful CI run before deployment. Production has separate token/app-ID secrets and a post-deploy smoke. Production resources and reviewer protection remain pending.
- **Dev web:** `.github/workflows/deploy-vercel.yml` listens for successful completion of the API `Deploy` workflow, filters to its trusted `main`-branch CI-triggered run, and checks out `workflow_run.head_sha`. It pulls the Vercel project's Production-target settings, builds, deploys prebuilt output, and verifies `/` plus `/login`.
- Do not use FastAPI Cloud's direct GitHub integration or connect the Vercel project to Git; either would bypass these gates.

The provider-adapted workflows are present and the latest CI/API/Vercel chain is green. Preserve the existing CI and deploy gates; do not overwrite `.github/workflows/deploy.yml` with a platform-generated push-to-deploy template.

## 4. Vercel frontend

- Dev project `fs-dev-web` is a Vercel Hobby project, Git-unconnected, and live at `https://fs-dev-web.vercel.app`. Keep it unconnected so Vercel cannot bypass the GitHub CI gate. The local `frontend/` directory is linked to team `hesam2`; its ignored `.env.local` contains a local OIDC token and must not be committed or shared.
- Build settings: root `frontend`, install `npm ci`, build `npm run build`, output `dist` (Framework Preset `Other`). `frontend/vercel.json` rewrites SPA paths to `/index.html`, allowing direct navigation to `/login`.
- Vercel project `VITE_API_URL` is set for the dev project's Production target and remains masked. Successful live browser registration and API-backed data operations functionally confirm the configured dev frontend/API connection; do not reveal the value in evidence.
- GitHub repository secrets `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, and `VERCEL_TOKEN` are configured. The token is project-scoped to `fs-dev-web`, expires 2026-11-26, and its value must remain private.
- `.github/workflows/deploy-vercel.yml` performs `vercel pull`, `vercel build --prod`, and `vercel deploy --prebuilt --prod` only after successful CI-gated API deployment. Its post-deploy smoke checks `/` and `/login`. Latest Deploy Vercel Web #3 is green.
- Production frontend `fs-prod-web` has not been created. After the production API and protected approval environment are ready, create it separately, set its own `VITE_API_URL`, and add a distinct exact production CORS origin. Do not enter payment details if a provider requests a card.

The API currently defaults to mock AI; no `GEMINI_API_KEY` is needed for this deterministic course demo.

## 5. Verification and evidence

The latest CI/API/Vercel chain is green: CI #10 (`10f7387`), API Deploy #10, Deploy Vercel Web #3. Public HTTP checks returned 200 for the dev frontend `/`, frontend `/login`, and API `/healthz`; the API lifecycle smoke also passed during its gated deploy. The owner tested registration/login, company and filing creation, a balanced 20-account upload, generated statements, 8/8 validation, mock notes, and an audit memo in the browser.

The Export checklist shows that the Revenue note is not yet finalized, and the filing has not been submitted. First open **Notes (AI)** and click **Save final text**; verify the notes item is checked on Export. Then return to **Review**, click **Submit for review**, and capture the resulting status. Preserve redacted evidence only; do not expose account email, National ID, passwords, or provider secrets. Production resources and manual approval protection remain pending; do not mark the overall deployment task complete until those are configured and verified.
