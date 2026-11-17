# Capability: Visit Audit (reusable workflow) — ClinicOps Multimodal

**Goal:** produce a one-page audit memo for a visit, using only server-provided facts.

**Requires:** MCP server `clinicops-multimodal` connected (read-only), a `CLINICOPS_TOKEN` for a reviewer (`doctor`) or the owning `nurse`/`pharmacist`.

**Steps**
1. `list_visits` → pick the target visit (by id/status).
2. `get_visit` → status (`draft`/`submitted`/`in_review`/`approved`/`dispensed`), deadline, patient.
3. `get_scores` → 10 computed scores (BMI, eGFR, MAP, BSA, Wells, CCI, dose/kg …); note any `null` (missing vitals).
4. `get_latest_validations` → R001–R008 table; note every failed rule with severity + R-id.
5. `list_attachments` → each attachment's `kind` (csv/image/audio/pdf) + `sha256` + whether transcription/vision draft exists.
6. `get_ai_draft vision_draft` and `get_ai_draft transcribe` → quote findings ONLY as given (never recompute; the model's text is the record).
7. `get_ai_draft notes_draft` (when present) → SOAP sections + reconciliation gap (gap ≠ 0 ⇒ R006/R007 concern).
8. `get_audit_log` → workflow transitions (`draft→submitted→in_review→approved`).
9. `get_checklist` → open items (`notes_finalized`, `submitted`, `accepted`).
10. `list_comments` → unresolved comments, last transition.

**Output format (memo)**
```
VISIT AUDIT — #<id> <patient_name> (<status>)
1. Gate status:      can it be submitted/approved? which rules block? (R001-R008)
2. Multimodal:       n attachments (csv/image/audio), m transcribed/vision-drafted
3. Scores & safety:  BMI/eGFR/MAP/Wells etc. (with formulas), missing vitals flag
4. Validations:      k/8 passed — failed: R005 consent, R008 missing vitals …
5. Checklist:        k/5 done — missing: ...
6. Review trail:     last transition, open comments
7. Recommendation:   one sentence, addressed to the preparer or reviewer
```

**Guardrails:** read-only; no figures invented or recalculated; if a tool call fails, say so in the memo instead of guessing; memo never includes national IDs; respect RBAC (nurse creates, doctor approves, pharmacist dispenses).

> The product ships this workflow as a built-in **ReWOO/ReAct agent**
> (`POST /api/visits/{id}/audit-memo` or `POST /api/ai/chat`: plan → execute the same read-only tools → solve).
> This MCP version is for external coding agents working against a running deployment.

**ClinicOps mapping vs Financial Statement:**
* `filing` → `visit` | `statement pl/bs/cf` → `scores + attachments + ai_drafts` | `ratios` → `clinical scores` | `anomalies` → `R001-R008 validations` | `review_history` → `audit_log + comments`
