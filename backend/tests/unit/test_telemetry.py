"""Unit tests for the telemetry layer: JSON logs with trace ids, metric helpers,
opt-in tracing. Everything offline — no exporters are started."""
import json
import logging

import pytest
from prometheus_client import REGISTRY

from app.infra.telemetry import (
    JsonFormatter,
    current_trace_id,
    inc_statement,
    inc_transition,
    inc_validation,
    init_telemetry,
    observe_ai_call,
    observe_journey_step,
    register_metrics,
)
from app.infra.telemetry.logging_conf import _SEVERITY, OtlpLogHandler


def _record(msg="hello", level=logging.INFO, **extra):
    return logging.LogRecord("fs.test", level, __file__, 1, msg, None, None)\
        if not extra else logging.Logger("fs.test").makeRecord(
            "fs.test", level, __file__, 1, msg, (), None, extra=extra)


@pytest.mark.unit
def test_json_formatter_shape():
    line = JsonFormatter().format(_record("startup ok"))
    data = json.loads(line)
    assert data["level"] == "INFO" and data["logger"] == "fs.test"
    assert data["message"] == "startup ok" and "ts" in data


@pytest.mark.unit
def test_json_formatter_whitelists_extras_only():
    """PII guard: arbitrary extras (emails, ids) never reach the log line."""
    rec = _record("http_request", method="POST", route="/api/filings/{filing_id}/submit",
                  status=200, duration_ms=12.5)
    rec.email = "someone@example.com"          # not whitelisted
    rec.national_id = "1234567890"             # not whitelisted
    data = json.loads(JsonFormatter().format(rec))
    assert data["route"] == "/api/filings/{filing_id}/submit"
    assert data["status"] == 200 and data["method"] == "POST"
    assert "email" not in data and "national_id" not in data
    assert "someone@example.com" not in json.dumps(data)


@pytest.mark.unit
def test_severity_mapping_covers_levels():
    assert _SEVERITY["INFO"] == 9 and _SEVERITY["ERROR"] == 17
    assert _SEVERITY["DEBUG"] < _SEVERITY["INFO"] < _SEVERITY["WARNING"] < _SEVERITY["CRITICAL"]


@pytest.mark.unit
def test_tracing_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    status = init_telemetry()
    assert status["tracing"] is False and "disabled" in status["reason"]
    assert current_trace_id() == ""  # no active span → empty, never raises


@pytest.mark.unit
def test_current_trace_id_with_active_span():
    from opentelemetry.sdk.trace import TracerProvider
    provider = TracerProvider()  # no exporters: fully offline
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("unit-span"):
        tid = current_trace_id()
    assert len(tid) == 32 and all(c in "0123456789abcdef" for c in tid)


@pytest.mark.unit
def test_business_metrics_move():
    def value(name, labels):
        return REGISTRY.get_sample_value(name, labels) or 0.0

    before = value("fs_statements_generated_total", {"kind": "cf"})
    inc_statement("cf")
    assert value("fs_statements_generated_total", {"kind": "cf"}) == before + 1

    before = value("fs_validation_runs_total", {"outcome": "passed"})
    inc_validation(0)
    assert value("fs_validation_runs_total", {"outcome": "passed"}) == before + 1

    before = value("fs_workflow_transitions_total", {"action": "accept", "to_status": "accepted"})
    inc_transition("accept", "accepted")
    assert value("fs_workflow_transitions_total",
                 {"action": "accept", "to_status": "accepted"}) == before + 1

    before = value("fs_ai_requests_total",
                   {"kind": "chat", "provider": "mock", "status": "ok"})
    observe_ai_call("chat", "mock", "ok", 0.01)
    assert value("fs_ai_requests_total",
                 {"kind": "chat", "provider": "mock", "status": "ok"}) == before + 1
    assert value("fs_ai_request_duration_seconds_count", {"kind": "chat"}) >= 1

    before = value("fs_journey_step_duration_seconds_count", {"step": "submit"})
    observe_journey_step("submit", 0.2)
    assert value("fs_journey_step_duration_seconds_count", {"step": "submit"}) == before + 1


@pytest.mark.unit
def test_register_metrics_lists_documented_names():
    names = register_metrics()
    assert "fs_statements_generated_total" in names and "fs_ai_requests_total" in names
    assert len(names) == 6


@pytest.mark.unit
def test_otlp_handler_swallows_provider_errors():
    """A broken provider must never break application logging."""
    class BrokenProvider:
        def get_logger(self, name):
            raise RuntimeError("collector down")

    handler = OtlpLogHandler.__new__(OtlpLogHandler)  # bypass __init__
    logging.Handler.__init__(handler)
    handler._logger = None
    handler._formatter = JsonFormatter()
    handler.handleError = lambda record: None
    rec = _record("anything")
    handler.emit(rec)  # would raise AttributeError inside → must be swallowed


@pytest.mark.unit
def test_otlp_handler_emits_native_trace_context():
    """The shipped OTLP bridge uses the SDK LogRecord API and inherits active span context."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    class Sink:
        record = None
        def emit(self, record):
            self.record = record

    sink = Sink()
    class Provider:
        def get_logger(self, _name):
            return sink

    handler = OtlpLogHandler(Provider())
    provider = TracerProvider()
    tracer = provider.get_tracer("telemetry-test")
    with tracer.start_as_current_span("linked-span"):
        handler.emit(_record("correlated"))
        expected = trace.get_current_span().get_span_context()
    assert sink.record is not None
    assert sink.record.body
    assert sink.record.trace_id == expected.trace_id
    assert sink.record.span_id == expected.span_id


@pytest.mark.unit
def test_trace_privacy_hook_redacts_raw_path_and_query():
    from app.infra.telemetry.tracing import _privacy_server_request_hook

    class Span:
        def __init__(self):
            self.attrs = {}

        def is_recording(self):
            return True
        def set_attribute(self, key, value):
            self.attrs[key] = value

    span = Span()
    _privacy_server_request_hook(
        span, {"path": "/api/filings/9382/submit", "query_string": b"customer=private",
               "client": ("203.0.113.42", 4444), "headers": [(b"user-agent", b"private-agent")]})
    assert span.attrs
    assert all(value == "[REDACTED]" for value in span.attrs.values())
    assert "/9382" not in repr(span.attrs) and "private" not in repr(span.attrs)
    assert "client.address" in span.attrs and "http.user_agent" in span.attrs
