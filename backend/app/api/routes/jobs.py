"""Batch job status routes."""

from __future__ import annotations

import json

from fastapi import APIRouter

from app.core.redis_client import get_redis
from app.models.schemas import JobStatusResponse

router = APIRouter(tags=["Jobs"])


@router.get(
    "/jobs/{job_id}/status",
    summary="Get batch job status",
    description="Read a batch parsing job status and current results from Redis.",
    response_model=JobStatusResponse,
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Return the live status of a batch parsing job."""

    redis = await get_redis()
    status = await redis.get(f"job:{job_id}:status") or "pending"
    completed_count = int(await redis.get(f"job:{job_id}:completed_count") or 0)
    total_count = int(await redis.get(f"job:{job_id}:total_count") or 0)
    results = [json.loads(item) for item in await redis.lrange(f"job:{job_id}:results", 0, -1)]
    errors = await redis.lrange(f"job:{job_id}:errors", 0, -1)
    return JobStatusResponse(
        job_id=job_id,
        status=status,  # type: ignore[arg-type]
        file_count=total_count,
        completed_count=completed_count,
        total_count=total_count,
        results=results,
        errors=errors,
    )
