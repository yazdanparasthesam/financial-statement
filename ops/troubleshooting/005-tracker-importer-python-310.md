# Troubleshooting episode 005 — Tracker importer compatibility with Python 3.10

**Date:** 2026-10-26  
**Status:** compatibility patch and dry run verified; commit `ce15063` pushed; all 14 public issues imported successfully; browser screenshot pending.  
**Evidence:** successful dry-run screenshot at `evidence/step5-tracker-dry-run-14-open-pending.png`; no failure screenshot retained.

## Issue and resolution

The owner's Ubuntu host runs Python 3.10.12. The tracker's `FOUND` lookup embedded a nested-quote f-string that requires newer Python parsing. The owner replaced it with `str.format`, preserving the NUL-safe YAML parsing and issue-title lookup.

Before importing issues, states 008–013 were changed to `open` because hosted CI/CD, deployed observability, alert/on-call recovery, and public Render deployments are not yet verified. The user ran `bash -n tracker/import.sh` and `bash tracker/import.sh --dry-run`; all 14 titles were listed without API side effects. Issues 001–007 and 014 remain marked closed as completed local implementation milestones.

## Next steps

1. The owner committed and pushed only `tracker/import.sh` and issue front matter files 008–012 as `ce15063`; issue 013 was already open and unchanged.
2. Run `gh auth status` locally; keep any token value private. Credential rotation is deferred by owner request to the final checklist.
3. The owner ran `bash tracker/import.sh --sync-state`: issues #1–#7 and #14 were created/closed, while #8–#13 were created open. `gh issue list --state all --limit 20` returned all 14.
4. Verify the public Issues tab and capture successful evidence.
