# Troubleshooting episode 006 — Hosted CI failures after publication

**Date:** 2026-10-26\
**Status:** fixed and verified by green CI run #3 on commit `6b643c1`; issue #8 closure pending.\
**Evidence handling:** failure screenshot not retained; record only prose until successful green runs exist.

## Observed

Public GitHub Actions page for `CI` shows two failed workflow runs on `main`:

- CI run #2, commit `ce15063` (`fix: keep pending milestones open and support Python 3.10`), failed after ~49 seconds.
- CI run #1, commit `1b72378` (`merge: preserve GitHub starter history`), failed after ~55 seconds.

The latest run summary shows backend, frontend, and oncall-agent succeeded; security alone failed. The security annotation states: `Unable to resolve action aquasecurity/trivy-action@0.28.0, unable to find version 0.28.0`. Issue #8 remains open. No failure screenshot is retained in `evidence/`.

## Next diagnostic

The action repository migrated release tags to `v`-prefixed names. The latest signed `v0.36.0` release resolves to commit `ed142fd0673e97e23eac54620cfb913e5ce36c25`; the project workflow now pins this full SHA with a version comment. The owner applied and reviewed exactly the single-line action reference change; `git diff --check` passed. Next commit referencing issue #8, push normally, and wait for the new CI run. Close issue #8 only when all four jobs pass.
