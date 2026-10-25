---
title: "Project scaffold, AGENTS.md context pack, product spec"
labels: [scaffold,agent-context]
milestone: "M1 — Foundations"
state: closed
agent: "Arena Agent"
---

## Goal
Repo skeleton, product-spec.md, AGENTS.md pointing at modular docs, Makefile, .env.example, LICENSE, seed data.

## Acceptance criteria
- [x] `product-spec.md` covers problem, users, journey, statutory context (Art. 95, INTA, 4-month deadline)
- [x] `AGENTS.md` exists and points to `docs/*` modules (architecture, decisions, testing, security)
- [x] `make help` lists every workflow; `.env.example` documented
- [x] `seed/` contains 4 realistic trial-balance CSVs (balanced FY2026 set)

## Agent evidence log
- **Arena Agent** — drafted spec + AGENTS.md structure; audited against 2025 full-mark projects (deedeepratiwi layout).
- **Arena Agent** — authored Makefile targets + `.env.example`; the repository artifacts and verification commands are the evidence.
- Verified: `make help`, `python -c "import yaml,sys; yaml.safe_load(open(\"docker-compose.yml\"))"`.
