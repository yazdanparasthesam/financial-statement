# Runbook: GoldenJourneyLatencyHigh

**Alert:** p95 API latency > 2s for 5m (warning)
**User impact:** uploads/generation feel broken; users retry and pile up load. No errors yet.

## Automated response (on-call agent)
**None — by design.** The agent diagnoses (compose ps + backend logs) and escalates:
blindly restarting on latency can make things worse (cold caches, in-flight uploads).

## Manual checklist
1. Grafana → "Golden-journey step p95": which step is slow (upload / generate / validate / submit)?
2. `generate` slow → expected for large trial balances; check `fs_journey_step_duration_seconds`
   exemplars → Tempo traces → which domain function dominates.
3. `upload` slow → file size / disk IO; check container resources.
4. DB-bound slowness → `docker compose logs db`, missing indexes, connection pool size.
5. If a bad deploy correlates: `ops/runbooks/rollback.md`.
