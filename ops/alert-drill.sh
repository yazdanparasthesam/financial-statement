#!/usr/bin/env bash
# Alert → on-call agent drill (rubric: "an alert triggers and the on-call agent fixes it").
#
#   FULL DRILL     ./ops/alert-drill.sh
#     Requires: docker compose --profile obs up -d   AND   oncall-agent service (started by the profile)
#     Stops the backend on purpose → Prometheus fires BackendDown → Alertmanager
#     webhooks the agent → agent runs its runbook (docker compose restart backend) →
#     verifies /healthz → writes an incident report to ops/incidents/.
#
#   SIMULATE       ./ops/alert-drill.sh --simulate
#     No docker needed: POSTs oncall-agent/sample-alert.json straight to the agent.
#     The agent diagnoses/acts per runbook and writes the same incident report.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

AGENT_URL="${AGENT_URL:-http://localhost:8090}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PROM_URL="${PROM_URL:-http://localhost:9090}"
INCIDENT_DIR="ops/incidents"

latest_incident() { ls -t "$INCIDENT_DIR"/*.md 2>/dev/null | head -1 || true; }

if [ "${1:-}" = "--simulate" ]; then
  echo "== alert drill (SIMULATE): posting synthetic BackendDown to $AGENT_URL =="
  curl -sf "$AGENT_URL/healthz" > /dev/null || { echo "agent not running: start with docker compose --profile obs up -d"; exit 1; }
  BEFORE=$(latest_incident || true)
  curl -s -X POST "$AGENT_URL/alerts" -H 'Content-Type: application/json' \
       --data-binary @oncall-agent/sample-alert.json; echo
  for i in $(seq 1 30); do
    NEW=$(latest_incident || true)
    [ -n "$NEW" ] && [ "$NEW" != "$BEFORE" ] && break
    sleep 1
  done
  NEW=$(latest_incident || true)
  [ -n "$NEW" ] || { echo "no incident report produced"; exit 1; }
  echo "== incident report: $NEW =="
  cat "$NEW"
  exit 0
fi

echo "== alert drill (FULL): stopping the backend to trigger BackendDown =="
curl -sf "$AGENT_URL/healthz" > /dev/null || { echo "agent not running: start with docker compose --profile obs up -d"; exit 1; }
curl -sf "$BACKEND_URL/healthz" > /dev/null || { echo "backend not up: docker compose up -d"; exit 1; }
BEFORE=$(latest_incident || true)

docker compose stop backend
echo "backend stopped — waiting for Prometheus rule (30s for) + Alertmanager (10s group_wait) + agent…"

RECOVERED="no"; NEW=""
for i in $(seq 1 40); do   # up to ~200s
  sleep 5
  if curl -sf -m 3 "$BACKEND_URL/healthz" > /dev/null 2>&1; then RECOVERED="yes"; fi
  NEW=$(latest_incident || true)
  [ "$RECOVERED" = "yes" ] && [ -n "$NEW" ] && [ "$NEW" != "$BEFORE" ] && break
done

echo "== backend recovered: $RECOVERED =="
if [ -n "$NEW" ] && [ "$NEW" != "$BEFORE" ]; then
  echo "== incident report: $NEW =="
  cat "$NEW"
else
  echo "!! no incident report — check: docker compose --profile obs ps / prometheus alerts / agent stdout"
  curl -sf "$PROM_URL/api/v1/alerts" | python3 -m json.tool | head -30 || true
  exit 1
fi
[ "$RECOVERED" = "yes" ] || { echo "!! backend still down — runbook did not remediate"; exit 1; }
echo "== DRILL PASSED: alert fired, agent remediated, service recovered, report written =="
