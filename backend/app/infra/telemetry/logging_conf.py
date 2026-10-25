"""Structured JSON logging + an OTLP log bridge, both carrying the trace id.

Console handler  → one JSON object per line (docker logs, CI output, humans).
OTLP handler     → same JSON body shipped to the collector → Loki → Grafana,
                   with native OTLP trace_id/span_id fields for correlation.

Privacy: only method, ROUTE TEMPLATE, status, duration and rule ids are logged.
Never bodies, tokens, emails, national ids, account names or file contents
(security/telemetry-policy.md).
"""
import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

_SEVERITY = {  # python level → OTel SeverityNumber
    "DEBUG": 5, "INFO": 9, "WARNING": 13, "ERROR": 17, "CRITICAL": 21,
}
_SKIP_PATHS = ("/metrics",)


class JsonFormatter(logging.Formatter):
    """One JSON object per log line, with trace_id when a span is active."""

    def format(self, record: logging.LogRecord) -> str:
        from .tracing import current_trace_id
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = getattr(record, "trace_id", "") or current_trace_id()
        if trace_id:
            payload["trace_id"] = trace_id
        for key in ("method", "route", "status", "duration_ms", "step", "rule_id"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class OtlpLogHandler(logging.Handler):
    """Bridge python logging → OTLP logs (body = the same JSON line)."""

    def __init__(self, logger_provider):
        super().__init__()
        self._logger = logger_provider.get_logger("financial-statement")
        self._formatter = JsonFormatter()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from opentelemetry import trace
            from opentelemetry._logs import LogRecord, SeverityNumber

            span_context = trace.get_current_span().get_span_context()
            self._logger.emit(LogRecord(
                timestamp=int(record.created * 1e9),
                severity_number=SeverityNumber(_SEVERITY.get(record.levelname, 9)),
                severity_text=record.levelname,
                body=self._formatter.format(record),
                trace_id=span_context.trace_id if span_context.is_valid else 0,
                span_id=span_context.span_id if span_context.is_valid else 0,
                trace_flags=span_context.trace_flags if span_context.is_valid else None,
                attributes={"logger.name": record.name},
            ))
        except Exception:  # noqa: BLE001 — logging must never break a request
            self.handleError(record)


def attach_otlp_handler(logger_provider) -> None:
    logging.getLogger().addHandler(OtlpLogHandler(logger_provider))


def configure_logging(level: str = "INFO") -> None:
    """JSON logs for everything: route uvicorn's loggers through the root handler.

    uvicorn.access is disabled on purpose — RequestLogMiddleware already logs
    one structured line per request (route TEMPLATE, never raw paths with ids
    beyond what the template shows, status, duration)."""
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(h, "_fs_json", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler._fs_json = True  # type: ignore[attr-defined]
        root.handlers[:] = [handler]
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
    logging.getLogger("uvicorn.access").disabled = True


class RequestLogMiddleware(BaseHTTPMiddleware):
    """One structured log line per request: method, route template, status, ms."""

    async def dispatch(self, request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        path = request.url.path
        if path not in _SKIP_PATHS:
            route = path
            if request.scope.get("route") is not None:
                route = getattr(request.scope["route"], "path", path)
            logging.getLogger("fs.http").info(
                "http_request",
                extra={"method": request.method, "route": route,
                       "status": response.status_code,
                       "duration_ms": round((time.monotonic() - started) * 1000, 1)},
            )
        return response
