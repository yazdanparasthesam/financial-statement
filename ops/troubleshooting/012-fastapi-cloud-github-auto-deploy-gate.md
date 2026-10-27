# 012 — FastAPI Cloud gated deployment: app-directory mismatch

**Date:** 2026-10-27  
**Area:** Deployment architecture / CI-CD  
**Status:** Resolved through commit `009f887`. The dev workflow gates are active: CI #7 and Deploy #7 passed, and FastAPI Cloud shows `fs-dev-api` Live/Ready. The first two failures and their fixes are documented below; the missing runtime extra is detailed in [episode 013](013-fastapi-cloud-healthz-404.md).
**Evidence policy:** Successful setup and commit screenshots may be retained. Failed-state screenshots are not retained; failed attempts and causes are recorded here in prose only.

## Requirement and provider behavior

Deploy to dev only after CI passes; keep production manual and protected. FastAPI Cloud's [GitHub Integration documentation](https://fastapicloud.com/docs/source-control/github-integration/) says pushes to a connected default branch can deploy directly, which would bypass this project's gate. The user disconnected the app's repository and is using the deploy-token path in GitHub Actions instead. Do not reconnect the repository or click **Deploy latest commit**.

## Setup already completed

1. FastAPI Cloud app `fs-dev-api` exists; the app's application directory is configured as `backend`.
2. The GitHub repository remains disconnected in the app settings, preventing native push-to-deploy.
3. User reports Neon `dev` role password was reset and the pooled `dev` `DATABASE_URL` plus fresh `JWT_SECRET` were saved as FastAPI Cloud secrets. The gated `ops/smoke.sh` lifecycle test passed after deployment, exercising the dev API with its configured database.
4. FastAPI Cloud deploy-token and app-ID values are stored in GitHub repository Actions secrets `FASTAPI_CLOUD_TOKEN` and `FASTAPI_CLOUD_APP_ID`; values are not recorded here. At setup the token showed last used Never; the successful CI-gated deployment subsequently used it.
5. The guarded workflow was committed to `main` as `a520622`. CI run #5 passed; automatic Deploy #5 failed after 9 seconds with the diagnosed app-directory mismatch, and `deploy-prod` was skipped as intended.
6. The user removed both `working-directory: backend` overrides and committed the fix as `0f1854c`. CI run #6 passed; Deploy #6 uploaded the artifact but verification later failed because the runtime lacked `fastapi[standard]`. Details and remedy are documented separately in [episode 013](013-fastapi-cloud-healthz-404.md).

## Failure diagnosis

The first attempt's GitHub log panel temporarily reported it could not download the log. After refreshing, the log showed that the FastAPI Cloud CLI successfully detected `FASTAPI_CLOUD_TOKEN`, created deployment slug `fs-dev-api`, and uploaded the deployment artifact. It then failed with:

> The app directory `backend` was not found in the source.

The workflow's dev and production deploy steps had `working-directory: backend`. That made the CLI deploy from inside the backend directory, so the uploaded source no longer contained a child directory named `backend`, while the FastAPI Cloud app configuration expected that path relative to the uploaded repository root. This is a path-context mismatch, not evidence of an invalid deploy token or database credential. Do not rotate secrets based on this error.

## Resolution and remaining deployment work

1. **Resolved path mismatch:** removed both `working-directory: backend` overrides; commit `0f1854c` runs the CLI from the repository root so the configured `backend/` directory exists in the uploaded source.
2. **Resolved runtime startup:** commit `009f887` changed `backend/requirements.txt` to install `fastapi[standard]>=0.115`; the platform's default FastAPI CLI runtime can now start.
3. **Verified dev:** CI run #7 and gated Deploy run #7 passed. FastAPI Cloud shows `fs-dev-api` Live and latest deployment Ready. Deploy run #7's green result includes successful `/healthz` and `ops/smoke.sh` steps.
4. **Still pending:** configure Vercel and exact dev CORS origin. Before production deployment, create a separate production app and secrets, and configure required reviewers on GitHub's `production` environment.

## Historical observations

- The initial FastAPI Cloud GitHub picker said no GitHub App installations were found. The user installed the app, after which the repository appeared.
- The app was created with correct application directory `backend`; the root cause was the CLI's working directory, not the app setting.
- The failed attempt screenshot is not stored in evidence, consistent with the success-only evidence rule.

Official FastAPI Cloud references: [GitHub Integration](https://fastapicloud.com/docs/source-control/github-integration/), [Setup CI](https://fastapicloud.com/docs/fastapi-cloud-cli/setup-ci/), and [Deploy Tokens](https://fastapicloud.com/docs/advanced-features/deploy-tokens/).
