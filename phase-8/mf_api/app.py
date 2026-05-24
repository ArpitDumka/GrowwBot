"""FastAPI application factory (§8 — backend for UI)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from mf_api.bootstrap import load_bootstrap
from mf_api.config import load_api_config
from mf_api.metrics import MetricsRegistry
from mf_api.rate_limit import RateLimiter
from mf_api.schemas import BootstrapResponse, ChatRequest, ChatResponse, HealthResponse, InsightsResponse
from mf_api.service import run_chat
from mf_insights.loader import load_insights

log = logging.getLogger(__name__)
TRACE_HEADER = "x-trace-id"


def create_app(
    *,
    test_embedder: bool = False,
    test_reranker: bool = False,
    llm: Any = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    cfg = load_api_config()
    bootstrap = load_bootstrap()
    limiter = rate_limiter
    if limiter is None and cfg.rate_limit_enabled:
        limiter = RateLimiter(requests_per_minute=cfg.rate_limit_rpm)

    app = FastAPI(
        title=cfg.title,
        version=cfg.version,
        description="Facts-only mutual fund FAQ API. Queries use POST only (edge 8.12).",
    )
    app.state.test_embedder = test_embedder
    app.state.test_reranker = test_reranker
    app.state.llm = llm
    app.state.api_config = cfg
    app.state.rate_limiter = limiter
    app.state.metrics = MetricsRegistry()

    @app.on_event("startup")
    async def _warm_pipeline() -> None:
        """Preload embedder + index so the first /chat call is fast (cold-start fix)."""
        try:
            from mf_compose.pipeline import _cached_index, ensure_paths, load_env  # noqa: PLC0415

            load_env()
            ensure_paths()
            log.info("Warming retrieval pipeline (embedder + index)...")
            _cached_index(test_embedder=test_embedder)
            log.info("Pipeline warm. First /chat will be fast.")
        except Exception as exc:  # noqa: BLE001
            log.warning("Pipeline warmup failed (will lazy-load on first request): %s", exc)

    if cfg.cors_origins or cfg.cors_origin_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cfg.cors_origins),
            allow_origin_regex=cfg.cors_origin_regex,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.get("/")
    async def root() -> dict:
        return {
            "service": cfg.title,
            "version": cfg.version,
            "status": "running",
            "role": "backend",
            "endpoints": {
                "health":    "/healthz",
                "warmup":    "/warmup",
                "bootstrap": "/api/v1/bootstrap",
                "insights":  "/api/v1/insights",
                "chat":      "/api/v1/chat  (POST, body: {\"query\": \"...\"})",
                "metrics":   "/metrics",
                "swagger":   "/docs",
                "openapi":   "/openapi.json",
            },
            "frontend": f"Next.js UI: {cfg.frontend_url}",
        }

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        return HealthResponse(version=cfg.version)

    @app.get("/warmup")
    async def warmup() -> dict[str, str]:
        """Load embedder + index (call from UI after healthz to cut first-chat latency)."""
        from mf_compose.pipeline import _cached_index, ensure_paths, load_env  # noqa: PLC0415

        load_env()
        ensure_paths()
        _cached_index(test_embedder=test_embedder)
        return {"status": "warm"}

    @app.get("/api/v1/bootstrap", response_model=BootstrapResponse)
    async def bootstrap_route() -> BootstrapResponse:
        return BootstrapResponse(**bootstrap.to_dict())

    @app.get("/api/v1/insights", response_model=InsightsResponse)
    async def insights_route() -> InsightsResponse:
        payload = load_insights()
        return InsightsResponse(**payload)

    @app.post("/api/v1/chat", response_model=ChatResponse)
    async def chat_route(request: Request, body: ChatRequest) -> Response:
        query = body.query.strip()
        if len(query) < cfg.min_query_length:
            return JSONResponse(
                status_code=422,
                content={"detail": f"query must be at least {cfg.min_query_length} characters"},
            )
        if len(query) > cfg.max_query_length:
            return JSONResponse(
                status_code=422,
                content={"detail": f"query must be at most {cfg.max_query_length} characters"},
            )

        client_host = request.client.host if request.client else "unknown"
        if app.state.rate_limiter is not None:
            allowed, retry = app.state.rate_limiter.allow(client_host)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again shortly."},
                    headers={"Retry-After": str(retry)},
                )

        trace_id = request.headers.get(TRACE_HEADER) or str(uuid.uuid4())
        response, log_payload = run_chat(
            query,
            trace_id=trace_id,
            prior_user_query=body.prior_user_query,
            prior_assistant_answer=body.prior_assistant_answer,
            test_embedder=app.state.test_embedder,
            test_reranker=app.state.test_reranker,
            llm=app.state.llm,
        )
        app.state.metrics.observe_chat(log_payload)
        return JSONResponse(
            content=response.model_dump(),
            headers={TRACE_HEADER: response.trace_id},
        )

    @app.get("/metrics")
    async def metrics_route() -> Response:
        return Response(app.state.metrics.render_prometheus(), media_type="text/plain; version=0.0.4")

    return app
