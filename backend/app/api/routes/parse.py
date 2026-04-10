"""Resume parsing routes."""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, get_session
from app.core.redis_client import get_redis
from app.models.db import Candidate, ExecutionTrace
from app.models.schemas import ErrorResponse, JobStatusResponse, ParseResponse

router = APIRouter(tags=["Parsing"])
settings = get_settings()

PARSE_RESPONSE_EXAMPLE = {
    "candidate_id": "e2fcb389-61ff-486b-8c2d-2429ec4db895",
    "candidate_profile": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1-555-1234",
        "location": {"city": "London", "country": "UK"},
        "linkedin": "https://linkedin.com/in/adalovelace",
        "summary": "Backend engineer focused on ML systems.",
        "skills": ["Python", "FastAPI"],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "publications": [],
    },
    "skill_profile": {"raw_skills": ["Python", "FastAPI"], "normalized_skills": [], "inferred_skills": [], "emerging_skills": [], "total_experience_years": 0.0, "embedding_vector": []},
    "traces": [{"agent": "parsing_agent", "latency_ms": 812, "quality_score": 0.91, "error": None}],
    "quality_score": 0.91,
    "partial": False,
}


def _structured_http_error(status_code: int, error: str, message: str, partial_result: dict[str, Any] | None = None) -> HTTPException:
    """Create a standardized HTTPException payload."""

    trace_id = str(uuid.uuid4())
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=error, message=message, trace_id=trace_id, partial_result=partial_result).model_dump(),
    )


async def _read_and_validate_file(file: UploadFile) -> tuple[bytes, str]:
    """Read an uploaded file and validate MIME type and file size."""

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_file_size_bytes:
        raise _structured_http_error(400, "file_too_large", f"{file.filename} exceeds the 10 MB limit.")
    mime_type = file.content_type or "application/octet-stream"
    valid_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    }
    if mime_type not in valid_types:
        raise _structured_http_error(400, "invalid_mime_type", f"{file.filename} has unsupported MIME type {mime_type}.")
    return file_bytes, mime_type


async def _persist_candidate(
    session: AsyncSession,
    mime_type: str,
    orchestrator_state: dict[str, Any],
) -> Candidate:
    """Persist candidate and agent traces after a parse pipeline run."""

    candidate_payload = orchestrator_state.get("parsed_profile", {})
    skill_payload = orchestrator_state.get("normalized_profile", {})
    traces = orchestrator_state.get("traces", [])
    candidate = Candidate(
        name=candidate_payload.get("name", ""),
        email=candidate_payload.get("email"),
        profile_json={
            "candidate_profile": candidate_payload,
            "skill_profile": skill_payload,
        },
        source_format=mime_type,
        quality_score=float(traces[0]["quality_score"]) if traces else 0.0,
    )
    session.add(candidate)
    await session.flush()

    for trace in traces:
        session.add(
            ExecutionTrace(
                job_id=orchestrator_state["job_id"],
                agent_name=trace["agent"],
                latency_ms=trace["latency_ms"],
                quality_score=trace.get("quality_score", 0.0),
                error=trace.get("error"),
            )
        )

    await session.commit()
    await session.refresh(candidate)
    return candidate


async def _cache_candidate(redis, candidate: Candidate) -> None:
    """Store the persisted candidate in Redis for one hour."""

    await redis.setex(f"candidate:{candidate.id}", settings.redis_cache_ttl_seconds, json.dumps(candidate.profile_json))


async def _consume_batch_queue(app, batch_id: str) -> None:
    """Consume a Redis queue for batch parsing and update status keys."""

    redis = await get_redis()
    total_count = int(await redis.get(f"job:{batch_id}:total_count") or 0)
    await redis.set(f"job:{batch_id}:status", "processing")

    for _ in range(total_count):
        item = await redis.brpop(f"jobs:{batch_id}", timeout=5)
        if not item:
            continue
        _, raw_payload = item
        payload = json.loads(raw_payload)
        file_bytes = base64.b64decode(payload["file_bytes"])
        async with AsyncSessionFactory() as session:
            try:
                state = await app.state.orchestrator.run(
                    session=session,
                    file_bytes=file_bytes,
                    mime_type=payload["mime_type"],
                    job_id=payload["file_job_id"],
                )
                candidate = await _persist_candidate(session, payload["mime_type"], state)
                result = {
                    "file_name": payload["file_name"],
                    "candidate_id": candidate.id,
                    "job_id": payload["file_job_id"],
                    "partial": state.get("partial", False),
                }
                await redis.rpush(f"job:{batch_id}:results", json.dumps(result))
                await redis.incr(f"job:{batch_id}:completed_count")
            except Exception as exc:
                await redis.rpush(f"job:{batch_id}:errors", str(exc))

    completed = int(await redis.get(f"job:{batch_id}:completed_count") or 0)
    errors = await redis.lrange(f"job:{batch_id}:errors", 0, -1)
    await redis.set(f"job:{batch_id}:status", "done" if completed == total_count and not errors else "failed")

    async with AsyncSessionFactory() as session:
        await app.state.webhook_service.dispatch_event(
            session=session,
            event_name="batch.complete",
            payload={
                "job_id": batch_id,
                "completed_count": completed,
                "total_count": total_count,
                "errors": errors,
            },
        )


@router.post(
    "/parse",
    summary="Parse a resume",
    description="Upload a single PDF, DOCX, or TXT resume and run the parsing plus normalization pipeline synchronously.",
    response_model=ParseResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    openapi_extra={"examples": {"default": {"summary": "Successful parse", "value": PARSE_RESPONSE_EXAMPLE}}},
)
async def parse_resume(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> ParseResponse:
    """Parse one uploaded resume and persist the result."""

    file_bytes, mime_type = await _read_and_validate_file(file)
    state = await request.app.state.orchestrator.run(session=session, file_bytes=file_bytes, mime_type=mime_type)
    candidate = await _persist_candidate(session, mime_type, state)
    redis = await get_redis()
    await _cache_candidate(redis, candidate)
    await request.app.state.webhook_service.dispatch_event(
        session=session,
        event_name="parse.complete",
        payload={"candidate_id": candidate.id, "job_id": state["job_id"]},
    )
    return ParseResponse(
        candidate_id=candidate.id,
        candidate_profile=state["parsed_profile"],
        skill_profile=state.get("normalized_profile", {}),
        traces=state.get("traces", []),
        quality_score=float(state.get("traces", [{}])[0].get("quality_score", 0.0)),
        partial=state.get("partial", False),
    )


@router.post(
    "/parse/batch",
    summary="Queue batch resume parsing",
    description="Upload up to 50 resumes, enqueue them in Redis, and process the batch asynchronously in the background.",
    response_model=JobStatusResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def parse_resume_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
) -> JobStatusResponse:
    """Queue a batch parsing job and start the background consumer."""

    if len(files) > settings.max_batch_files:
        raise _structured_http_error(400, "batch_too_large", f"Batch size exceeds the maximum of {settings.max_batch_files}.")

    redis = await get_redis()
    batch_id = str(uuid.uuid4())
    await redis.set(f"job:{batch_id}:status", "queued")
    await redis.set(f"job:{batch_id}:completed_count", 0)
    await redis.set(f"job:{batch_id}:total_count", len(files))
    await redis.delete(f"job:{batch_id}:results")
    await redis.delete(f"job:{batch_id}:errors")

    for file in files:
        file_bytes, mime_type = await _read_and_validate_file(file)
        payload = {
            "file_name": file.filename,
            "mime_type": mime_type,
            "file_job_id": str(uuid.uuid4()),
            "file_bytes": base64.b64encode(file_bytes).decode("utf-8"),
        }
        await redis.lpush(f"jobs:{batch_id}", json.dumps(payload))

    background_tasks.add_task(_consume_batch_queue, request.app, batch_id)
    return JobStatusResponse(job_id=batch_id, status="queued", completed_count=0, total_count=len(files), results=[], errors=[])
