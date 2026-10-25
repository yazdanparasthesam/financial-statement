"""Telemetry: OpenTelemetry traces + Prometheus metrics + structured logs.

Design rules (see security/telemetry-policy.md):
  * one trace_id joins the trace, the metric exemplars and every log line of a request;
  * no customer data, no credentials, no identifiers — only route templates, statuses,
    latencies and rule ids are recorded;
  * export is opt-in by env (OTEL_ENABLED): with it unset the app runs with zero
    exporters, so tests and CI stay offline and fast.
"""
from .logging_conf import JsonFormatter, OtlpLogHandler, RequestLogMiddleware, configure_logging
from .metrics import (
                      METRICS_ENABLED,
                      inc_statement,
                      inc_transition,
                      inc_validation,
                      observe_ai_call,
                      observe_journey_step,
                      register_metrics,
)
from .tracing import TRACING_ENABLED, current_trace_id, init_telemetry, instrument_app

__all__ = [
                      "METRICS_ENABLED",
                      "TRACING_ENABLED",
                      "JsonFormatter",
                      "OtlpLogHandler",
                      "RequestLogMiddleware",
                      "configure_logging",
                      "current_trace_id",
                      "inc_statement",
                      "inc_transition",
                      "inc_validation",
                      "init_telemetry",
                      "instrument_app",
                      "observe_ai_call",
                      "observe_journey_step",
                      "register_metrics",
]
