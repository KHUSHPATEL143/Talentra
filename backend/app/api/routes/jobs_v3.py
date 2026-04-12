"""Recruiter job posting and pipeline routes for TalentOS v3."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb_client import get_job_collection
from app.core.database import get_session
from app.core.redis_client import get_redis
from app.api.routes.parse import _consume_batch_queue, queue_batch_parse_job
from app.models.db_v3 import CandidateApplication, JobPosting, Recruiter
from app.models.schemas import ErrorResponse, JobStatusResponse
from app.models.schemas_v3 import (
    CandidateStageUpdateRequest,
    CandidateStageUpdateResponse,
    JobPostingCreateRequest,
    JobPostingListResponse,
    JobPostingPatchRequest,
    JobPostingResponse,
    RankedCandidate,
    RankedCandidateListResponse,
    RunMatchingResponse,
)
from app.services.auth_service import require_recruiter

router = APIRouter(tags=["TalentOS Jobs"])


def _job_response(record: JobPosting) -> JobPostingResponse:
    """Convert a job ORM record into the API response shape."""

    return JobPostingResponse(
        id=record.id,
        recruiter_id=record.recruiter_id,
        title=record.title,
        company=record.company,
        description=record.description,
        location_city=record.location_city,
        location_state=record.location_state,
        location_country=record.location_country,
        coordinates={"lat": record.lat, "lng": record.lng} if record.lat is not None and record.lng is not None else None,
        radius_km=record.radius_km,
        accept_relocation=record.accept_relocation,
        remote=record.remote,
        hybrid=record.hybrid,
        employment_type=record.employment_type,
        experience_min=record.experience_min,
        experience_max=record.experience_max,
        salary_min=record.salary_min,
        salary_max=record.salary_max,
        currency=record.currency,
        required_skills=record.required_skills,
        preferred_skills=record.preferred_skills,
        auto_shortlist_threshold=record.auto_shortlist_threshold,
        status=record.status,
        visibility=record.visibility,
        application_deadline=record.application_deadline,
        created_at=record.created_at,
    )


def _application_pipeline_identifier(application: CandidateApplication) -> str:
    """Return the stable recruiter-facing identifier for one pipeline row."""

    return application.employee_id or application.candidate_id or application.id


def _application_ranked_candidate(application: CandidateApplication, job: JobPosting) -> RankedCandidate:
    """Build a ranked-candidate payload from a persisted pipeline application."""

    match_payload = dict(application.match_result or {})
    score_breakdown = match_payload.get("score_breakdown") or {
        "skill_score": 0.0,
        "experience_score": 0.0,
        "project_score": 0.0,
        "verification_score": float(match_payload.get("verification_score", 0.0) or 0.0),
    }
    location_status = str(match_payload.get("location_status") or ("remote" if job.remote else "local"))
    if location_status not in {"local", "relocation", "remote"}:
        location_status = "remote" if job.remote else "local"

    candidate_data = application.candidate_data or {}
    return RankedCandidate.model_validate(
        {
            "candidate_id": _application_pipeline_identifier(application),
            "job_id": job.id,
            "final_score": round(float(application.final_score or match_payload.get("final_score", 0.0) or 0.0), 2),
            "grade": str(match_payload.get("grade") or ("Pending" if application.source == "form" else "F")),
            "location_status": location_status,
            "distance_km": match_payload.get("distance_km"),
            "pipeline_stage": application.pipeline_stage,
            "candidate_name": str(
                match_payload.get("candidate_name")
                or candidate_data.get("employee_name")
                or candidate_data.get("name")
                or "New applicant"
            ),
            "location_label": str(match_payload.get("location_label") or candidate_data.get("location") or ""),
            "top_skills": list(match_payload.get("top_skills", [])),
            "verification_score": float(match_payload.get("verification_score", 0.0) or 0.0),
            "skill_breakdown": list(match_payload.get("skill_breakdown", [])),
            "missing_required": list(match_payload.get("missing_required", [])),
            "strongest_projects": list(match_payload.get("strongest_projects", [])),
            "score_breakdown": score_breakdown,
            "recommendation": str(
                match_payload.get("recommendation")
                or (
                    "Application received from the public intake form and waiting for recruiter review."
                    if application.source == "form"
                    else "Application received and waiting for recruiter review."
                )
            ),
        }
    )


def _merge_rankings_with_applications(
    job: JobPosting,
    rankings: list[RankedCandidate],
    applications: list[CandidateApplication],
) -> list[RankedCandidate]:
    """Combine live matcher output with persisted recruiter pipeline applications."""

    merged = {ranking.candidate_id: ranking for ranking in rankings}
    for application in applications:
        pipeline_identifier = _application_pipeline_identifier(application)
        ranking = merged.get(pipeline_identifier)
        if ranking is None:
            merged[pipeline_identifier] = _application_ranked_candidate(application, job)
            continue
        ranking.pipeline_stage = application.pipeline_stage
    items = list(merged.values())
    items.sort(key=lambda item: (item.location_status != "local", -(item.final_score or 0.0), item.candidate_name.lower()))
    return items


@router.post(
    "/jobs",
    summary="Create job posting",
    description="Create a recruiter job posting from either raw JD text or structured form data.",
    response_model=JobPostingResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_job_posting(
    request: Request,
    payload: JobPostingCreateRequest,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> JobPostingResponse:
    """Create and persist a recruiter job posting."""

    structured = await request.app.state.job_posting_agent.run(payload, recruiter.company_name)
    record = JobPosting(
        recruiter_id=recruiter.id,
        title=structured.title,
        company=structured.company,
        description=structured.description,
        structured_requirements=structured.structured_requirements,
        location_city=structured.location_city,
        location_state=structured.location_state,
        location_country=structured.location_country,
        lat=structured.lat,
        lng=structured.lng,
        radius_km=structured.radius_km,
        accept_relocation=structured.accept_relocation,
        remote=structured.remote,
        hybrid=structured.hybrid,
        employment_type=structured.employment_type,
        experience_min=structured.experience_min,
        experience_max=structured.experience_max,
        salary_min=structured.salary_min,
        salary_max=structured.salary_max,
        currency=structured.currency,
        required_skills=structured.required_skills,
        preferred_skills=structured.preferred_skills,
        auto_shortlist_threshold=structured.auto_shortlist_threshold,
        application_deadline=structured.application_deadline,
        job_embedding_id="",
    )
    session.add(record)
    await session.flush()
    job_vector = await request.app.state.embedding_service.embed_text(record.description)
    get_job_collection().upsert(
        ids=[record.id],
        embeddings=[job_vector],
        metadatas=[{"title": record.title, "company": record.company}],
        documents=[record.description],
    )
    record.job_embedding_id = record.id
    await session.commit()
    await session.refresh(record)
    return _job_response(record)


@router.post(
    "/jobs/{job_id}/resume-batch",
    summary="Queue recruiter resume batch",
    description="Upload a recruiter-owned batch of resumes and attach parsed candidates to this job pipeline as resume uploads.",
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def queue_recruiter_resume_batch(
    job_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> JobStatusResponse:
    """Queue a recruiter-scoped batch resume parse for one job posting."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})

    redis = await get_redis()
    response = await queue_batch_parse_job(redis=redis, files=files, recruiter_job_id=job_id)
    background_tasks.add_task(_consume_batch_queue, request.app, response.job_id)
    return response


@router.get(
    "/jobs",
    summary="List recruiter jobs",
    description="List job postings owned by the authenticated recruiter.",
    response_model=JobPostingListResponse,
)
async def list_recruiter_jobs(
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> JobPostingListResponse:
    """Return recruiter-owned job postings."""

    items = list((await session.execute(select(JobPosting).where(JobPosting.recruiter_id == recruiter.id).order_by(JobPosting.created_at.desc()))).scalars().all())
    return JobPostingListResponse(items=[_job_response(item) for item in items], total=len(items))


@router.get(
    "/jobs/{job_id}",
    summary="Get recruiter job",
    description="Fetch one recruiter-owned job posting by id.",
    response_model=JobPostingResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_job_posting(
    job_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> JobPostingResponse:
    """Return one recruiter job posting."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})
    return _job_response(record)


@router.patch(
    "/jobs/{job_id}",
    summary="Update recruiter job",
    description="Update mutable recruiter job fields such as status, threshold, or radius.",
    response_model=JobPostingResponse,
    responses={404: {"model": ErrorResponse}},
)
async def patch_job_posting(
    job_id: str,
    payload: JobPostingPatchRequest,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> JobPostingResponse:
    """Apply a partial update to a recruiter job."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})

    for field_name, value in payload.model_dump(exclude_none=True).items():
        setattr(record, field_name, value)
    await session.commit()
    await session.refresh(record)
    return _job_response(record)


@router.post(
    "/jobs/{job_id}/run-matching",
    summary="Run recruiter matching",
    description="Rank the current candidate pool for a recruiter job and persist the results into the pipeline.",
    response_model=RunMatchingResponse,
    responses={404: {"model": ErrorResponse}},
)
async def run_matching(
    request: Request,
    job_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> RunMatchingResponse:
    """Run the location-aware role matcher for one recruiter job."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})

    rankings = await request.app.state.role_matcher.run(session, record)
    matched_count, shortlisted_count = await request.app.state.role_matcher.persist_rankings(session, record, rankings)
    return RunMatchingResponse(matched_count=matched_count, shortlisted_count=shortlisted_count, job_id=job_id)


@router.get(
    "/jobs/{job_id}/candidates",
    summary="List recruiter candidates",
    description="Return ranked candidates for one recruiter job, with location-aware ordering and optional filters.",
    response_model=RankedCandidateListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def list_job_candidates(
    request: Request,
    job_id: str,
    stage: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=100),
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> RankedCandidateListResponse:
    """Return recruiter candidate rankings for a job."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})
    rankings = await request.app.state.role_matcher.run(session, record)
    application_rows = list((await session.execute(select(CandidateApplication).where(CandidateApplication.job_id == job_id))).scalars().all())
    rankings = _merge_rankings_with_applications(record, rankings, application_rows)
    if stage is not None:
        rankings = [item for item in rankings if item.pipeline_stage == stage]
    if min_score is not None:
        rankings = [item for item in rankings if item.final_score >= min_score]
    return RankedCandidateListResponse(items=rankings, total=len(rankings))


@router.get(
    "/jobs/{job_id}/candidates/export",
    summary="Export recruiter candidates",
    description="Download the recruiter pipeline candidates for one job as CSV.",
    responses={404: {"model": ErrorResponse}},
)
async def export_job_candidates(
    request: Request,
    job_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export recruiter candidates for a job as a CSV attachment."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})

    rankings = await request.app.state.role_matcher.run(session, record)
    application_rows = list((await session.execute(select(CandidateApplication).where(CandidateApplication.job_id == job_id))).scalars().all())
    merged = _merge_rankings_with_applications(record, rankings, application_rows)
    sources = {_application_pipeline_identifier(application): application.source for application in application_rows}

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "candidate_id",
            "candidate_name",
            "pipeline_stage",
            "final_score",
            "grade",
            "location_status",
            "distance_km",
            "location_label",
            "top_skills",
            "missing_required",
            "source",
            "recommendation",
        ],
    )
    writer.writeheader()
    for item in merged:
        writer.writerow(
            {
                "candidate_id": item.candidate_id,
                "candidate_name": item.candidate_name,
                "pipeline_stage": item.pipeline_stage,
                "final_score": item.final_score,
                "grade": item.grade,
                "location_status": item.location_status,
                "distance_km": item.distance_km or "",
                "location_label": item.location_label,
                "top_skills": ", ".join(item.top_skills),
                "missing_required": ", ".join(item.missing_required),
                "source": sources.get(item.candidate_id, "pool"),
                "recommendation": item.recommendation,
            }
        )

    file_name = f"{record.title.strip().lower().replace(' ', '-') or 'job'}-candidates.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.delete(
    "/jobs/{job_id}",
    summary="Delete recruiter job",
    description="Delete a recruiter-owned job posting and its candidate pipeline rows.",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
)
async def delete_job_posting(
    job_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a recruiter job posting."""

    record = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})
    applications = list((await session.execute(select(CandidateApplication).where(CandidateApplication.job_id == job_id))).scalars().all())
    for application in applications:
        await session.delete(application)
    await session.delete(record)
    await session.commit()
    return {"deleted": True, "job_id": job_id}


@router.post(
    "/jobs/{job_id}/candidates/{candidate_id}/stage",
    summary="Update pipeline stage",
    description="Move a recruiter candidate to a new pipeline stage and optionally store a note.",
    response_model=CandidateStageUpdateResponse,
    responses={404: {"model": ErrorResponse}},
)
async def update_candidate_stage(
    job_id: str,
    candidate_id: str,
    payload: CandidateStageUpdateRequest,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> CandidateStageUpdateResponse:
    """Update one candidate's recruiter pipeline stage."""

    job = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})
    application = await session.scalar(
        select(CandidateApplication).where(
            CandidateApplication.job_id == job_id,
            (CandidateApplication.id == candidate_id)
            | (CandidateApplication.candidate_id == candidate_id)
            | (CandidateApplication.employee_id == candidate_id),
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail={"error": "candidate_not_found", "message": "Candidate is not in this pipeline."})
    application.pipeline_stage = payload.stage
    if payload.note is not None:
        application.recruiter_notes = payload.note
    await session.commit()
    await session.refresh(application)
    return CandidateStageUpdateResponse(
        application_id=application.id,
        candidate_id=candidate_id,
        job_id=job_id,
        pipeline_stage=application.pipeline_stage,
        recruiter_notes=application.recruiter_notes,
    )
