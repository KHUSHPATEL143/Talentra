"""Webhook registration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db import Webhook
from app.models.schemas import WebhookRegistrationRequest, WebhookRegistrationResponse

router = APIRouter(tags=["Webhooks"])


@router.post(
    "/webhooks",
    summary="Register a webhook",
    description="Store a webhook subscription for parse, match, or batch completion events.",
    response_model=WebhookRegistrationResponse,
)
async def register_webhook(
    request: Request,
    payload: WebhookRegistrationRequest,
    session: AsyncSession = Depends(get_session),
) -> WebhookRegistrationResponse:
    """Persist a webhook registration for the authenticated API key."""

    webhook = Webhook(url=str(payload.url), events=payload.events, owner_key_id=request.state.api_key["id"])
    session.add(webhook)
    await session.commit()
    await session.refresh(webhook)
    return WebhookRegistrationResponse(id=webhook.id, url=webhook.url, events=webhook.events)
