#!/usr/bin/env bash
# PostToolUse hook: instant feedback after an agent edits a file.
#  * backend python edited  → ruff on that file (exit 2 feeds lint errors back)
#  * contract-relevant file → remind to `make openapi`
input=$(cat 2>/dev/null || echo '{}')
file=$(printf '%s' "$input" | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
    ti=d.get("tool_input",{})
    print(ti.get("file_path") or ti.get("path") or "")
except Exception:
    print("")' 2>/dev/null)
[ -z "$file" ] && exit 0

case "$file" in
  *backend/app/*.py)
    if command -v ruff >/dev/null; then
      out=$(ruff check "$file" 2>&1) || { echo "ruff found problems in $file:" >&2; echo "$out" >&2; exit 2; }
    fi
    case "$file" in
      *routers/*|*schemas.py) echo "REMINDER: contract-relevant file changed — run 'make openapi' and commit the regenerated openapi.yaml." >&2 ;;
    esac
    ;;
  *frontend/src/api/*|*frontend/src/lib/*)
    echo "REMINDER: shared frontend module changed — run 'cd frontend && npm test'." >&2
    ;;
esac
exit 0
