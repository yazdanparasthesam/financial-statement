---
title: "Security hardening pass + credentials handling docs"
labels: [security]
milestone: "M7 — Ship"
state: closed
agent: "Arena Agent"
---

## Goal
Ship without secret leaks or credential mishandling.

## Acceptance criteria
- [x] gitleaks blocking in CI; scanners produce artifacts each run
- [x] `security-audit/credentials-handling.md` pattern; JWT secret required non-default
- [x] Telemetry privacy: whitelist-only log extras, no PII in labels/spans (security/telemetry-policy.md)
- [x] On-call agent allowlist + no-LLM design documented (security/agent-security.md)
- [x] CORS configurable; register/login rate-limit posture documented

## Agent evidence log
- **Arena Agent** — audit + policy docs; **Arena Agent** — wired the scanner workflow; CI config is the verification evidence.
- Verified: CI security job green; on-disk credential scan clean.
