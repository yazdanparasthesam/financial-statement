---
title: "Deploy to Render: public URLs for dev + prod"
labels: [deploy,needs-user]
milestone: "M7 — Ship"
state: open
agent: "USER (secrets required)"
---

## Goal
Rubric criterion 8: deployed public URL (dev auto-deploys; prod manual).

## Acceptance criteria
- [ ] Render services created (backend Docker, frontend static/Docker, Postgres)
- [ ] Secrets in GitHub: `RENDER_DEPLOY_HOOK_BACKEND`, `RENDER_DEPLOY_HOOK_FRONTEND`, `RENDER_DEPLOY_HOOK_PROD_*`
- [ ] Repo variables: `FS_DEV_BACKEND_URL`, `FS_PROD_BACKEND_URL`
- [ ] Environment `production` with required reviewer (manual gate)
- [ ] Push to main → dev deploy green; manual dispatch → prod deploy; smoke passes on both URLs

## Agent evidence log
- Agents prepared everything (workflows, runbooks, docs/deployment.md step-by-step).
- **Blocked on user-side secrets** — follow docs/deployment.md; paste screenshots into evidence/.
