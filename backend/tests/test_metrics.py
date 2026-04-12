"""Observability tests for Prometheus metrics support."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
from fastapi.testclient import TestClient

from app.api.middleware.auth import ApiKeyAuthMiddleware
from app.api.middleware.request_metrics import RequestMetricsMiddleware
from app.utils.metrics import export_metrics


def test_request_metrics_middleware_records_http_requests() -> None:
    """Serving a route should increment the API request counter with labels."""

    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware)

    @app.get("/observability-check")
    async def observability_check() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/observability-check")

    assert response.status_code == 200
    payload, content_type = export_metrics()
    metrics_text = payload.decode("utf-8")
    assert content_type.startswith("text/plain")
    assert "garuda_api_requests_total" in metrics_text
    assert 'route="/observability-check"' in metrics_text
    assert 'method="GET"' in metrics_text
    assert 'status_code="200"} 1.0' in metrics_text


def test_metrics_path_bypasses_api_key_authentication() -> None:
    """Prometheus scrapes should remain available without an API key."""

    app = FastAPI()
    app.add_middleware(ApiKeyAuthMiddleware)

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = export_metrics()
        return Response(content=payload, media_type=content_type)

    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "garuda_api_requests_total" in response.text


def test_non_metrics_path_still_requires_api_key() -> None:
    """The authentication bypass must stay limited to the metrics endpoint."""

    app = FastAPI()
    app.add_middleware(ApiKeyAuthMiddleware)

    @app.get("/secure-health")
    async def secure_health() -> PlainTextResponse:
        return PlainTextResponse("ok")

    client = TestClient(app)

    response = client.get("/secure-health")

    assert response.status_code == 401
