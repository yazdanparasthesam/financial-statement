# Final Project submission runbook — Financial Statement

This runbook records the Financial Statement project and the remaining course-submission gates.
The source and public tracker are published; local full-stack/observability, hosted CI, alert/on-call,
and the temporary Neon-branch app smoke are verified. **The project is not fully submission-complete**:
public Render deployment/CD secrets and three mandatory peer reviews remain owner tasks. Save only
successful screenshots in `evidence/`; record failed attempts in prose, never as evidence frames.

> Keep your own Git identity. Do not copy credentials into this repo. Never share `.env`,
> API keys, deploy-hook URLs or database URLs in screenshots/chat.

## Status snapshot

| Rubric area | Code/artifact status | Owner-side proof still needed |
|---|---|---|
| Problem + application spec | README + product-spec present | none beyond published repo |
| Public task tracker | 14 issues are public; #1–#8 and #14 are closed, #9–#13 are open in GitHub | reconcile GitHub #10–#12 (open publicly, marked closed in local issue files); close only with evidence links |
| Agent team + context | `docs/agent-team.md`, `AGENTS.md` and modular docs are in the public repo | none for rubric artifact; continue issue-linked work |
| Full stack + tests | Compose DB/backend/frontend healthy; live HTTP smoke **28/28**; backend 79, frontend 27, and responder tests pass; live Neon API smoke passes | optional richer two-year UI demo for cash-flow/anomaly evidence |
| Containerization | full app Compose (Postgres + backend + frontend) and `obs` profile verified locally | no blocker for local rubric criterion |
| Deployment | Neon Postgres policy and app-to-Neon smoke verified; Render deployment guide/workflows prepared | create public dev/prod services and record URLs/smoke results |
| CI/CD + rollback | workflow files exist; hosted CI run #3 on `6b643c1` passed all four jobs; rollback workflow/runbook prepared | configure deploy hooks/environments and verify dev auto-deploy + manual prod gate; current public issue #9 remains open |
| Observability + alert | Grafana/Loki/Tempo/Prometheus evidence; four user-impact rules; alert drill fired and cleared | reconcile public issue #10/#11 status with evidence |
| On-call responder | real alert reached the responder; it remediated, health recovered, and incident report was written | reconcile public issue #12 status with evidence |
| Peer reviews | not yet completed | complete **3 peer reviews** on course platform (mandatory to pass) |

## Step 1 — Extract the project and verify local tooling (verified)

The owner extracted the ZIP into the project root and confirmed the expected repository
layout (`README.md`, `backend/`, `frontend/`, `docker-compose.yml`, `observability/`,
`oncall-agent/`, and `tracker/`). The screenshot also confirms Docker Compose **v2.27.0**.

Successful evidence captured:

![Project root and Docker Compose version verified](../evidence/00-local-project-docker-version.png)

**Step 1 is complete.** Continue to Step 2 to test the app-only Compose stack. The public
GitHub repository is a later owner task (Step 4).

## Step 2 — Verify the app-only Compose stack

From the repository root:

```bash
cd "$HOME/Documents/financial-statement"  # the project root shown in Step 1
if [ ! -f .env ]; then
  cp .env.example .env
  python3 - <<'PYSECRET'
from pathlib import Path
import secrets
p = Path(".env")
t = p.read_text().replace("JWT_SECRET=change-me", f"JWT_SECRET={secrets.token_urlsafe(48)}")
p.write_text(t)
print("Generated a local JWT secret; value not displayed.")
PYSECRET
fi
docker compose config --quiet              # should return with no errors
docker compose up --build                  # leave this terminal running
```

Do not share or commit `.env`. In another terminal:

```bash
curl -fsS http://localhost:8000/healthz
curl -I http://localhost:3000
```

Expected for this sub-step: `docker compose ps` shows `db` and `backend` healthy and
`frontend` up; health JSON is `{"status":"ok"}`; the frontend returns HTTP 200 and displays
the sign-in screen. In this run the first build hit a Buildx permission error, then the
owner's `sudo docker compose up -d` retry succeeded. The error is documented in
`ops/troubleshooting/001-buildkit-permission-denied.md`; its failed screenshot is not kept
in evidence. Successful frames:

![Compose services healthy](../evidence/step2-compose-services-healthy.png)

![Compose service status](../evidence/step2-compose-ps.png)

![Backend health and frontend HTTP 200](../evidence/step2-health-and-http-200.png)

![Financial Statement login screen](../evidence/step2-frontend-login.png)

**Step 2 is complete; leave the services running.** The full HTTP smoke test is Step 3.
## Step 3 — Run the full HTTP smoke test

Keep the app-only Compose stack running. In a terminal at the project root:

```bash
cd "$HOME/Documents/financial-statement"
bash ops/smoke.sh http://localhost:8000
```

**Verified 2026-10-25:** the successful run returned **28 passed, 0 failed**. It covered
health/version, preparer/reviewer logins, prior-year statements, company/filing setup, TB
upload, statement generation, R001/R007, cash flow and ratios, self-critique notes, ReWOO
memo, ReAct chat, submit/review/accept, PDF/XLSX export, checklist, and Prometheus metrics.

![Full API lifecycle smoke test: 28 passed, 0 failed](../evidence/03-compose-smoke.png)

Step 3 is complete. Keep the stack running for subsequent local verification.

## Step 4 — Publish the project source to GitHub (verified)

Public repository: `https://github.com/yazdanparasthesam/financial-statement`.
The project source is on `main`, and the original GitHub starter commit is preserved in history.

The owner initialized an isolated repository at `/home/yazdanparasthesam/Documents/financial-statement`,
committed the project as `23ce9fb`, and merged the public starter commit `a050edf` using
`--allow-unrelated-histories`. Add/add conflicts in `.gitignore`, `LICENSE`, and `README.md`
were resolved conservatively: the generic Python ignore template was combined with project
secret/database protections; the complete project README was retained; and the MIT license
attribution uses the owner-confirmed handle `yazdanparasthesam`.

Merge commit `1b72378` has two parents (`23ce9fb` and `a050edf`). The normal push succeeded:
`a050edf..1b72378 main -> main`; `main` tracks `origin/main`, and `git status -sb` reported
`## main...origin/main` (clean). No force-push was used.

Success evidence:

![Project-scoped Git commit, clean worktree, no remote configured yet](../evidence/step4-project-commit-clean-no-remote.png)

![Local project and public starter histories fetched for safe merge](../evidence/step4-origin-fetched-unrelated-history.png)

![Resolved unrelated-history conflicts, clean .env ignore check](../evidence/step4-unrelated-history-resolved-env-ignored.png)

![Merge commit preserves project and starter parents; clean tree](../evidence/step4-merge-commit-two-parents-clean.png)

**Important repository safety note:** a separate parent-repository commit `d6fb15b` was
accidentally created under `$HOME`; it was not pushed. Never push from `$HOME`. Continue Git
commands only from the nested project root. Do not reset/revert/clean the parent repository
until its own remote and history are checked.

The owner asked to defer overlaying the updated evidence archive until the end. At final
packaging, overlay the rebuilt ZIP (excluding `.env`) into the current local folder and push
the documentation/evidence update as a follow-up commit.

## Step 5 — Public tracker status (import completed)

The issue definitions in `tracker/issues/` were imported into the public GitHub tracker. The
current public Issues page shows 14 issues: **#1–#8 and #14 closed; #9–#13 open**. Issue #8 was
closed after the verified green CI run. Public issues #10–#12 remain open even though their local
issue files and runbook contain completion evidence; reconcile those statuses and attach the
relevant evidence links before running `tracker/import.sh --sync-state` again. The initial public
issues screenshot below was taken before #8 closed, so it correctly shows the earlier six-open
state and is historical evidence, not the current count.

Public tracker: <https://github.com/yazdanparasthesam/financial-statement/issues>.
Each issue includes acceptance criteria and an agent evidence log; issue #8 also links the CI run
and commit that closed it. Continue referencing issue numbers in future commits/PRs.

![Initial public GitHub Issues list showing six open milestones before CI issue #8 closed](../evidence/02-public-issues.png)

![14 tracker issues dry-run with unfinished rubric work open](../evidence/step5-tracker-dry-run-14-open-pending.png)

### Hosted CI — verified green

After updating the Trivy action to a verified SHA, CI run #3 on commit `6b643c1` passed all four jobs: backend, frontend, oncall-agent, and security. The security summary reported “No leaks detected”; both SARIF and security scan artifacts were produced. The screenshots are successful evidence. Node 20 action-runtime deprecation notices are non-blocking and remain a maintenance note.

![Hosted CI green across all four jobs; no leaks detected](../evidence/07-ci-green.png)

![Uploaded security scan artifacts](../evidence/07-ci-security-artifacts.png)

Issue #8 is now closed publicly with the CI run URL and commit recorded in its evidence log.

## Step 6 — Verify observability, then run the real alert drill

The owner started the observability profile with telemetry enabled:

```bash
sudo env OTEL_ENABLED=true docker compose --profile obs up --build -d
sudo docker compose --profile obs ps
```

The app and telemetry services started; DB/backend and responder healthchecks passed. The
Prometheus scrape target `financial-statement-backend` is **1/1 UP**, and Alertmanager shows
no alert groups before the drill. Responder `/healthz`, Prometheus `/-/healthy`, and
Alertmanager `/-/healthy` all returned success.

![Compose observability profile services running](../evidence/04-observability.png)

![Responder, Prometheus, and Alertmanager health endpoints](../evidence/04-observability-health.png)

![Prometheus backend scrape target is UP](../evidence/04-prometheus-target-up.png)

![Alertmanager baseline has no alert groups](../evidence/04-alertmanager-baseline-clear.png)

To generate telemetry, the owner reran the full HTTP smoke after enabling OTel:

```bash
bash ops/smoke.sh http://localhost:8000
```

It passed **28/28**, including statement/workflow/HTTP metrics. Successful capture:

![Telemetry-enabled HTTP smoke: 28 passed, 0 failed](../evidence/04-observability-smoke.png)

After the initial scrape baseline, the owner reran the smoke and waited 25 seconds. Prometheus then reported statement-counter increase `5.1085` and HTTP-request increase `26.5663`; the golden-journey dashboard populated request rate, p95 latency, journey-step timing, statements (5), failed validations (1), submits (1), accepts (1), and AI calls. The 5xx panel has “No data,” expected because no 5xx responses occurred. The earlier zero-valued view is documented in `ops/troubleshooting/007-grafana-panels-zero.md` and is not retained as evidence.

![Golden-journey dashboard with request rate, latency, business counters](../evidence/04-grafana-golden-journey.png)

![Golden-journey AI metrics](../evidence/04-grafana-golden-journey-ai.png)

![Prometheus counter deltas after fresh smoke traffic](../evidence/04-observability-counter-delta.png)

Loki verification succeeded in Grafana Explore with `{service_name="financial-statement-backend"}` over the last 15 minutes: 142 JSON request logs were returned, and request entries include non-empty `trace_id` values. Success captures:

![Loki query returns structured backend logs](../evidence/05-loki-query-results.png)

![JSON request lines include trace IDs](../evidence/05-loki-json-trace-ids.png)

Tempo correlation succeeded: expanding a Loki request log exposed its `TraceID` link. Clicking it opened a Tempo trace with the same trace ID and multiple spans. Success evidence:

![Loki TraceID derived field links to Tempo](../evidence/05-loki-traceid-link.png)

![Matching Tempo trace and spans in Explore](../evidence/05-trace-log-correlation.png)

Observability metrics, logs, and traces are now verified. The next step is the real BackendDown alert drill; do not stop the profile before it completes.

After successful dashboard/log/trace checks, run the **real alert trigger** (it intentionally
stops the backend; the in-Compose responder restarts and verifies recovery):

```bash
sudo ./ops/alert-drill.sh
```

Expected: Prometheus `BackendDown` fires, Alertmanager posts to the internal responder,
`docker compose restart backend` runs, `/healthz` recovers, and a Markdown report appears in
`ops/incidents/`. Verify the report status is `remediated`; confirm Prometheus target returns
UP and Grafana recovers. The full drill reported `DRILL PASSED`, wrote incident report `ops/incidents/20261025-221233-BackendDown-2e62e391.md` with status `remediated`; a later Alertmanager resolved notification produced `ops/incidents/20261025-221257-BackendDown-2e62e391.md`, and `/healthz` recovered after two attempts. The first follow-up view was stale/unhealthy; after waiting and refreshing, Prometheus showed the backend target `1/1 UP` and Alertmanager showed no alert groups. This confirms the post-recovery state; do not rerun the drill. The mismatch and resolution are recorded in `ops/troubleshooting/008-alert-drill-post-recovery-check.md`.

Successful post-recovery captures:

![Prometheus backend target returned to UP](../evidence/06-prometheus-target-recovered.png)

![Alertmanager cleared after remediation](../evidence/06-alertmanager-cleared.png)

Optional no-outage webhook drill:
`sudo ./ops/alert-drill.sh --simulate`.

When done, shut down the profile without deleting data:

```bash
sudo docker compose --profile obs down
```

## Step 7 — Configure dev/prod deployment and CI/CD

### Neon Postgres integration (verified locally)

The user linked the existing Neon `production` branch, confirmed the plan had no changes (Postgres only), and ran `neon deploy`. The command confirmed the branch policy matches and pulled `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, and `NEON_BRANCH` into the ignored local `.env`; values were not captured. Successful output is embedded below.

![Neon deploy confirms Postgres policy and pulls the three environment variable names](../evidence/07-neon-postgres-deployed.png)

The CLI-generated `neon.ts`, root `package.json`, and lockfile are now incorporated. The branch policy disables Neon Auth (existing app JWT auth is preserved) and applies a seven-day TTL only to newly created non-default branches. Workspace code now reads repository-root `.env` / `.env.local` as well as the legacy `backend/.env`, and maps generic Postgres URLs to SQLAlchemy's existing psycopg 3 driver. Verification in the workspace: `ruff check app tests scripts` passed; the complete backend pytest suite exited 0; root `npm ci && npm run build` passed (TypeScript check, Vite production bundle, 102 modules); root `npm test` passed (27 frontend tests). `npm audit` reported 11 dependency advisories (8 moderate, 1 high, 2 critical); available high/critical fixes require major toolchain upgrades, so no `--force` upgrade was applied. Added `ops/neon-e2e-smoke.py`, which exercises FastAPI startup, database-backed register/login/me, and cleanup while reading the local branch URL without printing it. The user ran it against the checked-out temporary `neon-smoke` branch: `/healthz=200`, registration `201`, login `200`, `/me=200`, and the temporary user was cleaned up. This is the live FastAPI-to-Neon verification; the earlier workspace SQLite check was helper validation only.

![Neon branch FastAPI end-to-end smoke passed; temporary user cleaned up](../evidence/08-neon-e2e-smoke.png)

### In-app UI evidence (synthetic trial-balance data)

The following owner-provided UI captures are cropped to remove the signed-in email. They show a balanced 20-account trial balance, generated P&L and balance sheet, the clean 8/8 validation result, and a submitted filing with its mock audit memo. In this one-year demo, R006 (year-over-year) and R007 (cash-flow reconciliation) correctly report that they were skipped because no prior-year statements were on file; the figures remain deterministic. The live Neon connection itself is proven separately by the API smoke above.

![Uploaded balanced 20-account trial balance](../evidence/09-ui-trial-balance.png)

![Generated profit and loss and balance sheet](../evidence/10-ui-generated-statements.png)

![Validation clean: 8 of 8 checks passed](../evidence/11-ui-validation-clean.png)

![Submitted filing and mock audit memo](../evidence/12-ui-submitted-review.png)

### Neon Console evidence (temporary `neon-smoke` branch)

Owner-provided Neon Console captures show `neon-smoke` as a child of `production`, the application tables/schema present on that branch, and database monitoring activity after the API smoke. The data grid is empty because the smoke helper removes its temporary user and audit row; the schema remains. Browser URLs/account header were cropped, and no connection details are included.

![Neon branch list showing neon-smoke and its active compute](../evidence/15-neon-smoke-branches.png)

![Neon smoke branch contains the app's PostgreSQL tables](../evidence/13-neon-smoke-tables.png)

![Neon schema for the audit log table](../evidence/14-neon-smoke-schema.png)

![Neon monitoring captures database activity on neon-smoke](../evidence/16-neon-smoke-monitoring.png)

The CLI-generated `neon.ts` and root npm manifest/lockfile have been copied into the workspace and validated by the root build. The workspace model timestamp helper now uses `datetime.timezone.utc` for Python 3.10 compatibility.

Follow `docs/deployment.md` to create the four Render services (dev API + web, prod API
+ web). Use **separate** JWT/database secrets for dev and production; set exact frontend
CORS origins. Do not put secrets in Git or screenshots.

GitHub repo settings:

1. Settings → Environments → create `dev` and `production`.
2. `production` → Required reviewers → select yourself (this is the manual prod gate).
3. Add four Render deploy-hook secrets with the exact names in `docs/deployment.md`.
   Add Actions variables `FS_DEV_BACKEND_URL` and `FS_PROD_BACKEND_URL`.
4. Push any reviewed change to `main`; wait for CI (backend Postgres integration, frontend,
   on-call tests, security job) to pass. Confirm `deploy-dev` runs and the dev smoke passes.
5. Actions → Deploy → Run workflow → choose `prod`; approve the `production` environment;
   confirm prod smoke passes.
6. Verify the rollback workflow is present and read `ops/runbooks/rollback.md`. Do not test
   rollback on production just for evidence; use a disposable test branch/service if you
   want to demonstrate the workflow.

Open both public frontend URLs and run the demo. Set actual URLs in README §Deployment and
close tracker issue 013 after attaching successful Actions and smoke evidence. Capture
`evidence/07-ci-green.png`, `evidence/08-dev-deployed.png`, and
`evidence/09-prod-approved.png`.
## Step 8 — Final evidence and course submission

1. In `evidence/README.md`, tick each evidence row only after the screenshot exists.
2. Embed evidence screenshots in the runbook below the matching step (success images only).
3. Run `make test`, `make lint`, `cd frontend && npm test && npm run build`, plus the live
   smoke test against the deployed dev URL.
4. Confirm the FAQ field uses the accepted issue URL:
   `https://github.com/DataTalksClub/faq/issues/440` (optional contribution field).
5. On the course platform, evaluate **three other participants' projects**. This is mandatory
   for passing, regardless of your project score.
6. Submit the public repo URL, deployed frontend/backend URLs, tracker URL, evidence index,
   and FAQ URL (optional field). Keep screenshots of the successful submission/review state.
## Evidence embedding template

After each successful step, copy the screenshot into `evidence/` and add it here. Do not put
failed-state screenshots in this directory; document failures as dated prose in the relevant
issue/runbook instead.

<!-- Evidence images are embedded here as the owner completes the steps. -->
