---
title: "AI layer: LangChain/LangGraph — self-criticism, ReAct, ReWOO + MockLLM"
labels: [ai,backend]
milestone: "M4 — AI"
state: closed
agent: "Arena Agent"
---

## Goal
AI assist that is deterministic offline: anomaly explanation, notes drafting, classification, audit memo, chat.

## Acceptance criteria
- [x] `AI_PROVIDER=mock|gemini`; MockChatModel makes every graph runnable with zero keys
- [x] Self-criticism loop (draft → critique → revise, max loops configurable)
- [x] ReAct agent for assistant chat; ReWOO graph for audit memo (plan → solve)
- [x] TypedDict LangGraph state; failures degrade to `[AI UNAVAILABLE]`, never 500
- [x] Metrics: `fs_ai_requests_total{kind,provider,status}` + duration histogram

## Agent evidence log
- **Arena Agent** — designed graphs (D1–D6 dev log in IMPLEMENTATION_SUMMARY), implemented providers.py/graphs.py/ai_service.py.
- Verified: `pytest tests/unit -q` AI graph tests; smoke chat + memo + notes checks.
