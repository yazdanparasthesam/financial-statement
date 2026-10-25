---
title: "On-call responder agent: wakes on alert, fixes, reports"
labels: [oncall,agent]
milestone: "M7 — Ship"
state: closed
agent: "Arena Agent"
---

## Goal
Rubric criterion 12: an on-call agent wakes on an alert and fixes the issue.

## Acceptance criteria
- [x] `oncall-agent/agent.py` — stdlib + PyYAML only; Compose service in `obs` profile; POST /alerts (Alertmanager v4), GET /healthz
- [x] Deterministic runbooks.yaml: diagnose → allow-listed action → verify → incident report
- [x] Command allowlist enforced (`docker compose`/`echo`/`curl -s`/`true`); everything else refused rc=126
- [x] Cooldown dedupe; resolved-alert logging; warnings escalate instead of blind restarts
- [x] Incident markdown with full timeline → `ops/incidents/`
- [x] `ops/alert-drill.sh` (full + `--simulate`); 10 engine unit tests; responder runs as a Compose service and webhook stays internal

## Agent evidence log
- **Arena Agent** — implemented + verified live in sandbox: webhook POST → remediated incident report; real-runbook one-shot escalated gracefully where docker absent.
- Verified: `pytest oncall-agent/tests -q` (10), drill simulate transcript.
