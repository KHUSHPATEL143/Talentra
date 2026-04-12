"""Prometheus metrics helpers."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

AGENT_RUNS = Counter(
    "garuda_agent_runs_total",
    "Total number of agent executions.",
    ["agent_name", "status"],
)
AGENT_LATENCY = Histogram(
    "garuda_agent_latency_seconds",
    "Agent execution latency in seconds.",
    ["agent_name"],
)
API_REQUESTS = Counter(
    "garuda_api_requests_total",
    "Total API requests handled.",
    ["route", "method", "status_code"],
)


def record_agent_run(agent_name: str, status: str, latency_seconds: float) -> None:
    """Record agent execution metrics."""

    AGENT_RUNS.labels(agent_name=agent_name, status=status).inc()
    AGENT_LATENCY.labels(agent_name=agent_name).observe(latency_seconds)


def record_api_request(route: str, method: str, status_code: int) -> None:
    """Record API request metrics."""

    API_REQUESTS.labels(route=route, method=method, status_code=str(status_code)).inc()


def export_metrics() -> tuple[bytes, str]:
    """Render the current Prometheus registry into an HTTP response payload."""

    return generate_latest(), CONTENT_TYPE_LATEST
