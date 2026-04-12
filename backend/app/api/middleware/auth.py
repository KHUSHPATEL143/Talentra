"""API key authentication middleware."""

from __future__ import annotations

import hashlib

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.database import AsyncSessionFactory
from app.models.db import ApiKey
from app.models.schemas import ErrorResponse


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Validate incoming API keys against the database."""

    def __init__(self, app) -> None:
        """Initialize middleware with pass-through routes."""

        super().__init__(app)
        self.open_paths = {"/docs", "/openapi.json", "/redoc", "/api/v1/signup", "/api/v1/login"}

    async def dispatch(self, request: Request, call_next):
        """Authenticate the request and attach API key metadata to request state."""

        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        if request.url.path in self.open_paths:
            return await call_next(request)

        header_value = request.headers.get("X-API-Key")
        if not header_value:
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    error="missing_api_key",
                    message="X-API-Key header is required.",
                    trace_id=request.headers.get("X-Trace-Id", "auth-missing"),
                ).model_dump(),
            )

        key_hash = hashlib.sha256(header_value.encode("utf-8")).hexdigest()
        async with AsyncSessionFactory() as session:
            from sqlalchemy import select

            result = await session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
            record = result.scalar_one_or_none()

        if record is None:
            return JSONResponse(
                status_code=403,
                content=ErrorResponse(
                    error="invalid_api_key",
                    message="The supplied API key is not recognized.",
                    trace_id=request.headers.get("X-Trace-Id", "auth-invalid"),
                ).model_dump(),
            )

        request.state.api_key = {
            "id": record.id,
            "owner": record.owner,
            "rate_limit_per_min": record.rate_limit_per_min,
        }
        return await call_next(request)
