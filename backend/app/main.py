"""FastAPI application factory and startup wiring."""

from __future__ import annotations

import hashlib
import logging
import sys
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select

from app.agents.matching_agent import MatchingAgent
from app.agents.normalization_agent import NormalizationAgent
from app.agents.orchestrator import ResumeOrchestrator
from app.agents.parsing_agent import ParsingAgent
from app.agents.job_posting_agent import JobPostingAgent
from app.agents.role_matcher import RoleMatcher
from app.api.middleware.auth import ApiKeyAuthMiddleware
from app.api.middleware.request_metrics import RequestMetricsMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.routes import auth_v3, candidates, employees_v3, jobs, jobs_v3, match, parse, taxonomy, webhooks
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, init_database
from app.models.db import ApiKey
from app.models.schemas import ErrorResponse
from app.services.geocoding_service import GeocodingService
from app.services.embedding_service import EmbeddingService
from app.services.file_parser import FileParserService
from app.services.job_heuristics import JobHeuristicService
from app.services.llm_service import LLMService
from app.services.resume_heuristics import ResumeHeuristicService
from app.services.taxonomy_service import TaxonomyService
from app.services.webhook_service import WebhookService
from app.utils.metrics import export_metrics
from app.utils.skill_inference import SkillInferenceEngine

settings = get_settings()


def configure_logging() -> None:
    """Configure structlog for console-friendly JSON logging."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=settings.log_level.upper())


async def seed_default_api_key() -> None:
    """Ensure a development API key exists and print the usable raw key."""

    async with AsyncSessionFactory() as session:
        configured_key = settings.default_api_key.strip()
        if configured_key:
            configured_hash = hashlib.sha256(configured_key.encode("utf-8")).hexdigest()
            existing = await session.scalar(select(ApiKey).where(ApiKey.key_hash == configured_hash))
            if existing is None:
                session.add(
                    ApiKey(
                        key_hash=configured_hash,
                        owner=settings.default_api_key_owner,
                        rate_limit_per_min=settings.rate_limit_per_min,
                    )
                )
                await session.commit()
            print(f"DEV API KEY: {configured_key}")
            return

        count = await session.scalar(select(func.count()).select_from(ApiKey))
        if count and count > 0:
            return

        raw_key = str(uuid.uuid4())
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        record = ApiKey(
            key_hash=key_hash,
            owner=settings.default_api_key_owner,
            rate_limit_per_min=settings.rate_limit_per_min,
        )
        session.add(record)
        await session.commit()
        print(f"DEV API KEY: {raw_key}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize infrastructure, services, and seed data."""

    configure_logging()
    await init_database()

    embedding_service = EmbeddingService()
    llm_service = LLMService()
    file_parser = FileParserService()
    heuristic_service = ResumeHeuristicService()
    taxonomy_service = TaxonomyService(embedding_service=embedding_service, llm_service=llm_service)
    geocoding_service = GeocodingService()
    job_heuristic_service = JobHeuristicService([entry["canonical_name"] for entry in taxonomy_service.taxonomy_entries])
    inference_engine = SkillInferenceEngine.from_yaml(settings.resolved_inference_rules_path)
    parsing_agent = ParsingAgent(file_parser=file_parser, llm_service=llm_service, heuristic_service=heuristic_service)
    normalization_agent = NormalizationAgent(taxonomy_service=taxonomy_service, inference_engine=inference_engine)
    job_posting_agent = JobPostingAgent(
        llm_service=llm_service,
        taxonomy_service=taxonomy_service,
        geocoding_service=geocoding_service,
    )
    matching_agent = MatchingAgent(
        embedding_service=embedding_service,
        llm_service=llm_service,
        job_heuristic_service=job_heuristic_service,
    )
    role_matcher = RoleMatcher(
        embedding_service=embedding_service,
        geocoding_service=geocoding_service,
    )
    orchestrator = ResumeOrchestrator(
        parsing_agent=parsing_agent,
        normalization_agent=normalization_agent,
        matching_agent=matching_agent,
        embedding_service=embedding_service,
    )
    webhook_service = WebhookService()

    async with AsyncSessionFactory() as session:
        await taxonomy_service.seed_taxonomy(session)
    await seed_default_api_key()

    app.state.embedding_service = embedding_service
    app.state.llm_service = llm_service
    app.state.file_parser = file_parser
    app.state.heuristic_service = heuristic_service
    app.state.job_heuristic_service = job_heuristic_service
    app.state.taxonomy_service = taxonomy_service
    app.state.geocoding_service = geocoding_service
    app.state.inference_engine = inference_engine
    app.state.parsing_agent = parsing_agent
    app.state.normalization_agent = normalization_agent
    app.state.job_posting_agent = job_posting_agent
    app.state.matching_agent = matching_agent
    app.state.role_matcher = role_matcher
    app.state.orchestrator = orchestrator
    app.state.webhook_service = webhook_service
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ApiKeyAuthMiddleware)
    app.add_middleware(RequestMetricsMiddleware)

    app.include_router(parse.router, prefix=settings.api_v1_prefix)
    app.include_router(candidates.router, prefix=settings.api_v1_prefix)
    app.include_router(match.router, prefix=settings.api_v1_prefix)
    app.include_router(taxonomy.router, prefix=settings.api_v1_prefix)
    app.include_router(jobs.router, prefix=settings.api_v1_prefix)
    app.include_router(webhooks.router, prefix=settings.api_v1_prefix)
    app.include_router(auth_v3.router, prefix=settings.api_v1_prefix)
    app.include_router(jobs_v3.router, prefix=settings.api_v1_prefix)
    app.include_router(employees_v3.router, prefix=settings.api_v1_prefix)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Expose Prometheus-compatible counters and histograms."""

        payload, content_type = export_metrics()
        return Response(content=payload, media_type=content_type)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        """Return structured HTTP error responses."""

        detail = exc.detail if isinstance(exc.detail, dict) else {"error": "http_error", "message": str(exc.detail)}
        body = ErrorResponse(
            error=detail.get("error", "http_error"),
            message=detail.get("message", "Request failed."),
            trace_id=detail.get("trace_id", str(uuid.uuid4())),
            partial_result=detail.get("partial_result"),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Return structured validation error responses."""

        body = ErrorResponse(
            error="validation_error",
            message=str(exc),
            trace_id=str(uuid.uuid4()),
            partial_result=None,
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Return structured internal error responses."""

        body = ErrorResponse(
            error="internal_server_error",
            message=str(exc),
            trace_id=str(uuid.uuid4()),
            partial_result=None,
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
