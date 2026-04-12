"""Webhook delivery tests."""

from __future__ import annotations

import httpx
import pytest

from app.services.webhook_service import WebhookService


class FakeResponse:
    """Minimal response double for webhook delivery tests."""

    def __init__(self, should_raise: bool) -> None:
        """Store whether this response should behave like an HTTP failure."""

        self.should_raise = should_raise

    def raise_for_status(self) -> None:
        """Raise an HTTP status error when configured to fail."""

        if self.should_raise:
            raise httpx.HTTPStatusError("delivery failed", request=httpx.Request("POST", "http://example.com"), response=httpx.Response(500))


class FakeClient:
    """Minimal async client double that returns queued webhook outcomes."""

    def __init__(self, outcomes: list[bool]) -> None:
        """Store a sequence of failure flags for each POST attempt."""

        self.outcomes = outcomes
        self.calls = 0

    async def post(self, url: str, json: dict[str, object]) -> FakeResponse:
        """Return the next configured response outcome."""

        self.calls += 1
        should_raise = self.outcomes[min(self.calls - 1, len(self.outcomes) - 1)]
        return FakeResponse(should_raise=should_raise)


@pytest.mark.asyncio
async def test_webhook_delivery_retries_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Webhook delivery should retry transient failures and stop on success."""

    service = WebhookService()
    client = FakeClient([True, False])
    recorded_sleeps: list[int] = []

    async def fake_sleep(delay: int) -> None:
        recorded_sleeps.append(delay)

    monkeypatch.setattr("app.services.webhook_service.asyncio.sleep", fake_sleep)

    await service._deliver(client, "http://example.com/hook", "parse.complete", {"candidate_id": "123"})

    assert client.calls == 2
    assert recorded_sleeps == [1]


@pytest.mark.asyncio
async def test_webhook_delivery_gives_up_after_three_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Webhook delivery should stop retrying after the third failed attempt."""

    service = WebhookService()
    client = FakeClient([True, True, True])
    recorded_sleeps: list[int] = []

    async def fake_sleep(delay: int) -> None:
        recorded_sleeps.append(delay)

    monkeypatch.setattr("app.services.webhook_service.asyncio.sleep", fake_sleep)

    await service._deliver(client, "http://example.com/hook", "batch.complete", {"job_id": "abc"})

    assert client.calls == 3
    assert recorded_sleeps == [1, 2]
