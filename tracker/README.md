# Task tracker

The public tracker for this project lives in **GitHub Issues** on the repository
(`https://github.com/yazdanparasthesam/financial-statement/issues`). This directory is the
source of truth the issues are generated from — every issue has acceptance criteria
and an **agent evidence log** (repo artifact, verification command, and—after import—
commit/CI links). Completed-work notes are retrospective; use the public issues for any
remaining work and reference their numbers in commits so future agent usage is directly auditable.

## Import into GitHub Issues (one command)

```bash
gh auth login                 # once
bash tracker/import.sh --dry-run  # inspect titles/states first
bash tracker/import.sh --sync-state # import; close only front-matter state: closed
```

Then close them as the work lands (`gh issue close N --comment "…"`), or close them
all at once after verifying — the front-matter already records the real state:

```bash
bash tracker/import.sh --sync-state   # creates + closes issues whose state: closed
```

## Layout

- `issues/NNN-slug.md` — one file per issue; YAML front-matter (title, labels,
  milestone, state, agent) + body with **acceptance criteria** and **evidence**.
- Issue numbers mirror the milestone plan in `IMPLEMENTATION_SUMMARY.md`.


## Current public status (2026-10-26)
GitHub shows 14 issues: #1–#8 and #14 closed; #9–#13 open. Local front-matter currently marks #10–#12 closed despite their public issues remaining open. Attach current evidence and reconcile those states before another `--sync-state` run; do not assume local state and GitHub state are synchronized.
