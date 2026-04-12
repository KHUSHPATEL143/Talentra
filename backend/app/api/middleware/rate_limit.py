"""Redis-backed sliding window rate limiting middleware."""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.redis_client import redis_client
from app.models.schemas import ErrorResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-key request limits using a Redis sorted set."""

    async def dispatch(self, request: Request, call_next):
        """Reject requests that exceed the configured per-minute quota."""

        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        if request.url.path in {"/docs", "/openapi.json", "/redoc", "/metrics"}:
            return await call_next(request)

        api_key = getattr(request.state, "api_key", None)
        if not api_key:
            return await call_next(request)

        now = time.time()
        window_start = now - 60
        redis_key = f"ratelimit:{api_key['id']}"
        member = f"{now}:{request.url.path}"
        await redis_client.zremrangebyscore(redis_key, "-inf", window_start)
        await redis_client.zadd(redis_key, {member: now})
        current_count = await redis_client.zcard(redis_key)
        await redis_client.expire(redis_key, 60)

        if current_count > api_key["rate_limit_per_min"]:
            retry_after = 60
            response = JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error="rate_limit_exceeded",
                    message="Request limit exceeded for the current 60-second window.",
                    trace_id=request.headers.get("X-Trace-Id", "rate-limit"),
                ).model_dump(),
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        return await call_next(request)
