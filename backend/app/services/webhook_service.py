"""Webhook persistence and async delivery helpers."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.db import Webhook


class WebhookService:
    """Register and dispatch webhook events with retry handling."""

    def __init__(self) -> None:
        """Store timeout-related settings."""

        self.settings = get_settings()

    async def dispatch_event(self, session: AsyncSession, event_name: str, payload: dict[str, Any]) -> None:
        """Send an event payload to every subscribed webhook."""

        result = await session.execute(select(Webhook).where(Webhook.events.contains([event_name])))
        hooks = list(result.scalars().all())
        if not hooks:
            return

        async with httpx.AsyncClient(timeout=self.settings.webhook_timeout_seconds) as client:
            await asyncio.gather(*(self._deliver(client, hook.url, event_name, payload) for hook in hooks))

    async def _deliver(
        self,
        client: httpx.AsyncClient,
        url: str,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        """POST an event to a webhook endpoint with retries."""

        body = {"event": event_name, "payload": payload}
        for attempt in range(3):
            try:
                response = await client.post(url, json=body)
                response.raise_for_status()
                return
            except Exception:
                if attempt == 2:
                    return
                await asyncio.sleep(2**attempt)
