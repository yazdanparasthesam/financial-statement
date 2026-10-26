# 009 — Neon Console sign-in succeeded, but Neon CLI authentication is still pending

**Status:** CLI sign-in and project linking succeeded on the user machine (2026-10-26); review of the generated Neon config is pending before deployment.

## Observed

- The user is signed into Neon Console and confirmed the existing `financial-statement` project, its default `production` branch, and a provisioned Postgres database.
- The first `npx --yes neon@latest login` attempt failed during package resolution with `ENOTFOUND` for the configured registry; no Neon auth flow began.
- Retrying with the official npm registry started browser authorization. The user completed it; terminal output confirmed `Auth complete (profile DEFAULT)`.
- The browser Console session is separate from Neon CLI authentication.
- Do not retain the failure screenshot in `evidence/`; failure states are recorded here as prose. Do not add personal paths, account identifiers, or registry hostnames to public evidence.

## Current workspace setup

- Global `npm i -g neon@latest` failed in the sandbox with `EACCES`; the allowed `npx neon@latest` fallback runs Neon CLI 8.11.4.
- Project-level Copilot MCP config was created at `.vscode/mcp.json` with OAuth URL only; Neon sign-in is prompted by the MCP client on first use.
- Neon overview, Postgres, and Postgres-branches skills are installed under `.agents/skills/` for GitHub Copilot.
- `.neon` is now ignored by Git. No authenticated Neon profile, `.neon`, or `neon.ts` exists in the workspace yet.

## Next safe action

The user ran the requested `neon init` command from the local project root. It linked `financial-statement` / `production`, generated `neon.ts`, installed dependencies, and pulled three variable names (`DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `NEON_BRANCH`) into local `.env`. The screenshot shows no values, and no local env file is present in the workspace. The CLI output recommends reviewing `neon config plan` before `neon deploy`; do that next. The CLI also installed a user-level Neon plugin for several agents and configured MCP for OpenCode. Do not record any API-key value from the local agent config.

## App integration finding

The backend already uses SQLAlchemy 2 and `psycopg[binary]` (psycopg 3). Preserve that driver. Use Neon’s pooled application URL as `DATABASE_URL`; use `DATABASE_URL_UNPOOLED` only for migration/admin work that needs a direct connection. App code still needs to read the Neon CLI dotenv output (`.env.local` when no `.env` exists) and normalize plain `postgresql://` URLs to the SQLAlchemy `postgresql+psycopg://` driver form if required.


## Config plan reviewed (2026-10-26)
The user ran `npx neon@latest config plan` against the linked `production` branch. Result: `No changes — branch production already matches the policy.` Utilized services: `Postgres`. This is the expected Postgres-only setup; proceed with `neon deploy` to apply/sync and refresh local environment variables.


## Neon deploy completed (2026-10-26)
The user ran `npx neon@latest deploy` against the linked production branch. Output confirmed `No changes — branch production already matches the policy`, `Utilized services: Postgres`, and three variable names were pulled into local `.env`: `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `NEON_BRANCH`. Values were not shared. The next code integration uses SQLAlchemy 2 + psycopg 3 and the pooled application URL.


## App wiring and workspace build (2026-10-26)
The user supplied the CLI-generated `neon.ts`, root `package.json`, and `package-lock.json`; these were added to the workspace. Root `npm ci && npm run build` passed. Root `npm test` passed all 27 frontend tests. Backend Ruff and the full backend pytest suite also passed after adding `.env` discovery and psycopg 3 URL normalization. The live app-to-Neon integration test remains pending; no Neon connection values were copied into the workspace.


## E2E branch selection (2026-10-26)
The user approved a temporary `neon-smoke` branch for the live app test, rather than writing smoke data to `production`. The branch policy in `neon.ts` applies a seven-day TTL to this new non-default branch. The user successfully created and checked out `neon-smoke`; Neon applied the new-branch policy with a seven-day TTL and pulled `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, and `NEON_BRANCH` into local `.env`. The app-level live test later passed on this temporary branch; see the E2E result below.


## Smoke helper added and locally validated (2026-10-26)
`ops/neon-e2e-smoke.py` loads the checked-out branch dotenv without printing values, normalizes the URL to psycopg 3, starts FastAPI through `TestClient`, verifies health and authenticated register/login/me, and removes the temporary user/audit row. It passed against a temporary SQLite database in the workspace. The user then ran it against the checked-out Neon test branch and it passed: `/healthz` 200, register 201, login 200, `/me` 200; temporary user/audit row cleanup completed. Success-only evidence is `evidence/08-neon-e2e-smoke.png` and is embedded in the course runbook.


## Python 3.10 local smoke compatibility (2026-10-26)
The user-created venv is Python 3.10. The import diagnostic found that `app.models` fails importing `datetime.UTC` (available starting in Python 3.11), in addition to the earlier generic PostgreSQL driver inference. Updated workspace `backend/app/models.py` to use `datetime.timezone.utc`, which works on Python 3.10+. The user applied the two-line compatibility edit in the local folder; the smoke then passed against the Neon test branch. The final bundle includes the Python 3.10-compatible implementation.


## Neon Console verification images (2026-10-26)
The owner supplied Console screenshots with `neon-smoke` selected (not production): branch list, app schema/tables, and monitoring activity. Safe crops omit browser URLs and account header; the separate monitoring capture that exposed endpoint hostnames was not retained. The branch-list crop shows `neon-smoke` as a child of production with active compute; the Console confirms the app schema exists. Evidence is indexed as `evidence/13`–`evidence/16` and embedded in the runbook.
