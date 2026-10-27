# 014 — Vercel CLI bootstrap and local project linking

**Date:** 2026-10-27  
**Area:** Vercel project provisioning / local Node tooling  
**Status:** **Resolved for project setup.** Empty project `fs-dev-web` was created and the local `frontend/` folder is linked to team `hesam2` and project `fs-dev-web`. No Git integration or deployment was created.  
**Evidence:** Successful redacted screenshots are indexed as [`evidence/41-vercel-fs-dev-web-cli-created.png`](../../evidence/41-vercel-fs-dev-web-cli-created.png), [`evidence/42-vercel-fs-dev-web-empty-project.png`](../../evidence/42-vercel-fs-dev-web-empty-project.png), and [`evidence/51-vercel-fs-dev-web-local-link.png`](../../evidence/51-vercel-fs-dev-web-local-link.png). The original terminal screenshot with a one-time device-login code and the later failed link attempt are not retained.

## Failure chronology and resolution

1. The initial `npx vercel@latest project create fs-dev-web` attempt used the configured npm registry `nexus.tasn.ir` and failed with `getaddrinfo ENOTFOUND` before Vercel CLI started.
2. Retrying with a command-scoped public registry successfully created the empty Vercel project. The dashboard confirms `fs-dev-web.vercel.app`, no Git connection, and no deployment.
3. A subsequent link attempt omitted the per-command registry override and again failed before CLI startup; it was also run from the repository root instead of `frontend/`.
4. The user then ran the corrected command from `~/Documents/financial-statement/frontend` with the public registry override. Vercel CLI confirms the directory is linked to `hesam2/fs-dev-web`.

## Local credential handling

During linking, the CLI downloaded a fresh `VERCEL_OIDC_TOKEN` to the local `.env.local` file and reported adding that file to `.gitignore`. Do not reveal, upload, or commit `frontend/.env.local`; it contains a local credential. This local token is not the planned GitHub Actions deployment credential. No token value was shared.

## Remaining deployment setup

The project remains Git-unconnected and undeployed to preserve the CI gate. Add the Vercel CLI token and project identifiers to GitHub Actions secrets, then add the Vercel CLI deployment job that runs only after successful CI. Keep Vercel Git integration disabled.
