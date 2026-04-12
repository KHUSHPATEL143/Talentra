"""Middleware for tracking HTTP request metrics."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.metrics import record_api_request


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Capture request totals by route, method, and response status."""

    async def dispatch(self, request: Request, call_next):
        """Execute the downstream app and emit a Prometheus counter."""

        try:
            response = await call_next(request)
        except Exception:
            record_api_request(request.url.path, request.method.upper(), 500)
            raise

        record_api_request(request.url.path, request.method.upper(), response.status_code)
        return response
