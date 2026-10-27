# Troubleshooting episode 004 — GitHub CLI authenticated with an over-scoped token

**Date:** 2026-10-26  
**Status:** owner deferred credential rotation until the final checklist; current `gh` authentication works, no issue creation yet.  
**Evidence handling:** no token value or screenshot retained. The screenshot displayed a masked token and broad scope names only.

## What happened

GitHub CLI 2.103.2 was installed and authenticated by pasting a classic personal access token. `gh auth status` showed numerous organization/enterprise administration, key, package deletion, and other broad scopes that are not needed for importing this project's issues. The token string was masked in the supplied screenshot; no token value was captured in chat or stored in project files.

## Deferred response

The owner asked to proceed quickly and defer this credential follow-up until the end. No token value is recorded here; do not request or capture it. Before final submission, remind the owner to revoke the broad token used for this login and replace it with browser-based authentication.

Recommended cleanup commands (deferred):

```bash
gh auth logout -h github.com
gh auth login --web --hostname github.com --git-protocol https
gh auth status
```

3. Confirm the resulting authentication is valid without showing a token value. If the new status still lists unrelated administrative scopes, stop and use a repository-scoped credential appropriate to the CLI operation.
4. Only then proceed with tracker work. The issue importer will not be run until its Python 3.10 compatibility and open/closed front-matter states are corrected in the owner’s local copy.

## Prevention

Use browser-based `gh` login; inspect scopes; never use a broad PAT for routine issue creation. The detailed policy is in `security-audit/credentials-handling.md`.
