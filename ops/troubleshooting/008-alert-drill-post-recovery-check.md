# 008 — Alert drill health checks still showed BackendDown after responder report

**Status:** resolved (2026-10-26). After waiting and refreshing, Prometheus showed the backend scrape target `1/1 UP`, and Alertmanager showed no alert groups. The responder’s recovery was confirmed independently.

## Observed

On 2026-10-25 UTC, the user ran `sudo ./ops/alert-drill.sh`. The command output reported:

- Backend was intentionally stopped; the `BackendDown` alert reached the responder.
- The responder's `docker compose restart backend` action returned `rc=0` and the container started.
- `/healthz` recovered after two attempts.
- Incident report `ops/incidents/20261025-221233-BackendDown-2e62e391.md` was written with **Status: remediated**.
- Script ended with `DRILL PASSED`.

Immediately afterward, the user showed Prometheus Targets with `financial-statement-backend (0/1 up)` and a DNS lookup error for `backend` (`127.0.0.11:53: server misbehaving`), plus Alertmanager still listing one `BackendDown` alert. These follow-up views were not saved as evidence because they do not show successful recovery.

## Resolution

After allowing the scrape/evaluation interval and refreshing, Prometheus showed `financial-statement-backend (1/1 up)` and a green `UP` state. Alertmanager showed `No alert groups found`. This confirms the host `/healthz` verification and Prometheus in-network scrape converged. Successful captures are `evidence/06-prometheus-target-recovered.png` and `evidence/06-alertmanager-cleared.png`. No failure screenshots were retained. The incident report was emitted at `ops/incidents/20261025-221233-BackendDown-2e62e391.md` with status `remediated`.


## Additional report received
The later resolved-notification report `ops/incidents/20261025-221257-BackendDown-2e62e391.md` is now included. It records the resolved webhook and “no action taken,” which is expected for the follow-up resolution event. The primary remediated report from the drill output (`20261025-221233-BackendDown-2e62e391.md`) was received and included alongside the resolved-webhook follow-up report.
