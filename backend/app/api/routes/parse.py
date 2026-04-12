"""Resume parsing routes."""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb_client import get_candidate_collection
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, get_session
from app.core.redis_client import get_redis
from app.models.db import Candidate, ExecutionTrace, utcnow
from app.models.db_v3 import CandidateApplication, JobPosting
from app.models.schemas import BatchJobFileResult, ErrorResponse, JobStatusResponse, ParseResponse
from app.models.schemas_v3 import RankedCandidate

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


def _create_batch_file_result(file_name: str, job_id: str) -> BatchJobFileResult:
    """Create the initial queued status payload for one batch file."""

    return BatchJobFileResult(
        file_name=file_name or "Unnamed file",
        job_id=job_id,
        status="queued",
    )


def _merge_batch_file_result(
    entries: list[BatchJobFileResult],
    job_id: str,
    **updates: Any,
) -> list[BatchJobFileResult]:
    """Return updated batch entries with one file status merged in."""

    merged: list[BatchJobFileResult] = []
    for entry in entries:
        if entry.job_id == job_id:
            payload = entry.model_dump()
            payload.update(updates)
            merged.append(BatchJobFileResult.model_validate(payload))
        else:
            merged.append(entry)
    return merged


async def _load_batch_file_results(redis, batch_id: str) -> list[BatchJobFileResult]:
    """Load per-file batch statuses from Redis."""

    raw_value = await redis.get(f"job:{batch_id}:results")
    if not raw_value:
        return []
    return [BatchJobFileResult.model_validate(item) for item in json.loads(raw_value)]


async def _save_batch_file_results(redis, batch_id: str, entries: list[BatchJobFileResult]) -> None:
    """Persist per-file batch statuses to Redis."""

    await redis.set(
        f"job:{batch_id}:results",
        json.dumps([entry.model_dump() for entry in entries]),
    )


async def _update_batch_file_result(redis, batch_id: str, job_id: str, **updates: Any) -> list[BatchJobFileResult]:
    """Apply one per-file status update and persist the batch payload."""

    entries = await _load_batch_file_results(redis, batch_id)
    updated_entries = _merge_batch_file_result(entries, job_id, **updates)
    await _save_batch_file_results(redis, batch_id, updated_entries)
    return updated_entries


async def _enqueue_dead_letter(redis, batch_id: str, payload: dict[str, Any], error_message: str) -> None:
    """Persist a failed batch payload for later inspection or replay."""

    await redis.rpush(
        f"job:{batch_id}:dead_letter",
        json.dumps(
            {
                "file_name": payload.get("file_name"),
                "file_job_id": payload.get("file_job_id"),
                "mime_type": payload.get("mime_type"),
                "file_bytes": payload.get("file_bytes"),
                "error": error_message,
            }
        ),
    )


async def _drain_batch_queue(redis, batch_id: str, total_count: int) -> list[dict[str, Any]]:
    """Read every queued batch payload from Redis before concurrent processing starts."""

    payloads: list[dict[str, Any]] = []
    for _ in range(total_count):
        item = await redis.brpop(f"jobs:{batch_id}", timeout=5)
        if not item:
            continue
        _, raw_payload = item
        payloads.append(json.loads(raw_payload))
    return payloads


async def _process_batch_payload(app, redis, batch_id: str, payload: dict[str, Any]) -> None:
    """Process one batch file end to end and persist its per-file status."""

    file_bytes = base64.b64decode(payload["file_bytes"])
    await _update_batch_file_result(redis, batch_id, payload["file_job_id"], status="processing", error=None)

    try:
        async with AsyncSessionFactory() as session:
            state = await app.state.orchestrator.run(
                session=session,
                file_bytes=file_bytes,
                mime_type=payload["mime_type"],
                job_id=payload["file_job_id"],
            )
            if not state.get("parsed_profile"):
                raise ValueError(_extract_failure_message(state))

            candidate = await _persist_candidate(session, payload["mime_type"], state)
            recruiter_job_id = payload.get("recruiter_job_id")
            if recruiter_job_id:
                await _attach_candidate_to_recruiter_job(
                    app=app,
                    session=session,
                    recruiter_job_id=recruiter_job_id,
                    candidate=candidate,
                )
            await _cache_candidate(redis, candidate)
            await _upsert_candidate_embedding(candidate)
            await _update_batch_file_result(
                redis,
                batch_id,
                payload["file_job_id"],
                status="partial" if state.get("partial", False) else "done",
                candidate_id=candidate.id,
                partial=state.get("partial", False),
                error=None,
            )
    except Exception as exc:
        error_message = str(exc)
        await _enqueue_dead_letter(redis, batch_id, payload, error_message)
        await _update_batch_file_result(
            redis,
            batch_id,
            payload["file_job_id"],
            status="failed",
            candidate_id=None,
            partial=False,
            error=error_message,
        )
        await redis.rpush(f"job:{batch_id}:errors", error_message)
    finally:
        await redis.incr(f"job:{batch_id}:completed_count")


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
    if not candidate_payload:
        raise ValueError("Cannot persist candidate because parsed_profile is missing.")
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


async def _build_parsed_candidate_context(app, candidate: Candidate):
    """Create a RoleMatcher candidate context from a parsed resume record."""

    candidate_profile = candidate.profile_json.get("candidate_profile", {})
    skill_profile = candidate.profile_json.get("skill_profile", {})
    location = candidate_profile.get("location", {})
    location_label = ", ".join(part for part in [location.get("city", ""), location.get("country", "")] if part)
    coordinates = await app.state.geocoding_service.geocode(location_label) if location_label else None
    normalized_skills = list(skill_profile.get("normalized_skills", []))
    verified_skills = [
        {
            "canonical_name": item.get("name", ""),
            "verification_tier": "SELF_DECLARED",
            "years": float(item.get("years_experience", 0.0) or 0.0),
            "proficiency": item.get("proficiency", "intermediate"),
        }
        for item in normalized_skills
        if item.get("name")
    ]
    return app.state.role_matcher.build_candidate_context(
        candidate_id=candidate.id,
        employee_id=None,
        name=candidate.name,
        location_label=location_label,
        coordinates=coordinates,
        open_to_relocation=False,
        verified_skills=verified_skills,
        total_years=float(skill_profile.get("total_experience_years", 0.0) or 0.0),
        projects=list(candidate_profile.get("projects", [])),
    )


def _fallback_candidate_ranking(candidate: Candidate, job: JobPosting) -> RankedCandidate:
    """Return a recruiter-visible fallback ranking when a parsed resume misses the job filters."""

    candidate_profile = candidate.profile_json.get("candidate_profile", {})
    skill_profile = candidate.profile_json.get("skill_profile", {})
    location = candidate_profile.get("location", {})
    location_label = ", ".join(part for part in [location.get("city", ""), location.get("country", "")] if part)
    top_skills = [item.get("name", "") for item in list(skill_profile.get("normalized_skills", []))[:3] if item.get("name")]
    return RankedCandidate(
        candidate_id=candidate.id,
        job_id=job.id,
        final_score=0.0,
        grade="F",
        location_status="remote" if job.remote else "local",
        distance_km=None,
        pipeline_stage="new",
        candidate_name=candidate.name,
        location_label=location_label,
        top_skills=top_skills,
        verification_score=0.0,
        skill_breakdown=[],
        missing_required=[item.get("skill", "") for item in (job.required_skills or []) if item.get("skill")],
        strongest_projects=[],
        score_breakdown={
            "skill_score": 0.0,
            "experience_score": 0.0,
            "project_score": 0.0,
            "verification_score": 0.0,
        },
        recommendation="Resume uploaded successfully, but the current profile does not yet meet the role filters strongly enough for a positive match score.",
    )


async def _attach_candidate_to_recruiter_job(app, session: AsyncSession, recruiter_job_id: str, candidate: Candidate) -> None:
    """Attach a parsed resume candidate to a recruiter job as a resume-upload pipeline row."""

    job = await session.scalar(select(JobPosting).where(JobPosting.id == recruiter_job_id))
    if job is None:
        return

    candidate_context = await _build_parsed_candidate_context(app, candidate)
    ranking = await app.state.role_matcher.score_candidate_for_job(job, candidate_context)
    if ranking is None:
        ranking = _fallback_candidate_ranking(candidate, job)

    application = await session.scalar(
        select(CandidateApplication).where(
            CandidateApplication.job_id == recruiter_job_id,
            CandidateApplication.candidate_id == candidate.id,
        )
    )
    pipeline_stage = "shortlisted" if ranking.final_score >= job.auto_shortlist_threshold else (application.pipeline_stage if application else "new")
    candidate_data = {
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "candidate_email": candidate.email,
        "source_format": candidate.source_format,
    }
    if application is None:
        session.add(
            CandidateApplication(
                candidate_id=candidate.id,
                employee_id=None,
                job_id=recruiter_job_id,
                source="resume_upload",
                candidate_data=candidate_data,
                match_result=ranking.model_dump(),
                final_score=ranking.final_score,
                pipeline_stage=pipeline_stage,
            )
        )
    else:
        application.candidate_data = candidate_data
        application.match_result = ranking.model_dump()
        application.final_score = ranking.final_score
        application.pipeline_stage = pipeline_stage
        application.updated_at = utcnow()
    await session.commit()


async def _cache_candidate(redis, candidate: Candidate) -> None:
    """Store the persisted candidate in Redis for one hour."""

    await redis.setex(f"candidate:{candidate.id}:cache", settings.redis_cache_ttl_seconds, json.dumps(candidate.profile_json))


async def _upsert_candidate_embedding(candidate: Candidate) -> None:
    """Persist a candidate embedding in the dedicated Chroma collection."""

    skill_profile = candidate.profile_json.get("skill_profile", {})
    embedding_vector = skill_profile.get("embedding_vector") or []
    if not embedding_vector:
        return

    collection = get_candidate_collection()
    collection.upsert(
        ids=[candidate.id],
        embeddings=[embedding_vector],
        metadatas=[{"name": candidate.name, "source_format": candidate.source_format}],
        documents=[candidate.profile_json.get("candidate_profile", {}).get("summary") or candidate.name or candidate.id],
    )


def _extract_failure_message(state: dict[str, Any]) -> str:
    """Return the most relevant orchestrator error message."""

    errors = state.get("errors", [])
    if errors:
        return errors[-1]
    traces = state.get("traces", [])
    for trace in reversed(traces):
        if trace.get("error"):
            return str(trace["error"])
    return "Resume parsing failed before a candidate profile could be created."


async def _consume_batch_queue(app, batch_id: str) -> None:
    """Consume a Redis queue for batch parsing and update status keys."""

    redis = await get_redis()
    total_count = int(await redis.get(f"job:{batch_id}:total_count") or 0)
    await redis.set(f"job:{batch_id}:status", "processing")
    payloads = await _drain_batch_queue(redis, batch_id, total_count)
    semaphore = asyncio.Semaphore(settings.max_workers)

    async def _runner(payload: dict[str, Any]) -> None:
        async with semaphore:
            await _process_batch_payload(app, redis, batch_id, payload)

    await asyncio.gather(*(_runner(payload) for payload in payloads))

    results = await _load_batch_file_results(redis, batch_id)
    errors = [entry.error for entry in results if entry.error]
    overall_status = "failed" if any(entry.status == "failed" for entry in results) else "done"
    await redis.set(f"job:{batch_id}:status", overall_status)

    async with AsyncSessionFactory() as session:
        await app.state.webhook_service.dispatch_event(
            session=session,
            event_name="batch.complete",
            payload={
                "job_id": batch_id,
                "completed_count": int(await redis.get(f"job:{batch_id}:completed_count") or 0),
                "total_count": total_count,
                "errors": errors,
                "results": [entry.model_dump() for entry in results],
            },
        )


async def queue_batch_parse_job(
    *,
    redis,
    files: list[UploadFile],
    recruiter_job_id: str | None = None,
) -> JobStatusResponse:
    """Queue a Redis-backed batch parse job, optionally tied to a recruiter job."""

    if len(files) > settings.max_batch_files:
        raise _structured_http_error(400, "batch_too_large", f"Batch size exceeds the maximum of {settings.max_batch_files}.")

    batch_id = str(uuid.uuid4())
    await redis.set(f"job:{batch_id}:status", "queued")
    await redis.set(f"job:{batch_id}:completed_count", 0)
    await redis.set(f"job:{batch_id}:total_count", len(files))
    await redis.delete(f"job:{batch_id}:results")
    await redis.delete(f"job:{batch_id}:errors")
    await redis.delete(f"job:{batch_id}:dead_letter")

    queued_entries: list[BatchJobFileResult] = []
    for file in files:
        file_bytes, mime_type = await _read_and_validate_file(file)
        file_job_id = str(uuid.uuid4())
        payload = {
            "file_name": file.filename,
            "mime_type": mime_type,
            "file_job_id": file_job_id,
            "file_bytes": base64.b64encode(file_bytes).decode("utf-8"),
        }
        if recruiter_job_id:
            payload["recruiter_job_id"] = recruiter_job_id
        queued_entries.append(_create_batch_file_result(file.filename or "Unnamed file", file_job_id))
        await redis.lpush(f"jobs:{batch_id}", json.dumps(payload))

    await _save_batch_file_results(redis, batch_id, queued_entries)
    return JobStatusResponse(
        job_id=batch_id,
        status="queued",
        file_count=len(files),
        completed_count=0,
        total_count=len(files),
        results=queued_entries,
        errors=[],
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
    if not state.get("parsed_profile"):
        raise _structured_http_error(
            502,
            "parse_pipeline_failed",
            _extract_failure_message(state),
            partial_result={
                "job_id": state.get("job_id"),
                "traces": state.get("traces", []),
                "errors": state.get("errors", []),
                "partial": state.get("partial", True),
            },
        )
    candidate = await _persist_candidate(session, mime_type, state)
    redis = await get_redis()
    await _cache_candidate(redis, candidate)
    await _upsert_candidate_embedding(candidate)
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

    redis = await get_redis()
    response = await queue_batch_parse_job(redis=redis, files=files)
    background_tasks.add_task(_consume_batch_queue, request.app, response.job_id)
    return response
