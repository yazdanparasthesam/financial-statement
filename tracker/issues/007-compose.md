---
title: "Containerization: one-command full stack incl. DB"
labels: [infra]
milestone: "M6 — Infra"
state: closed
agent: "Arena Agent"
---

## Goal
`docker compose up --build` → frontend :3000, backend :8000, Postgres :5433, healthy.

## Acceptance criteria
- [x] Single command boots everything; healthchecks gate startup order (db → backend → frontend)
- [x] SQLAlchemy URL env-switch SQLite↔Postgres (same code, no changes)
- [x] `--profile obs` adds the full telemetry stack without touching app-only mode
- [x] Volumes persist DB/Grafana/Prometheus/Tempo/Loki state

## Agent evidence log
- **Arena Agent** — authored compose, fixed DB-name drift (`financial_statement` / `_ci`) found in on-disk audit.
- Verified: YAML lint + service graph check; user-side: compose up screenshot in evidence/.
