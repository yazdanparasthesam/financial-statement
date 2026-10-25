# Submission evidence index

**Rule:** this folder contains successful evidence frames only. Failed attempts are described
in dated prose in the relevant issue/runbook; do not save or embed failure screenshots here.

The app/automation is prepared, but owner-side verification is still pending. Add each
screenshot after the corresponding step succeeds, then embed it in
`docs/course-submission-runbook.md` under that step.

| File | What it proves | Status |
|---|---|---|
| `01-public-repository.png` | Public GitHub repo contains the full project tree | pending owner push |
| `02-public-issues.png` | Imported GitHub Issues with acceptance criteria/evidence logs | pending `tracker/import.sh --sync-state` |
| `03-compose-smoke.png` | Full-stack Compose app starts; 28/28 HTTP smoke checks pass | pending Docker run |
| `04-observability.png` | Grafana dashboard + Prometheus target up | pending `--profile obs` |
| `05-trace-log-correlation.png` | JSON log trace ID links to the matching Tempo trace | pending Docker run |
| `06-alert-responder-recovery.png` | Real alert fired; Compose responder restarted backend and verified recovery | pending full alert drill |
| `07-ci-green.png` | GitHub Actions CI green on `main` | pending public repo run |
| `08-dev-deployed.png` | Dev public frontend/backend URLs + smoke test | pending Render/Neon setup |
| `09-prod-approved.png` | Manual production approval + deployed URLs + smoke | pending production gate |
| `10-peer-reviews.png` | Course platform confirms three peer reviews completed | pending course platform |

See [`docs/course-submission-runbook.md`](../docs/course-submission-runbook.md) for the
step-by-step procedure and screenshot placement.
