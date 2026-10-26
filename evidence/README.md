# Submission evidence index

**Rule:** this folder contains successful evidence frames only. Failed attempts are described
in dated prose in the relevant troubleshooting record; do not save or embed failure screenshots.

Add a screenshot only after the corresponding owner-side step succeeds, then embed it in
`docs/course-submission-runbook.md` under that step.

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
| `08-dev-deployed.png` | Dev public frontend/backend URLs and smoke test | pending Render/Neon setup |
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

See [`docs/course-submission-runbook.md`](../docs/course-submission-runbook.md) for the
step-by-step procedure and screenshot placement.


**Current public tracker status checked 2026-10-26:** 14 issues total; #1–#8 and #14 closed, #9–#13 open. The local tracker files mark #10–#12 closed while GitHub still shows them open; reconcile before the next sync.
