# Capability: Filing Audit (reusable workflow)

**Goal:** produce a one-page audit memo for a filing, using only server-provided facts.

**Requires:** MCP server `financial-statement` connected (read-only), a `FS_TOKEN` for a reviewer or
the owning preparer.

**Steps**
1. `list_filings` → pick the target filing (by id/status).
2. `get_filing` → status, fiscal year, deadline.
3. `get_latest_validation` → rule table; note every failed rule with severity + R-id.
4. `list_anomalies` → each anomaly's pct change + whether an explanation exists.
5. `get_statement pl` and `get_statement bs` → quote totals ONLY as given
   (never recompute; the system's numbers are the record).
6. `get_statement cf` (when present) → operating/investing/financing totals + the
   reconciliation gap (gap ≠ 0 ⇒ rule R007 concern).
7. `get_ratios` → quote values WITH their formula strings (current ratio < 1 ⇒ liquidity flag).
8. `get_checklist` → open items.
9. `review_history` → unresolved comments, last transition.

**Output format (memo)**
```
FILING AUDIT — #<id> FY<year> (<status>)
1. Gate status:      can it be submitted/accepted? which rules block?
2. Anomalies:        n flagged, m explained, largest movement X% (<section>)
3. Cash & liquidity: cf reconciliation gap, current ratio, quick ratio, D/E (with formulas)
4. Checklist:        k/8 done — missing: ...
5. Review trail:     last transition, open comments
6. Recommendation:   one sentence, addressed to the preparer or reviewer
```

**Guardrails:** read-only; no figures invented or recalculated; if a tool call fails,
say so in the memo instead of guessing; memo never includes national IDs/economic codes.

> The product ships this workflow as a built-in **ReWOO agent**
> (`POST /api/filings/{id}/audit-memo`: plan → execute the same read-only tools → solve).
> This MCP version is for external coding agents working against a running deployment.
