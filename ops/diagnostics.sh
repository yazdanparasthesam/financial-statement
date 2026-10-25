#!/usr/bin/env bash
# Operational diagnosis: latency, liveness, AI mode, stack state. Output is the
# "operational diagnosis output" artifact (criterion 13) — tee it into ops/runs/.
# Usage: bash ops/diagnostics.sh [BASE_URL] [FRONTEND_URL]
set -uo pipefail
BASE="${1:-http://localhost:8000}"
FRONT="${2:-}"
echo "== Financial Statement diagnostics $(date -u +%FT%TZ) =="
echo "target: $BASE"

probe() { # probe <label> <url>
  local label="$1" url="$2"
  local out code time
  out=$(curl -s -o /tmp/diag_body -w '%{http_code} %{time_total}' --max-time 20 "$url" 2>/dev/null) || out="000 0"
  code="${out%% *}"; time="${out##* }"
  echo "  $label: HTTP $code in ${time}s"
  [ -s /tmp/diag_body ] && head -c 200 /tmp/diag_body && echo
}

probe "healthz" "$BASE/healthz"
probe "version" "$BASE/version"
if [ -n "$FRONT" ]; then probe "frontend" "$FRONT"; fi

echo "-- database port reachability --"
if command -v python3 >/dev/null; then
  python3 - <<'PYEOF'
import os, socket
url = os.environ.get("DATABASE_URL", "")
if "@" in url and ":" in url.rsplit("@", 1)[1]:
    hostport = url.rsplit("@", 1)[1].split("/")[0]
    host, _, port = hostport.partition(":")
    try:
        s = socket.create_connection((host, int(port or 5432)), timeout=5); s.close()
        print(f"  {host}:{port or 5432}: reachable")
    except OSError as e:
        print(f"  {host}:{port or 5432}: UNREACHABLE ({e})")
else:
    print("  DATABASE_URL not set in this shell — skipping (backend probes above cover it)")
PYEOF
fi

echo "-- container state (if docker present) --"
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  docker compose ps --format 'table {{.Name}}\t{{.Status}}' 2>/dev/null || echo "  (not a compose directory)"
else
  echo "  docker not available here — skipped"
fi
echo "== end =="
