# Troubleshooting episode 002 — Git root was the home directory

**Date:** 2026-10-25\
**Status:** parent-root mistake confirmed; isolated project repository created and committed; merge is paused for conflict review.\
**Evidence handling:** failed/mis-scoped Git output is recorded only in prose, not saved in `evidence/`.

## Cause

The check `git rev-parse --is-inside-work-tree` only proves that the current directory is inside *some* Git worktree. It does not prove that the worktree root is the project. The assistant recommended that insufficient guard; `git init` was therefore skipped because an ancestor repository existed.

Read-only inspection from `~/Documents/financial-statement` returned:

```text
git rev-parse --show-toplevel
/home/yazdanparasthesam

git log -1 --format='commit=%h%nparents=%P%nsubject=%s'
commit=d6fb15b
parents=a3a960191f0432449a9cf3c1491573b77f29d375
subject=feat: upload financial statement project
```

The commit output listed `Documents/financial-statement/...` paths. A later status listing contained unrelated `../../../...` paths, confirming that the current view was not safely scoped to the project. The accidentally-created commit remains local; it has not been pushed to the Financial Statement GitHub repository.

## Safety status

- **Do not push from `$HOME` or the ancestor repository.** It may contain unrelated/private files.
- **Do not reset/revert/clean the parent repo until its history/remotes are checked.** The project files must be preserved.
- `.env` was checked with `git check-ignore -v .env` and is ignored; `.env.example` was staged, which is expected.
- The screenshot with unrelated paths and personal identity is not retained as public evidence.

## Safe recovery

From the project root, create a nested repo and verify its root before any staging:

```bash
cd ~/Documents/financial-statement
git init -b main
git rev-parse --show-toplevel
```

Verified by the owner: `git init -b main` created `/home/yazdanparasthesam/Documents/financial-statement/.git/`, and `git rev-parse --show-toplevel` printed exactly `/home/yazdanparasthesam/Documents/financial-statement`. Next, copy the configured local identity into this nested repository without displaying the email, then stage and inspect only from this directory. The owner reviewed the project-only staged summary: 204 files, 16,640 insertions. `git check-ignore -v .env` returned `.gitignore:16:.env`, and `git status --short -- .env` printed nothing. No `.env` or database is listed in the staged summary. The owner verified the nested repository commit `23ce9fb` (`feat: upload financial statement project`); `git status --short` and `git diff --cached --stat` were empty. The project working tree is clean, and `git remote` printed no remotes. A success-only screenshot is retained in `evidence/step4-project-commit-clean-no-remote.png`. The intended public `origin` was added and fetched. History inspection showed local `23ce9fb` and `origin/main` `a050edf` as separate roots. Their histories are being joined using `git merge --no-commit --no-ff --allow-unrelated-histories origin/main`. The merge is paused with add/add conflicts in `.gitignore`, `LICENSE`, and `README.md`. Do not stage, commit, abort, or push until the project and starter versions are reviewed. Preserve the full project README and its `.env` protections while retaining the remote starter commit in history. The earlier `git commit` response said nothing to commit, but read-only inspection confirmed the commit exists. Never force-push. The parent commit cleanup is a separate optional task after checking the parent repo's tracking remote and branch status.

## Prevention

Always verify `git rev-parse --show-toplevel` equals the intended repository root; never use only `--is-inside-work-tree` as a repository-boundary guard.


## Unrelated-history conflict review (2026-10-25)

The owner ran a no-commit/no-ff merge of `origin/main` with `--allow-unrelated-histories`. Git paused with add/add conflicts in `.gitignore`, `LICENSE`, and `README.md`; no screenshot was retained as evidence because the merge is unresolved. Stage inspection showed:

- Project `.gitignore` includes `.env`, `.env.*`, `!.env.example`, `*.pem`, database files, Python/Node caches, and editor artifacts.
- Starter `.gitignore` is a broad generic Python template. A safe resolution combines the starter template with the project-specific rules, placing the latter last so `.env.example` remains unignored.
- Project README is the substantive Financial Statement guide; starter README contains only the placeholder title. Retain the project README in the merge result; the starter commit remains preserved in Git history.
- Both licenses are MIT. The project license attributes Hesam Yazdanparast but links to `github.com/yazadanparasthesam`, while the public repository owner is `yazdanparasthesam`. The owner confirmed using the public repo owner handle `yazdanparasthesam` in the resolved project license.

Resolution was staged after the owner confirmed the public handle `yazdanparasthesam`: the combined `.gitignore` keeps the full generic template plus local `.env`, `.env.*`, `!.env.example`, `*.pem`, and database exclusions; the complete project README is retained; the MIT LICENSE uses the confirmed handle. `git ls-files -u` and `git diff --cached --check` printed nothing, `.env` remains ignored, and status shows only `.gitignore` and LICENSE modified against the local project commit (README content is unchanged). A success-only screenshot is saved in `evidence/step4-unrelated-history-resolved-env-ignored.png`. Merge commit `1b72378` was verified with parents `23ce9fb` and `a050edf`; `git status --short` was clean. Success evidence is saved in `evidence/step4-merge-commit-two-parents-clean.png`. Next push only from the nested project repository. The accidental parent-root commit `d6fb15b` remains local and must not be pushed.
