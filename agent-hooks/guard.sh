#!/usr/bin/env bash
# PreToolUse guard for agent Bash calls (Claude Code hook protocol:
# reads hook JSON on stdin; exit 2 = BLOCK and feed stderr back to the agent).
# Blocks the destructive/secret-touching command classes listed in
# security/agent-security.md. Fails CLOSED on recognized danger patterns.
input=$(cat 2>/dev/null || echo '{}')
cmd=$(printf '%s' "$input" | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("command","") or "")
except Exception:
    print("")' 2>/dev/null)

[ -z "$cmd" ] && exit 0   # nothing parseable → not a Bash payload we govern

deny() { echo "BLOCKED by financial-statement guard ($1). Rewrite the command or ask the human to run it." >&2; exit 2; }

case "$cmd" in
  *"rm -rf /"*|*"rm -rf ~"*|*"rm -rf .git"*|*"rm -rf .."*) deny "destructive delete" ;;
  *"push --force"*|*"push -f "*|*"-f origin main"*|*"--force-with-lease origin main"*) deny "force-push" ;;
  *"chmod -R 777"*) deny "world-writable permissions" ;;
  *"docker system prune"*|*"docker volume rm"*) deny "container/volume destruction" ;;
esac

if printf '%s' "$cmd" | grep -Eq '(cat|less|more|head|tail|cp|scp|rsync|code)[^|;&]*[[:space:]](\.env|backend/\.env|frontend/\.env)([[:space:]]|$|;|&)'; then
  deny "reading/copying .env — secrets must not enter agent context"
fi
if printf '%s' "$cmd" | grep -Eiq '(DROP[[:space:]]+DATABASE|DROP[[:space:]]+TABLE|TRUNCATE[[:space:]]+TABLE)'; then
  deny "destructive SQL"
fi
# prod mutation guard: host matches AND a mutating flag appears anywhere in the command
if printf '%s' "$cmd" | grep -Eq 'onrender\.com|neon\.tech' \
   && printf '%s' "$cmd" | grep -Eq '(-X[[:space:]]*(POST|PUT|PATCH|DELETE)|--request[[:space:]]*(POST|PUT|PATCH|DELETE)|--data|-d[[:space:]])'; then
  deny "mutating production over HTTP — use the deployed UI or ask the human"
fi
exit 0
