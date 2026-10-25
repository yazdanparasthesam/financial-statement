"""Prometheus metrics — user-impact signals for the golden journey.

HTTP request metrics come from prometheus-fastapi-instrumentator (/metrics);
the business counters/histograms below answer "are filings progressing?":
statements generated, validation outcomes, workflow transitions, AI call health.
Histogram observations carry trace_id exemplars so Grafana can jump
metric spike → trace → logs (one correlated journey).
"""
from prometheus_client import Counter, Histogram

METRICS_ENABLED = True  # /metrics is always exposed; scrapers are opt-in

JOURNEY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

STATEMENTS_GENERATED = Counter(
    "fs_statements_generated_total", "Statements generated", ["kind"])
VALIDATION_RUNS = Counter(
    "fs_validation_runs_total", "Validation runs by outcome", ["outcome"])
WORKFLOW_TRANSITIONS = Counter(
    "fs_workflow_transitions_total", "Workflow transitions", ["action", "to_status"])
AI_REQUESTS = Counter(
    "fs_ai_requests_total", "LLM calls by kind/provider/status", ["kind", "provider", "status"])
AI_LATENCY = Histogram(
    "fs_ai_request_duration_seconds", "LLM call latency seconds", ["kind"],
    buckets=JOURNEY_BUCKETS)
JOURNEY_STEP = Histogram(
    "fs_journey_step_duration_seconds", "Golden-journey step latency seconds", ["step"],
    buckets=JOURNEY_BUCKETS)


def _trace_exemplar() -> dict | None:
    from .tracing import current_trace_id
    tid = current_trace_id()
    return {"trace_id": tid} if tid else None


def _observe(histogram: Histogram, value: float, labels: tuple) -> None:
    try:
        ex = _trace_exemplar()
        if ex:
            histogram.labels(*labels).observe(value, exemplar=ex)
            return
    except Exception:  # noqa: BLE001 — exemplars are best-effort; never break a request
        pass
    histogram.labels(*labels).observe(value)


def inc_statement(kind: str) -> None:
    STATEMENTS_GENERATED.labels(kind).inc()


def inc_validation(failed_count: int) -> None:
    VALIDATION_RUNS.labels("failed" if failed_count else "passed").inc()


def inc_transition(action: str, to_status: str) -> None:
    WORKFLOW_TRANSITIONS.labels(action, to_status).inc()


def observe_ai_call(kind: str, provider: str, status: str, seconds: float) -> None:
    AI_REQUESTS.labels(kind, provider, status).inc()
    _observe(AI_LATENCY, seconds, (kind,))


def observe_journey_step(step: str, seconds: float) -> None:
    """step: upload | generate | validate | submit (golden journey)."""
    _observe(JOURNEY_STEP, seconds, (step,))


def register_metrics() -> list[str]:
    """Metric names registered by this module (used by tests and docs)."""
    return ["fs_statements_generated_total", "fs_validation_runs_total",
            "fs_workflow_transitions_total", "fs_ai_requests_total",
            "fs_ai_request_duration_seconds", "fs_journey_step_duration_seconds"]
