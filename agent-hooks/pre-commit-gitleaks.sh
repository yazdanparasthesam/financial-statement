#!/usr/bin/env bash
# Git pre-commit hook — blocks staged secrets.
# Install:  cp agent-hooks/pre-commit-gitleaks.sh .git/hooks/pre-commit
#           chmod +x .git/hooks/pre-commit
if command -v gitleaks >/dev/null 2>&1; then
  if ! gitleaks protect --staged --redact -v; then
    echo "pre-commit: gitleaks found a secret in staged changes — commit blocked." >&2
    echo "Remove it, or if it is a false positive: gitleaks allowlist (see security/audit-brief.md)." >&2
    exit 1
  fi
else
  # dependency-free fallback: common secret patterns in the staged diff
  if git diff --cached -U0 | grep -Ein \
    "(api[_-]?key|secret|token|password)[\"' ]*[:=][\"' ]*[A-Za-z0-9_\-]{16,}|AIza[0-9A-Za-z_\-]{30,}|ghp_[A-Za-z0-9]{30,}"; then
    echo "pre-commit: possible secret in staged changes (fallback scanner; install gitleaks for full coverage)." >&2
    exit 1
  fi
fi
exit 0
