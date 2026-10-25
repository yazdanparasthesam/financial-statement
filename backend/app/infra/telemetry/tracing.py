"""OpenTelemetry tracing + OTLP log export. Opt-in via OTEL_ENABLED=true.

With OTEL_ENABLED unset (tests, CI, bare dev) nothing is exported and no
background threads start — the app behaves exactly as before.

Telemetry privacy (security/telemetry-policy.md): spans carry route TEMPLATES
(/api/filings/{filing_id}/...), HTTP status and timing only — never bodies,
tokens, emails, national ids or account names.
"""
import os

TRACING_ENABLED = os.environ.get("OTEL_ENABLED", "").strip().lower() in ("1", "true", "yes")
_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
_initialized = False


def current_trace_id() -> str:
    """32-hex trace id of the active span, or '' when tracing is off/absent."""
    try:
        from opentelemetry import trace
        ctx = trace.get_current_span().get_span_context()
        if ctx is not None and ctx.trace_id:
            return format(ctx.trace_id, "032x")
    except Exception:  # noqa: BLE001 — telemetry must never break a request
        pass
    return ""


def init_telemetry(service_name: str = "financial-statement-backend",
                   environment: str = "dev") -> dict:
    """Initialise TracerProvider + LoggerProvider with OTLP/gRPC exporters.

    Returns a status dict (logged at startup) — safe to call once per process.
    """
    global _initialized
    if not TRACING_ENABLED:
        return {"tracing": False, "otlp_logs": False,
                "reason": "OTEL_ENABLED not set — telemetry disabled (zero exporters)"}
    if _initialized:
        return {"tracing": True, "otlp_logs": True, "reason": "already initialised"}

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", service_name),
        "deployment.environment": os.environ.get("OTEL_ENVIRONMENT", environment),
    })

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=_OTLP_ENDPOINT, insecure=True)))
    trace.set_tracer_provider(tracer_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=_OTLP_ENDPOINT, insecure=True)))

    from .logging_conf import attach_otlp_handler
    attach_otlp_handler(logger_provider)

    _initialized = True
    return {"tracing": True, "otlp_logs": True, "endpoint": _OTLP_ENDPOINT}


def _privacy_server_request_hook(span, scope) -> None:
    """Remove raw URL paths/queries from spans before export (identifiers stay private).

    FastAPI's default span name and `http.route` are route templates. The ASGI
    semantic-convention attributes `http.target`, `url.path`, `url.full` and
    `http.url` can contain concrete resource ids or query strings, so overwrite
    them before the request runs. No headers are captured.
    """
    if not span.is_recording():
        return
    for key in (
        "http.target", "url.path", "url.full", "http.url", "url.query", "http.query",
        "http.client_ip", "client.address", "network.peer.address", "client.port",
        "network.peer.port", "http.user_agent", "user_agent.original",
    ):
        span.set_attribute(key, "[REDACTED]")


def instrument_app(app) -> None:
    """Attach FastAPI spans; only route templates survive the privacy hook."""
    if not TRACING_ENABLED:
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(
        app, excluded_urls="metrics,healthz",
        server_request_hook=_privacy_server_request_hook,
    )
