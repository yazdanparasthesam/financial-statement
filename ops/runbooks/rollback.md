# Runbook: Rollback

**App:** Render → service → Deploys → select last known-good → Rollback (both services if
the contract changed between versions). Re-run `ops/smoke.sh` after rollback.

**Data:** v1 has no destructive migrations (`create_all` is additive), so app rollback never
requires DB rollback. If a future Alembic migration must be reverted:
`alembic downgrade -1` (post-M7), then restore from Neon PITR/backup only as last resort
(`backup.md`) — PITR loses nothing, dumps lose since-dump writes.

**Frontend:** static-site deploys are immutable builds — rolling back is re-publishing the
previous build (Render keeps it). No cache purge needed (hashed asset filenames).
