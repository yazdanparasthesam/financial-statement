# Runbook: AIUnavailableSpike

**Alert:** `rate(fs_ai_requests_total{status="error"}[10m]) > 0.02` for 2m (warning)
**User impact:** AI assist (explanations, notes drafts, chat, classification) returns the
`[AI UNAVAILABLE]` fallback. Deterministic features (statements, validation, workflow) are unaffected.

## Automated response (on-call agent)
Diagnose + escalate only. The safe degradation is a config flip, which needs a human decision.

## Manual checklist
1. Grafana → "AI calls by status/provider": is `gemini/error` spiking while `mock` is clean?
2. Provider-side: quota exhausted, key revoked, outage → check the provider status page.
3. **Mitigation:** set `AI_PROVIDER=mock` and restart — the app keeps working with
   deterministic mock responses (self-criticism / ReAct / ReWOO graphs still exercised).
4. `GEMINI_API_KEY` missing in the deploy environment → fix the secret, redeploy.
5. Confirm recovery: error rate back to 0 on the dashboard; AI notes endpoint returns provider text.
