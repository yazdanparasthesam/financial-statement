"""Financial Statement API — FastAPI application factory.

Layer rules (enforced in review, see AGENTS.md):
  routers → services → domain (pure) / infra (IO)
The AI layer never computes figures; all arithmetic lives in app/domain.

Observability (docs/observability.md): structured JSON logs, OTel traces and
Prometheus metrics share one trace id per request. Export is opt-in via
OTEL_ENABLED; /metrics is always exposed for scraping.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .config import get_settings
from .db import init_db
from .infra.ingestion import IngestionError
from .infra.telemetry import RequestLogMiddleware, configure_logging, init_telemetry, instrument_app
from .routers import (
    ai,
    auth,
    companies,
    exports,
    filings,
    ops,
    statements,
    trial_balance,
    validations,
    workflow,
)

logger = logging.getLogger("fs.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("telemetry_status", extra={"step": "startup"})
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="Financial Statement API",
        version=s.version,
        description="AI-assisted financial statements & tax filing platform "
                    "(Iranian statutory context, English UI).",
        lifespan=lifespan,
    )
    origins = ["*"] if s.cors_origins.strip() == "*" else [
        o.strip() for o in s.cors_origins.split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["*"], allow_headers=["*"])

    # ---- observability: one trace id across logs, metrics exemplars and traces ----
    configure_logging()
    status = init_telemetry()  # OTEL_ENABLED / OTEL_ENVIRONMENT drive behaviour
    logger.info("telemetry initialised: %s", status)
    app.state.telemetry = status
    instrument_app(app)                                   # OTel server spans (opt-in)
    app.add_middleware(RequestLogMiddleware)              # structured request log
    Instrumentator(                                       # Prometheus /metrics
        should_group_status_codes=True,
        excluded_handlers=["/metrics", "/healthz"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    for r in (ops.router, auth.router, companies.router, filings.router,
              trial_balance.router, statements.router, validations.router,
              ai.router, workflow.router, exports.router):
        app.include_router(r)

    @app.exception_handler(IngestionError)
    async def _ingestion(_req: Request, exc: IngestionError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def _value_error(_req: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


app = create_app()
