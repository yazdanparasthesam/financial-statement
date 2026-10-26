# Credentials Handling

Lessons applied from HW4 (where a PAT appeared in a terminal screenshot and had to be
rotated). Rules for this project:

1. **`.env` never commits.** Gitignored; `.env.example` holds placeholders only. CI has a
   gitleaks job; a pre-commit hook scans staged files.
2. **Screenshots/evidence:** before capturing a terminal, ensure no token, key, or
   connection string is visible. Export artifacts (PDF/XLSX) and `/version` output are safe
   by design (no secrets surface).
3. **Where each credential lives:**
   | Credential | Location | Rotation |
   |---|---|---|
   | `GEMINI_API_KEY` | local `.env` + Render env (secret-marked) + GitHub Actions secret (only if a live-AI CI job is added — currently CI is mock-only, so it is NOT needed there) | Google AI Studio → revoke; on any leak |
   | `JWT_SECRET` | local `.env` + Render env | regenerate (`secrets.token_urlsafe(48)`); invalidates sessions (acceptable) |
   | `DATABASE_URL` (Neon) | local `.env` (only for direct DB work) + Render env | Neon console → rotate password |
   | Render deploy hooks | GitHub Actions secrets `RENDER_DEPLOY_HOOK_*` | Render → Settings → regenerate hook |
   | `FS_TOKEN` (MCP) | agent's local env only | delete/recreate the demo user |
4. **Demo logins** (`preparer@fsapp.dev` etc.) are seeded *test data*, not credentials —
   they only exist where the seeder ran; prod seeding is not done.
5. **If something leaks:** revoke at the source first, then rotate, then note the incident
   in `security/audit-brief.md` findings log. Order matters: rotate-before-revoke leaves a
   window.

For GitHub CLI authentication and least-privilege guidance, see [security-audit/credentials-handling.md](../security-audit/credentials-handling.md).
