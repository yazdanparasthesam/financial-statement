# Runbook: Rollback

## FastAPI Cloud API

A failed FastAPI Cloud rollout does not replace the last successful deployment; check the app's deployment/build/runtime logs first. If a successful rollout causes a regression, use the **Rollback** GitHub Actions workflow to redeploy a known-good commit:

1. Find the last known-good full commit SHA in the `CI` and `Deploy` workflow histories.
2. Actions → **Rollback** → Run workflow.
3. Select `dev` or `prod`, enter the full 40-character SHA, and provide a reason.
4. The workflow verifies that the SHA is reachable from `main` and has a successful `CI` run. Production waits for approval through the protected `production` environment.
5. It redeploys that commit's API code and runs `/healthz` plus `ops/smoke.sh`.

This redeploys the old code; it does not rewrite Git history. To permanently revert a bad change, create a normal `git revert` commit or PR, let CI pass, and merge. The standard dev deploy workflow then deploys the reverted state.

## Vercel frontend

The Vercel deployment/rollback path is still being configured. Once Vercel CLI deployment is wired behind the same CI gate, use its immutable deployment history to restore a known-good frontend build through the controlled workflow. Do not use a direct provider deploy/rollback action that bypasses the project gate.

## Data safety

V1 uses additive `create_all` schema setup, so an API code rollback does not require a database rollback. If a future Alembic migration is destructive, follow `backup.md` and plan a backward-compatible migration before rolling code back. Use Neon PITR only when application-level recovery is insufficient.
