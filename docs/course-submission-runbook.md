# Final Project submission runbook — Financial Statement

This is the step-by-step path from the workspace ZIP to a complete 2026 submission.
The project code is prepared; public GitHub, Docker, Render/Neon accounts, evidence
screenshots and the course-platform peer reviews must be completed by the owner.
**Do each step in order; save only successful screenshots in `evidence/`.** Failed attempts
belong in prose/incident notes, never in the evidence screenshot folder.

> Keep your own Git identity. Do not copy credentials into this repo. Never share `.env`,
> API keys, deploy-hook URLs or database URLs in screenshots/chat.

## Status snapshot

| Rubric area | Code/artifact status | Owner-side proof still needed |
|---|---|---|
| Problem + application spec | README + product-spec present | none beyond published repo |
| Public task tracker | 14 prepared issue files + importer | publish repo, import issues; reference issue numbers in remaining commits |
| Agent team + context | `docs/agent-team.md`, `AGENTS.md` and modular docs | publish |
| Full stack + tests | implementation present; 74 backend tests, 10 responder tests, 27 frontend tests passed | run Compose on your machine; capture successful run |
| Containerization | app-only and `obs` Compose profiles configured | build/run Docker images on your machine |
| Deployment | Render + Neon instructions and workflows prepared | create dev/prod services, configure URLs/secrets, verify URLs |
| CI/CD + rollback | workflows configured; dev auto / prod manual / rollback workflow | GitHub Actions green runs + protected production environment |
| Observability + alert | OTel/metrics/logs, LGTM Compose profile, 4 user-impact rules | start Docker stack, inspect Grafana, fire alert and capture successful recovery |
| On-call responder | Compose responder with exact command grammar + 10 tests | run the real alert drill; verify incident report |
| Peer reviews | optional FAQ contribution accepted | complete **3 peer reviews** on course platform (mandatory to pass) |

## Step 1 — Extract the final ZIP and publish a public GitHub repository

1. Download `financial-statement.zip` from this handoff and extract it.
2. Open a terminal in the extracted **`financial-statement/`** directory (the folder containing
   `README.md`, `backend/`, and `frontend/`).
3. On GitHub, create an **empty, public** repository named `financial-statement` (do not
   initialize it with a README, license or `.gitignore`).
4. In the project terminal, set your own identity and push the starter commit:

```bash
git init
git config user.name "YOUR NAME"
git config user.email "YOUR GITHUB EMAIL"
git add .
git commit -m "feat: complete financial statement project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/financial-statement.git
git push -u origin main
```

5. Confirm the public GitHub repo shows the README, `observability/`, `oncall-agent/`,
   `tracker/`, and `.github/workflows/`. Capture a screenshot in
   `evidence/01-public-repository.png`.

**Stop here and ask for review before continuing.** The remote must be public and the push
must succeed before importing issues or configuring GitHub Actions secrets.

## Step 2 — Create the public tracker issues

Prerequisites: GitHub CLI `gh` installed and authenticated (`gh auth login`) and your
terminal still in the project root.

```bash
gh auth status
bash tracker/import.sh --dry-run          # review the 14 titles first
bash tracker/import.sh --sync-state       # creates labels/issues; closes completed items;
                                          # leaves the Render deployment task open
```

Open the repo's **Issues** tab. Confirm the imported issues have acceptance criteria and
agent evidence logs. Leave `Deploy to Render: public URLs for dev + prod` open until that
work is really complete. During remaining steps, reference issue numbers in PRs/commits and
add workflow-run URLs to those issue bodies (the retrospective implementation log is not a
substitute for future public tracker use). Capture `evidence/02-public-issues.png`.

## Step 3 — Verify the app-only Compose stack

From the repository root:

```bash
cp .env.example .env                 # edit secrets locally; never commit .env
# set JWT_SECRET to a new random secret; leave AI_PROVIDER=mock for reproducibility
docker compose up --build
```

In another terminal:

```bash
curl -fsS http://localhost:8000/healthz
bash ops/smoke.sh http://localhost:8000
```

Expected: health JSON `{"status":"ok"}` and **28 passed, 0 failed**. Open
`http://localhost:3000` and verify the UI loads. Stop with Ctrl+C; keep the named DB volume.
Capture only successful compose startup + smoke output in `evidence/03-compose-smoke.png`.

## Step 4 — Bring up observability + responder, then run the real alert drill

Use one terminal for the Compose stack:

```bash
OTEL_ENABLED=true docker compose --profile obs up --build -d
docker compose --profile obs ps
```

Verify these local-only UIs:

- Grafana `http://localhost:3001` → “Financial Statement — golden journey” dashboard.
- Prometheus `http://localhost:9090/targets` → backend target is **UP**.
- Alertmanager `http://localhost:9093` → no firing alert before the drill.
- Responder health `curl -fsS http://localhost:8090/healthz`.

Create traffic and metrics:

```bash
python backend/scripts/seed_demo.py http://localhost:8000
bash ops/smoke.sh http://localhost:8000
```

Open Grafana and confirm request rate, journey-step timing, statement/validation/workflow
counters and AI status populate. Check Explore → Loki for JSON request lines; click a
`trace_id` derived field into Tempo. Capture successful target/dashboard/log correlation
screenshots in `evidence/04-observability.png` and `evidence/05-trace-log-correlation.png`.

Now run the **real alert trigger** (it intentionally stops the backend; the in-Compose
responder restarts and verifies it):

```bash
./ops/alert-drill.sh
```

Expected: the Prometheus `BackendDown` alert fires, Alertmanager posts to the internal
responder, `docker compose restart backend` runs, `/healthz` recovers, and a Markdown report
appears in `ops/incidents/`. Verify the report status is `remediated`; then verify Grafana
shows the target UP again. Capture only the successful fired→recovered result in
`evidence/06-alert-responder-recovery.png`. Optional no-outage webhook drill:
`./ops/alert-drill.sh --simulate`.

When done, shut down the profile without deleting data:

```bash
docker compose --profile obs down
```

## Step 5 — Configure dev/prod deployment and CI/CD

Follow `docs/deployment.md` to create Neon and four Render services (dev API + web, prod API
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

## Step 6 — Final evidence and course submission

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
