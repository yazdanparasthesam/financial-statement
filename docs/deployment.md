# Deployment (Render + Neon) — prepared; owner-side setup pending

Topology: **Render static site** (frontend) + **Render web service** (backend, Docker) +
**Neon serverless Postgres** (`DATABASE_URL`). Dev and production each have their own
frontend/backend services (and preferably separate Neon branches/databases). Chosen for
free-tier durability: Render's own free Postgres expires after 90 days; Neon's free tier does not.

## 1. Database — Neon

Neon is the managed database provider. The AWS region is only where Neon runs the database; create and manage it in Neon Console. **No AWS account or AWS console setup is required.**

1. neon.tech → create or select project `financial-statement` (AWS eu-central-1 or us-east-1).
2. Authenticate the Neon CLI with `neon login` (or `npx --yes neon@latest login` when the CLI is not installed globally) and complete the browser authorization.
3. In the project root, link/configure the intended project branch with `neon init`; review the proposed changes using `neon config plan`, then use `neon deploy` to apply `neon.ts` and pull branch environment variables. The verified `production` plan had no changes and listed Postgres as the utilized service.
The generated `neon.ts` keeps Neon Auth disabled (the app already has JWT auth) and applies a seven-day TTL only to newly created non-default branches; production remains unchanged. Postgres is the only utilized service. The root npm manifest retains `@neon/config` and `@neon/env` and provides a root `npm run build` that builds the frontend.

The application uses SQLAlchemy 2 + psycopg 3 (`psycopg[binary]`). Keep this existing driver. Use the pooled app connection string as `DATABASE_URL`; use the direct `DATABASE_URL_UNPOOLED` only for migrations/admin tasks that need it. The backend loads `.env` / `.env.local` from the repository root (as well as the legacy `backend/.env`) and normalizes generic `postgresql://` or `postgres://` URLs to SQLAlchemy's `postgresql+psycopg://` form while preserving query options such as `sslmode=require`.

## 2. Backend — Render web service

1. New → Web Service → point at your `financial-statement` repo → **Runtime: Docker** (uses
   `backend/Dockerfile`; set *Root Directory* to `backend`).
2. Environment:
   - `DATABASE_URL` = Neon string (from step 1)
   - `JWT_SECRET` = output of `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `AI_PROVIDER` = `gemini` (or `mock` for a key-less demo instance)
   - `GEMINI_API_KEY` = your key (marked secret in Render)
   - `CORS_ORIGINS` = your frontend URL (explicit, not `*`)
3. Health check path: `/healthz`. Free tier sleeps after idle — first request ≈ 30–60 s
   cold start (documented in README).

## 3. Frontend — Render static site

1. New → Static Site → repo → *Root Directory* `frontend`.
2. Build command `npm ci && npm run build`; publish directory `dist`.
3. Environment (build-time): `VITE_API_URL=https://<backend>.onrender.com`.
4. SPA rewrite: Render static sites serve `index.html` fallback automatically for 404s —
   confirm "Rewrites" shows `/* → /index.html 200`.

### Create both environments

Create four Render services from the same public GitHub repository:

| Environment | Service | Render configuration |
|---|---|---|
| dev | `fs-dev-api` | Docker, root `backend`, health `/healthz`, dev Neon `DATABASE_URL` |
| dev | `fs-dev-web` | Static, root `frontend`, build `npm ci && npm run build`, publish `dist`, `VITE_API_URL=https://<dev-api>` |
| prod | `fs-prod-api` | Docker, root `backend`, production Neon `DATABASE_URL`, production `JWT_SECRET` |
| prod | `fs-prod-web` | Static, root `frontend`, prod `VITE_API_URL=https://<prod-api>` |

Set backend `CORS_ORIGINS` to that environment's frontend URL. Create a Deploy Hook for
all four services. Put the dev hooks in the GitHub `dev` environment (or repository secrets)
and the prod hooks in the `production` environment. Do not reuse JWT/database secrets
between dev and prod. Give both pairs distinct Render URLs and add those URLs to README.

## 4. CD — dev automatic, prod manual, rollback ready

`.github/workflows/ci.yml` runs the full suite (backend unit+integration on Postgres
service, frontend tests+build, on-call engine tests, security scans).

**Dev — automatic.** `.github/workflows/deploy.yml` (job `deploy-dev`) triggers on
`workflow_run: CI completed` for `main`, **only if `conclusion == success`**, and curls the
dev Render deploy hooks. Then it runs `ops/smoke.sh` against `FS_DEV_BACKEND_URL`.

**Prod — manual, gated.** The same workflow's `deploy-prod` job runs only via
**Run workflow** (`workflow_dispatch`) and is attached to the GitHub `production`
**environment**: create it under Settings → Environments → `production` → *Required
reviewers* = you. Optional `sha` input deploys a specific commit. Post-deploy smoke runs
against `FS_PROD_BACKEND_URL`.

**Rollback.** `.github/workflows/rollback.yml` (dispatch: bad SHA or blank = HEAD, plus a
reason) reverts on main → CI re-runs → dev auto-redeploys the reverted state; for instant
prod rollback use Render → Deploys → **Rollback** (no CI wait). Details:
`ops/runbooks/rollback.md`.

### Secrets & variables checklist (Settings → Secrets and variables → Actions)

| Name | Kind | Where from |
|---|---|---|
| `RENDER_DEPLOY_HOOK_BACKEND` | secret | dev backend service → Settings → Deploy Hook |
| `RENDER_DEPLOY_HOOK_FRONTEND` | secret | dev frontend service → Settings → Deploy Hook |
| `RENDER_DEPLOY_HOOK_PROD_BACKEND` | secret | prod backend service → Deploy Hook |
| `RENDER_DEPLOY_HOOK_PROD_FRONTEND` | secret | prod frontend service → Deploy Hook |
| `FS_DEV_BACKEND_URL` | variable | e.g. `https://fs-dev-backend.onrender.com` |
| `FS_PROD_BACKEND_URL` | variable | prod backend public URL |

## 5. Verification (evidence for criterion 8)

For a live Neon backend check, first `neon checkout neon-smoke` (the configured seven-day test branch), then run `backend/.venv/bin/python ops/neon-e2e-smoke.py` from the repository root. The script reads the ignored branch dotenv locally, normalizes the pooled URL for psycopg 3, starts the FastAPI app in-process, tests `/healthz` and register/login/me, and removes its temporary user/audit row. It prints only status codes, never configuration values. Do not run it against production.

```bash
curl -i https://<backend>.onrender.com/healthz        # 200 {"status":"ok"}
curl -s https://<backend>.onrender.com/version        # app Financial Statement, ai_provider gemini
bash ops/smoke.sh https://<backend>.onrender.com      # full lifecycle over HTTPS
bash ops/diagnostics.sh https://<backend>.onrender.com | tee ops/runs/$(date +%F)-prod-diagnosis.txt
```
Open the frontend URL, run the demo story, screenshot both. URLs go into README §Deployment.

## Rollback

Two paths (see §4): the **Rollback workflow** (`git revert` → CI → dev auto-redeploy,
prod via manual deploy) and Render's built-in rollback — Render keeps prior successful
deploys → service → Deploys → pick previous → "Rollback".
DB is not auto-migrated in v1 (`create_all` is additive-only); schema changes that need
migration land with Alembic post-M7 (see architecture.md ADR 3). Details:
`ops/runbooks/rollback.md`.
