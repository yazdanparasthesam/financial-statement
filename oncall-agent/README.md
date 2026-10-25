# On-call responder agent

The **responder** of the agent team (`docs/agent-team.md`). It is woken by an Alertmanager
webhook and fixes what can safely be fixed automatically — deterministically, with an audit
trail, and without an LLM in the loop.

## Why deterministic?
It executes shell commands. The safest possible design: `alertname → runbook → allow-listed
command → verify → incident report`. No prompt injection surface, no improvised fixes.

## Run it (Compose service — recommended)

The agent starts automatically with the observability profile; Alertmanager posts to it
on the internal Compose network. Port 8090 is bound to **127.0.0.1 only** for local drills.

```bash
OTEL_ENABLED=true docker compose --profile obs up --build -d
curl http://localhost:8090/healthz
```

The image contains the Docker CLI + Compose plugin because the `BackendDown` and
`SubmitFlowErrors` runbooks restart the backend. It receives a read-only repo mount, a
write-only incident-report mount, and the Docker socket. Keep this profile local; do not
expose the agent or Docker socket on a public host.

One-shot mode for local development/tests (no docker restart action unless Docker is present):

```bash
pip install -r oncall-agent/requirements.txt
python oncall-agent/agent.py --payload oncall-agent/sample-alert.json
```

## What happens on an alert

1. **Parse** the Alertmanager v4 payload (alertname, severity, annotations, fingerprint).
2. **Match** a runbook in `runbooks.yaml` (`default` = diagnose + escalate).
3. **Cooldown** — the same fingerprint is not re-remediated within 5 minutes.
4. **Diagnose** — run the runbook's diagnose/logs commands, capture output.
5. **Act** — run `action` only if it matches the exact command grammar in `agent.py`
   (safe `docker compose ps|logs|restart backend`, `echo`, `true`).
   No shell interpretation; everything else is refused, rc=126.
6. **Verify** — poll `verify_url` (`http://localhost:8000/healthz`) up to N times.
7. **Report** — write `ops/incidents/<ts>-<alertname>-<fp>.md` with the full timeline.
   Statuses: `remediated`, `escalated`, `diagnosed`, `suppressed`, `resolved`.

Resolved notifications (`send_resolved: true`) are logged as `resolved` incidents — no action.

## Runbooks shipped

| alertname | action | verify |
|---|---|---|
| `BackendDown` | `docker compose restart backend` | `/healthz` ×12 |
| `SubmitFlowErrors` | `docker compose restart backend` | `/healthz` ×12 |
| `GoldenJourneyLatencyHigh` | *(none — escalate)* | — |
| `AIUnavailableSpike` | *(none — escalate)* | — |
| `default` | *(none — escalate)* | — |

Warnings never trigger blind restarts: the agent collects evidence and escalates with the
human runbook (`ops/runbooks/*.md`).

## Evidence

Every drill leaves an incident report in `ops/incidents/` — see `example-incident.md` for
the format. Run the drill yourself: `./ops/alert-drill.sh` (full) or `--simulate` (no docker).

## Tests

```bash
python -m pytest oncall-agent/tests -q     # 10 tests: allowlist, cooldown, escalate, reports
```
