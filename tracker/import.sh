#!/usr/bin/env bash
# Creates GitHub Issues from tracker/issues/*.md (front-matter: title/labels/state).
# Idempotent: issue with same title is skipped. --sync-state closes issues marked state: closed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
DRY=0; SYNC=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --sync-state) SYNC=1 ;;
    *) echo "usage: tracker/import.sh [--dry-run] [--sync-state]"; exit 1 ;;
  esac
done
for f in tracker/issues/*.md; do
  # YAML is parsed safely; values are passed as NUL-delimited records, never eval'd.
  mapfile -d '' -t META < <(python3 - "$f" <<'PY'
import pathlib, sys, yaml
text = pathlib.Path(sys.argv[1]).read_text()
fm = yaml.safe_load(text.split("---", 2)[1])
body = text.split("---", 2)[2].strip()
pathlib.Path("/tmp/fs-issue-body.md").write_text(body)
for value in (fm["title"], ",".join(fm.get("labels", [])), fm.get("state", "open")):
    sys.stdout.write(str(value) + "\0")
PY
)
  TITLE="${META[0]}"; LABELS="${META[1]}"; STATE="${META[2]}"
  if [ "$DRY" = "1" ]; then
    echo "would create: $TITLE [$LABELS] ($STATE)"
    continue
  fi
  command -v gh >/dev/null || { echo "gh CLI required: https://cli.github.com"; exit 1; }
  ISSUES=$(gh issue list --state all --limit 1000 --json number,title,state)
  FOUND=$(printf '%s' "$ISSUES" | python3 -c 'import json,sys; title=sys.argv[1]; issues=json.load(sys.stdin); matches=[x for x in issues if x["title"] == title]; print("{}\t{}".format(matches[0]["number"], matches[0]["state"]) if matches else "")' "$TITLE")
  if [ -n "$FOUND" ]; then
    IFS=$'\t' read -r NUM REMAINDER <<< "$FOUND"
    if [ "$SYNC" = "1" ] && [ "$STATE" = "closed" ] && [ "$REMAINDER" = "OPEN" ]; then
      gh issue close "$NUM" --comment "Closed with evidence — see issue body (agent log + verification commands)."
    else
      echo "skip (exists): $TITLE (#$NUM, $REMAINDER)"
    fi
    continue
  fi
  IFS=',' read -r -a LABEL_ARRAY <<< "$LABELS"
  for label in "${LABEL_ARRAY[@]}"; do
    [ -z "$label" ] && continue
    gh label create "$label" --force --description "Financial Statement project tracker" >/dev/null 2>&1 || true
  done
  URL=$(gh issue create --title "$TITLE" --label "$LABELS" --body-file /tmp/fs-issue-body.md)
  echo "created: $URL"
  NUM="${URL##*/}"
  if [ "$SYNC" = "1" ] && [ "$STATE" = "closed" ]; then
    gh issue close "$NUM" --comment "Closed with evidence — see issue body (agent log + verification commands)."
  fi
done
