"""Recruiter job posting and pipeline routes for TalentOS v3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb_client import get_job_collection
from app.core.database import get_session
from app.models.db_v3 import CandidateApplication, JobPosting, Recruiter
from app.models.schemas import ErrorResponse
from app.models.schemas_v3 import (
    CandidateStageUpdateRequest,
    CandidateStageUpdateResponse,
    JobPostingCreateRequest,
    JobPostingListResponse,
    JobPostingPatchRequest,
    JobPostingResponse,
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
    application_rows = {
        row.candidate_id: row
        for row in list((await session.execute(select(CandidateApplication).where(CandidateApplication.job_id == job_id))).scalars().all())
        if row.candidate_id
    }
    for ranking in rankings:
        application = application_rows.get(ranking.candidate_id)
        if application is not None:
            ranking.pipeline_stage = application.pipeline_stage
    if stage is not None:
        rankings = [item for item in rankings if item.pipeline_stage == stage]
    if min_score is not None:
        rankings = [item for item in rankings if item.final_score >= min_score]
    return RankedCandidateListResponse(items=rankings, total=len(rankings))


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
            CandidateApplication.candidate_id == candidate_id,
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
