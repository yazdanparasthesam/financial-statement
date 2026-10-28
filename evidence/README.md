# Submission evidence index

**Rule:** this folder contains successful evidence frames only. Failed attempts are described
in dated prose in the relevant troubleshooting record; do not save or embed failure screenshots.

Add a screenshot only after the corresponding owner-side step succeeds, then embed it in
`docs/course-submission-runbook.md` under that step. A cropped Export checklist snapshot is
embedded there as an in-progress instruction only; it is intentionally not indexed as completion evidence.

| File | What it proves | Status |
|---|---|---|
| `00-local-project-docker-version.png` | Project root extracted; Docker Compose v2.27.0 available | **verified (2026-10-25)** |
| `step2-compose-services-healthy.png` | Compose build completed; DB/backend healthy and frontend started | **verified (2026-10-25)** |
| `step2-compose-ps.png` | Compose status confirms the three app-only services running | **verified (2026-10-25)** |
| `step2-health-and-http-200.png` | Backend health endpoint OK; frontend responds HTTP 200 | **verified (2026-10-25)** |
| `step2-frontend-login.png` | Browser renders the Financial Statement login page | **verified (2026-10-25)** |
| `03-compose-smoke.png` | App-only Compose lifecycle smoke: 28 passed, 0 failed | **verified (2026-10-25)** |
| `step4-project-commit-clean-no-remote.png` | Nested project root verified; local commit present and worktree clean | **verified (2026-10-25)** |
| `step4-origin-fetched-unrelated-history.png` | Public starter history fetched; separate roots inspected before merge | **verified (2026-10-25)** |
| `step4-unrelated-history-resolved-env-ignored.png` | Merge conflicts resolved; project ignore rules retained and .env ignored | **verified (2026-10-25)** |
| `step4-merge-commit-two-parents-clean.png` | Merge commit 1b72378 preserves local project and GitHub starter parents | **verified (2026-10-25)** |
| `step5-tracker-dry-run-14-open-pending.png` | Historical dry run listed 14 issues; #8–#13 were open at that time | **verified (2026-10-26; historical state)** |
| `02-public-issues.png` | Historical public tracker capture: 14 issues, #8–#13 open before CI issue #8 closed | **verified (2026-10-26; historical state)** |
| `07-ci-green.png` | CI run #3 on 6b643c1: backend, frontend, oncall-agent, security green | **verified (2026-10-26)** |
| `07-neon-postgres-deployed.png` | Neon production branch matches the Postgres-only policy; three env var names pulled | **verified (2026-10-26)** |
| `07-ci-security-artifacts.png` | Security artifacts published; no leaks detected | **verified (2026-10-26)** |
| `04-observability.png` | Full Compose observability profile running; DB/backend healthy | **verified (2026-10-26)** |
| `04-observability-health.png` | Responder, Prometheus, and Alertmanager health endpoints succeed | **verified (2026-10-26)** |
| `04-prometheus-target-up.png` | Prometheus backend target financial-statement-backend is UP | **verified (2026-10-26)** |
| `04-alertmanager-baseline-clear.png` | Alertmanager has no firing alert groups before drill | **verified (2026-10-26)** |
| `04-observability-smoke.png` | Telemetry-enabled HTTP smoke: 28 passed, 0 failed | **verified (2026-10-26)** |
| `04-grafana-golden-journey.png` | Grafana golden-journey dashboard populated with request rate, latency, and business counters | **verified (2026-10-26)** |
| `04-grafana-golden-journey-ai.png` | Grafana AI-call rate and latency panels populated | **verified (2026-10-26)** |
| `04-observability-counter-delta.png` | Prometheus counters increased after fresh smoke; statements and HTTP requests recorded | **verified (2026-10-26)** |
| `05-loki-query-results.png` | Loki query returns structured backend request logs (142 entries) | **verified (2026-10-26)** |
| `05-loki-json-trace-ids.png` | Structured request logs carry non-empty trace IDs | **verified (2026-10-26)** |
| `05-loki-traceid-link.png` | Grafana derived TraceID field links directly to Tempo | **verified (2026-10-26)** |
| `05-trace-log-correlation.png` | Loki log trace ID opens matching Tempo trace with spans | **verified (2026-10-26)** |
| `06-prometheus-target-recovered.png` | Prometheus scrape target returned to 1/1 UP after the alert drill | **verified (2026-10-26)** |
| `06-alertmanager-cleared.png` | Alertmanager cleared BackendDown after remediation | **verified (2026-10-26)** |
| `../ops/incidents/20261025-221233-BackendDown-2e62e391.md` | Responder report proving BackendDown remediation (`Status: remediated`) | **verified (2026-10-26)**
| `../ops/incidents/20261025-221257-BackendDown-2e62e391.md` | Follow-up resolved webhook report | received (2026-10-26)
| `08-dev-deployed.png` | Final browser proof of a submitted dev filing and public API/web URLs | pending owner clicks Submit for review and captures resulting status; current browser flow through Draft review is indexed as evidence 62–71 |
| `09-prod-approved.png` | Production approval, deployed URLs, and smoke test | pending production gate |
| `10-peer-reviews.png` | Three course-platform peer reviews completed | pending course platform |
| `08-neon-e2e-smoke.png` | FastAPI against temporary Neon branch: health 200, register 201, login 200, /me 200; temporary user cleaned up | **verified (2026-10-26)** |
| `09-ui-trial-balance.png` | In-app synthetic trial balance: 20 accounts, debits equal credits; email header cropped | **verified (2026-10-26)** |
| `10-ui-generated-statements.png` | In-app generated P&L and balance sheet from seed data; email header cropped | **verified (2026-10-26)** |
| `11-ui-validation-clean.png` | In-app validation clean: 8/8 passed; year-over-year/cash-flow checks skipped without prior-year data; email header cropped | **verified (2026-10-26)** |
| `12-ui-submitted-review.png` | In-app submitted workflow and mock audit memo; email header cropped | **verified (2026-10-26)** |
| `13-neon-smoke-tables.png` | Neon Console on `neon-smoke`: app tables present; test rows cleaned after smoke | **verified (2026-10-26)** |
| `14-neon-smoke-schema.png` | Neon Console schema view for the application's audit-log table | **verified (2026-10-26)** |
| `15-neon-smoke-branches.png` | Neon branch list: `neon-smoke` child of production, compute active; account/browser chrome cropped | **verified (2026-10-26)** |
| `16-neon-smoke-monitoring.png` | Neon monitoring view shows database activity after smoke; hostnames not included | **verified (2026-10-26)** |
| `17-fastapi-cloud-hobby-dashboard.png` | FastAPI Cloud dashboard shows no app created yet; setup/access evidence only, not deployment proof | **verified (2026-10-26)** |
| `18-vercel-hobby-dashboard.png` | Vercel Hobby workspace usage panel; account name and unrelated project cards excluded; setup/access evidence only | **verified (2026-10-26)** |
| `19-fastapi-cloud-create-app-options.png` | FastAPI Cloud offers GitHub Repo and Empty app creation paths; account and browser identity excluded | **verified (2026-10-27)** |
| `20-fastapi-cloud-github-repository-list.png` | GitHub integration installed; public `financial-statement` repository is available to select | **verified (2026-10-27; setup only)** |
| `21-fastapi-cloud-backend-app-config.png` | Initial pre-create form confirms repository and `backend` application directory | **verified (2026-10-27; setup only)** |
| `22-fastapi-cloud-dev-app-config.png` | Updated pre-create form uses app name `fs-dev-api` and correct `backend` application directory | **verified (2026-10-27; setup only)** |
| `23-fastapi-cloud-created-not-deployed.png` | FastAPI Cloud dev API app `fs-dev-api` exists and shows **Not deployed**; GitHub source remains connected; no code deployed | **verified (2026-10-27; setup only)** |
| `24-fastapi-cloud-source-settings-connected.png` | Settings confirm `backend` root directory and currently connected GitHub repository; app remains not deployed | **verified (2026-10-27; pre-disconnect setup state)** |
| `25-fastapi-cloud-source-disconnect-control.png` | Scrolled settings show the repository **Disconnect** control; action not yet taken at capture time | **verified (2026-10-27; pre-disconnect setup state)** |
| `26-fastapi-cloud-github-disconnected.png` | FastAPI Cloud settings show repository **Not Connected** and root directory `backend`; auto-deploy integration removed | **verified (2026-10-27)** |
| `27-fastapi-cloud-env-empty.png` | Environment Variables page shows no variables set; app remains not deployed | **verified (2026-10-27; pre-configuration state)** |
| `28-fastapi-cloud-env-entry-form.png` | Blank environment-variable entry form; no values entered or saved | **verified (2026-10-27; pre-configuration state)** |
| `29-neon-dev-role-list.png` | Neon `dev` branch has role `neondb_owner`, which owns database `neondb`; no credential shown | **verified (2026-10-27; pre-rotation state)** |
| `30-neon-dev-role-list-branch-context.png` | Same Neon Roles view with project and `dev` branch selector visible; no credential shown | **verified (2026-10-27; pre-rotation state)** |
| `31-neon-dev-role-reset-menu.png` | Neon `dev` role menu shows **Reset password** for `neondb_owner`; no reset completed in this capture | **verified (2026-10-27; pre-rotation state)** |
| `32-neon-dev-role-after-reset.png` | User-reported post-reset Neon `dev` Roles view; no password shown; database connection test will verify the new credential | **owner-confirmed (2026-10-27; connection check pending)** |
| `33-fastapi-cloud-env-keys-partial.png` | Partial Environment Variables view shows `DATABASE_URL` and `JWT_SECRET` key names; values, Secret toggles, and save status are cropped out | **observed (2026-10-27; configuration not yet verified)** |
| `34-fastapi-cloud-dev-secrets-saved.png` | `DATABASE_URL` and `JWT_SECRET` are saved as encrypted secrets; values masked; app remains not deployed | **owner-confirmed (2026-10-27)** |
| `35-fastapi-cloud-deploy-token-active.png` | Active FastAPI Cloud deploy token is listed; token value is not shown; expires Jan 25, 2027; last used Never | **verified (2026-10-27; GitHub secret setup pending)** |
| `36-github-actions-secrets-empty.png` | Initial GitHub Actions repository-secrets page before FastAPI Cloud secrets were added | **verified (2026-10-27; historical setup state)** |
| `37-github-actions-secrets-configured.png` | Repository secret names `FASTAPI_CLOUD_APP_ID` and `FASTAPI_CLOUD_TOKEN` now exist; values are not displayed | **verified (2026-10-27)** |
| `38-github-deploy-workflow-committed.png` | GitHub shows the FastAPI Cloud CI-gated deployment workflow committed to `main`; hosted CI/deployment result is not shown | **verified (2026-10-27; commit a520622)** |
| `39-github-fastapi-deploy-7-green.png` | GitHub Actions CI #7 and the automatically gated FastAPI Cloud Deploy #7 are both green for commit `009f887` | **verified (2026-10-27)** |
| `40-fastapi-cloud-dev-deployment-live.png` | FastAPI Cloud dashboard shows `fs-dev-api` Live and latest deployment Ready; historical failures excluded from crop | **verified (2026-10-27; region us-east-1)** |
| `41-vercel-fs-dev-web-cli-created.png` | Vercel CLI confirms the empty `fs-dev-web` project was created; one-time device-authentication code and local shell identity are excluded | **verified (2026-10-27)** |
| `42-vercel-fs-dev-web-empty-project.png` | Vercel dashboard shows `fs-dev-web` and “Connect Git Repository”; project remains unlinked and undeployed | **verified (2026-10-27)** |
| `43-vercel-api-url-env-production.png` | `VITE_API_URL` saved in the Vercel project for Production; value is masked in the screenshot | **owner-confirmed (2026-10-27; verify it matches dev API URL before deployment)** |
| `44-vercel-build-and-root-settings.png` | Vercel build command `npm run build`, output `dist`, install `npm ci`, root `frontend`; custom overrides saved, preset shows Other | **verified (2026-10-27)** |
| `45-vercel-root-ignore-node-settings.png` | Root directory `frontend`; outside-root files included; skip-deployment optimization left disabled | **verified (2026-10-27)** |
| `46-vercel-basic-build-machine-settings.png` | Vercel project uses the Basic Hobby build machine; no paid build-machine upgrade selected | **verified (2026-10-27)** |
| `47-vercel-deployment-checks-and-rollout-settings.png` | No Vercel deployment checks configured; CI gate remains in GitHub Actions; on-demand concurrency unavailable on Hobby | **verified (2026-10-27)** |
| `48-vercel-oidc-and-retention-settings.png` | Rolling releases remain disabled; no OIDC policies configured; these are not needed for the planned CLI-token workflow | **verified (2026-10-27)** |
| `49-vercel-retention-settings.png` | Vercel deployment retention values reviewed at their existing 30-day settings | **verified (2026-10-27)** |
| `50-fastapi-cloud-dev-cors-origin-saved.png` | FastAPI Cloud `CORS_ORIGINS` set to the exact Vercel dev origin; `DATABASE_URL` and `JWT_SECRET` remain masked | **owner-confirmed (2026-10-27; Save Only, applies on next deployment)** |
| `51-vercel-fs-dev-web-local-link.png` | Vercel CLI confirms local `frontend/` is linked to team/project `hesam2/fs-dev-web`; token line and local identity are excluded | **verified (2026-10-27; no deployment)** |
| `52-vercel-project-metadata-redacted.png` | Local Vercel project metadata confirms `fs-dev-web`; organization/project IDs and shell identity are cropped out | **verified (2026-10-27; redacted)** |
| `53-vercel-project-scoped-token-settings.png` | Vercel token configuration selected scope `fs-dev-web` and 30-day expiry through 2026-11-26; no token value shown | **verified (2026-10-27; configuration form)** |
| `54-github-vercel-secrets-before-addition.png` | GitHub Actions secrets page before Vercel setup; only the two FastAPI Cloud secret names are present | **verified (2026-10-27; baseline)** |
| `55-github-vercel-deploy-secrets-configured.png` | GitHub repository Actions secret names `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, and `VERCEL_TOKEN` are present; values are hidden | **verified (2026-10-27)** |
| `56-github-vercel-dev-deploy-green.png` | GitHub Actions shows CI #9, API Deploy #9, and Deploy Vercel Web #2 green; commit `179fbd8` is visible on main | **verified (2026-10-27)** |
| `57-github-latest-dev-deploy-green.png` | Latest GitHub Actions shows CI #10 (`10f7387`), API Deploy #10, and Deploy Vercel Web #3 green | **verified (2026-10-27)** |
| `58-vercel-dev-project-production-ready.png` | Vercel `fs-dev-web` overview shows the Production deployment Ready at the public dev domain | **verified (2026-10-27)** |
| `59-vercel-dev-deployment-details-ready.png` | Vercel deployment details mark the latest deployment Ready and Production/Current for `fs-dev-web.vercel.app` | **verified (2026-10-27)** |
| `60-vercel-preview-login-page.png` | The Vercel-generated deployment URL serves the Financial Statement sign-in page | **verified (2026-10-27; preview deployment)** |
| `61-dev-web-login-page.png` | The stable `fs-dev-web.vercel.app/login` URL renders the Financial Statement sign-in page | **verified (2026-10-27)** |
| `62-dev-web-registration-form-redacted.png` | Registration page renders; full name, email, and password values are blanked in this evidence copy | **verified (2026-10-27; redacted)** |
| `63-dev-web-empty-dashboard.png` | Newly registered dev user reaches the initial Dashboard; no account email is included | **owner-confirmed (2026-10-27; redacted crop)** |
| `64-dev-web-company-created-redacted.png` | Dashboard company/filing form shown with the entered National ID value blanked | **owner-provided (2026-10-27; identifier redacted)** |
| `65-dev-web-filing-created.png` | Synthetic company and FY2026 filing #9 appear on the dev dashboard in Draft status | **owner-confirmed (2026-10-27; redacted crop)** |
| `66-dev-web-trial-balance-step.png` | Filing #9 opens at the Trial Balance step and accepts a CSV/XLSX upload | **owner-confirmed (2026-10-27; redacted crop)** |
| `67-dev-web-trial-balance-uploaded.png` | 20-account trial balance loaded; debits and credits each total 909,000 | **owner-confirmed (2026-10-27; synthetic data)** |
| `68-dev-web-statements-generated.png` | Deterministic Profit & Loss and Balance Sheet generated from the uploaded trial balance | **owner-confirmed (2026-10-27; synthetic data)** |
| `69-dev-web-validation-passed.png` | Validation reports 8/8 passed and clean; prior-year checks are skipped because none is on file | **owner-confirmed (2026-10-27; synthetic data)** |
| `70-dev-web-mock-notes-generated.png` | Mock AI Revenue note is generated and displayed; **Save final text has not yet been clicked** | **owner-confirmed (2026-10-27; redacted crop)** |
| `71-dev-web-review-draft.png` | Review page shows mock audit memo and a clear gate, but filing remains Draft; Submit for review has not been clicked | **owner-confirmed (2026-10-27; pre-submit)** |
| `72-neon-project-list.png` | Neon project list shows `financial-statement` in Frankfurt on the Free plan; no credentials shown | **owner-provided (2026-10-28; project-level evidence)** |
| `73-neon-production-branch-overview.png` | Neon overview shows the persistent `production` default branch and three project branches | **owner-provided (2026-10-28; branch exists, API not deployed)** |
| `74-neon-production-pooled-connect.png` | Connect dialog selects `production` / `neondb` / `neondb_owner`; pooling on and password masked; password rotation not confirmed | **owner-provided (2026-10-28; settings evidence, connection not yet tested)** |
| `75-fastapi-cloud-prod-env-secrets-masked.png` | FastAPI Cloud `fs-prod-api` lists `DATABASE_URL` and `JWT_SECRET` with masked values; app still Not deployed | **owner-provided (2026-10-28; values hidden; database connectivity not tested)** |
| `76-fastapi-cloud-prod-source-root-confirmed.png` | `fs-prod-api` settings show root `backend`, GitHub repository **Not Connected**, and app still Not deployed | **owner-provided (2026-10-28; preserves CI deployment gate)** |
| `77-github-production-environment-secrets.png` | `production` environment shows required reviewer (self-review allowed), admin bypass disabled, `main` only, and the two FastAPI Cloud prod secret names | **owner-provided (2026-10-28; values hidden; repo-level duplicates still pending cleanup)** |
| `78-github-prod-secrets-env-only.png` | Production API secrets appear under Environment secrets; repository list retains only dev FastAPI and Vercel secrets | **owner-provided (2026-10-28; names only, values hidden)** |
| `79-vercel-fs-prod-web-created.png` | Vercel CLI confirms empty `fs-prod-web` project created under team `hesam2`; no deployment shown | **owner-provided (2026-10-28; Git connection/deployment not performed)** |
| `80-vercel-fs-prod-web-settings.png` | Build fields are visible and `frontend` is typed in Root Directory, but its separate Save button remains active; later CLI inspect confirms root was still `.` | **owner-provided (2026-10-28; root setting not saved)** |
| `81-vercel-fs-prod-web-prod-api-url.png` | Confirms `VITE_API_URL` is saved for Production; URL was verified in the edit form before saving | **owner-provided (2026-10-28; no redeploy)** |
| `82-vercel-fs-prod-web-domain.png` | Vercel assigns `fs-prod-web.vercel.app` as the Production domain; shows `No Deployment` | **owner-provided (2026-10-28; domain assigned, no deployment)** |
| `83-fastapi-cloud-prod-cors-origin.png` | FastAPI Cloud `fs-prod-api` shows `CORS_ORIGINS=https://fs-prod-web.vercel.app`; DATABASE_URL/JWT_SECRET stay masked and app is not deployed | **owner-provided (2026-10-28; configuration saved, no deployment)** |
| `84-github-production-vercel-token-secret.png` | GitHub `production` environment lists `VERCEL_PROD_TOKEN` with no value exposed | **owner-provided (2026-10-28; token is set but workflow not ready)** |
| `85-vercel-token-project-scope-expiry.png` | Vercel token is scoped to `fs-prod-web` but marked `Never expires`; replace with finite expiry before use | **owner-provided (2026-10-28; remediation required)** |
| `86-vercel-cli-inspect-root-uncommitted.png` | Read-only Vercel CLI inspection reports Root Directory `.` for `fs-prod-web`, contradicting the unsaved UI entry of `frontend`; no deployment | **owner-provided (2026-10-28; root correction required)** |
| `87-vercel-cli-root-frontend-confirmed.png` | Vercel CLI inspection confirms saved Root Directory is `frontend` and build settings match the intended config | **owner-provided (2026-10-28; no deployment)** |
| `88-vercel-prod-project-id.png` | Vercel CLI JSON confirms project ID for `fs-prod-web`; `latestProductionUrl` is empty, so no deployment is recorded | **owner-provided (2026-10-28; read-only metadata)** |
| `89-vercel-team-id.png` | Vercel CLI JSON confirms team slug `hesam2` and team ID for the production project | **owner-provided (2026-10-28; read-only metadata)** |
| `90-github-prod-vercel-ids-added.png` | GitHub `production` environment lists `VERCEL_PROD_ORG_ID` and `VERCEL_PROD_PROJECT_ID`; secret values are hidden | **owner-provided (2026-10-28; environment-only configuration)** |
| `91-github-dev-chain-efb3596-green.png` | GitHub Actions shows CI #32, dev API Deploy #32, and dev Vercel Web #25 green for `efb3596`; no production dispatch | **owner-provided (2026-10-28; dev-only verification)** |
| `92-vercel-prod-git-disconnected.png` | Vercel project Settings explicitly says `fs-prod-web` is not connected to a Git repository | **owner-provided (2026-10-28; manual gate preserved)** |
| `93-deploy32-production-job-skipped.png` | GitHub Deploy #32: `deploy-dev` succeeded and `deploy-prod` was skipped for the automatic `workflow_run` event | **owner-provided (2026-10-28; manual production gate verified)** |

See [`docs/course-submission-runbook.md`](../docs/course-submission-runbook.md) for the
step-by-step procedure and screenshot placement.


**Current public tracker status checked 2026-10-26:** 14 issues total; #1–#8 and #14 closed, #9–#13 open. The local tracker files mark #10–#12 closed while GitHub still shows them open; reconcile before the next sync.
