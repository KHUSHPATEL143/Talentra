"""Recruiter pool browser and analytics routes for TalentOS v3."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db_v3 import (
    CandidateApplication,
    CareerSuggestion,
    Employee,
    JobPosting,
    PoolAccessRequest,
    Recruiter,
    SocialProfile,
    VerifiedSkillProfile,
)
from app.models.schemas_v3 import (
    PoolAccessRequestPayload,
    PoolAccessRequestResponse,
    PoolCandidateListResponse,
    PoolCandidateResponse,
    RecruiterAnalyticsResponse,
)
from app.services.auth_service import require_recruiter

router = APIRouter(tags=["TalentOS Pool"])


@router.get("/pool/candidates", response_model=PoolCandidateListResponse, summary="Browse talent pool")
async def list_pool_candidates(
    skill: str | None = Query(default=None),
    location: str | None = Query(default=None),
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> PoolCandidateListResponse:
    """Return searchable employee profiles from the TalentOS pool."""

    employees = list((await session.execute(select(Employee).order_by(Employee.created_at.desc()))).scalars().all())
    social_profiles = {
        row.employee_id: row
        for row in list((await session.execute(select(SocialProfile))).scalars().all())
    }
    verified_profiles = {
        row.employee_id: row
        for row in list((await session.execute(select(VerifiedSkillProfile))).scalars().all())
    }

    items: list[PoolCandidateResponse] = []
    for employee in employees:
        verified = verified_profiles.get(employee.id)
        social = social_profiles.get(employee.id)
        top_skills = [item.get("canonical_name", "") for item in (verified.skills if verified else []) if item.get("canonical_name")]
        location_label = ", ".join(part for part in [employee.location_city, employee.location_country] if part)
        if skill and not any(skill.strip().lower() in item.lower() for item in top_skills):
            continue
        if location and location.strip().lower() not in location_label.lower():
            continue
        items.append(
            PoolCandidateResponse(
                employee_id=employee.id,
                name=employee.name,
                location=location_label,
                open_to_relocation=employee.open_to_relocation,
                verification_score=verified.verification_score if verified else 0.0,
                profile_completeness=employee.profile_completeness,
                top_skills=top_skills[:6],
                github_username=social.github_username if social and social.github_username else "",
                linkedin_url=social.linkedin_url if social and social.linkedin_url else "",
            )
        )
    return PoolCandidateListResponse(items=items, total=len(items))


@router.post("/pool/request/{employee_id}", response_model=PoolAccessRequestResponse, summary="Request candidate contact")
async def request_pool_access(
    employee_id: str,
    payload: PoolAccessRequestPayload,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> PoolAccessRequestResponse:
    """Create a recruiter contact request for a pooled employee."""

    request_row = PoolAccessRequest(
        recruiter_id=recruiter.id,
        employee_id=employee_id,
        job_id=payload.job_id,
        status="pending",
        message=payload.message,
    )
    session.add(request_row)
    await session.commit()
    await session.refresh(request_row)
    return PoolAccessRequestResponse(
        id=request_row.id,
        employee_id=request_row.employee_id,
        recruiter_id=request_row.recruiter_id,
        status=request_row.status,
        message=request_row.message,
    )


@router.get("/analytics/overview", response_model=RecruiterAnalyticsResponse, summary="Recruiter analytics overview")
async def recruiter_analytics(
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> RecruiterAnalyticsResponse:
    """Return simple recruiter analytics for current jobs and pipelines."""

    jobs = list((await session.execute(select(JobPosting).where(JobPosting.recruiter_id == recruiter.id))).scalars().all())
    job_ids = [job.id for job in jobs]
    applications = list((await session.execute(select(CandidateApplication).where(CandidateApplication.job_id.in_(job_ids) if job_ids else False))).scalars().all()) if job_ids else []

    shortlisted = [item for item in applications if item.pipeline_stage == "shortlisted"]
    hired = [item for item in applications if item.pipeline_stage == "hired"]
    average_score = round(sum(item.final_score for item in applications) / len(applications), 2) if applications else 0.0

    skill_counter: Counter[str] = Counter()
    for job in jobs:
        for skill in job.required_skills or []:
            name = str(skill.get("skill", "")).strip()
            if name:
                skill_counter[name] += 1

    return RecruiterAnalyticsResponse(
        active_jobs=len([job for job in jobs if job.status == "active"]),
        total_pipeline_candidates=len(applications),
        shortlisted_candidates=len(shortlisted),
        hired_candidates=len(hired),
        average_score=average_score,
        skill_distribution=[{"skill": skill, "count": count} for skill, count in skill_counter.most_common(8)],
    )
