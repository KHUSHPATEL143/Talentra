"""Recruiter form builder and public submission routes for TalentOS v3."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db_v3 import CandidateApplication, FormResponse, IntakeForm, JobPosting, Recruiter
from app.models.schemas import ErrorResponse
from app.models.schemas_v3 import (
    IntakeFormCreateRequest,
    IntakeFormResponse,
    PublicFormSubmissionRequest,
    PublicFormSubmissionResponse,
    RecruiterFormResponseItem,
    RecruiterFormResponseListResponse,
)
from app.services.auth_service import require_recruiter

router = APIRouter(tags=["TalentOS Forms"])


def _form_response(form: IntakeForm) -> IntakeFormResponse:
    """Serialize an intake form."""

    return IntakeFormResponse(
        id=form.id,
        job_id=form.job_id,
        public_slug=form.public_slug,
        response_count=form.response_count,
        fields=form.form_schema,
    )


@router.post(
    "/jobs/{job_id}/forms",
    response_model=IntakeFormResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Create recruiter intake form",
)
async def create_or_replace_form(
    job_id: str,
    payload: IntakeFormCreateRequest,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> IntakeFormResponse:
    """Create or replace the intake form for a recruiter job."""

    job = await session.scalar(select(JobPosting).where(JobPosting.id == job_id, JobPosting.recruiter_id == recruiter.id))
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "job_not_found", "message": "Job posting not found."})

    form = await session.scalar(select(IntakeForm).where(IntakeForm.job_id == job_id, IntakeForm.recruiter_id == recruiter.id))
    if form is None:
        form = IntakeForm(
            recruiter_id=recruiter.id,
            job_id=job_id,
            form_schema=[field.model_dump() for field in payload.fields],
            public_slug=f"{job.title.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}",
        )
        session.add(form)
    else:
        form.form_schema = [field.model_dump() for field in payload.fields]
    await session.commit()
    await session.refresh(form)
    return _form_response(form)


@router.get(
    "/jobs/{job_id}/forms",
    response_model=IntakeFormResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get recruiter intake form",
)
async def get_recruiter_form(
    job_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> IntakeFormResponse:
    """Return the recruiter intake form for a job."""

    form = await session.scalar(select(IntakeForm).where(IntakeForm.job_id == job_id, IntakeForm.recruiter_id == recruiter.id))
    if form is None:
        raise HTTPException(status_code=404, detail={"error": "form_not_found", "message": "Intake form not found."})
    return _form_response(form)


@router.get(
    "/forms/{form_id}/responses",
    response_model=RecruiterFormResponseListResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get recruiter intake form responses",
)
async def get_recruiter_form_responses(
    form_id: str,
    recruiter: Recruiter = Depends(require_recruiter),
    session: AsyncSession = Depends(get_session),
) -> RecruiterFormResponseListResponse:
    """Return recruiter-visible public form submissions for one intake form."""

    form = await session.scalar(select(IntakeForm).where(IntakeForm.id == form_id, IntakeForm.recruiter_id == recruiter.id))
    if form is None:
        raise HTTPException(status_code=404, detail={"error": "form_not_found", "message": "Intake form not found."})

    response_rows = list(
        (
            await session.execute(
                select(FormResponse).where(FormResponse.form_id == form_id).order_by(FormResponse.created_at.desc())
            )
        ).scalars().all()
    )
    application_ids = [row.application_id for row in response_rows if row.application_id]
    applications = {}
    if application_ids:
        applications = {
            application.id: application
            for application in list(
                (await session.execute(select(CandidateApplication).where(CandidateApplication.id.in_(application_ids)))).scalars().all()
            )
        }

    items: list[RecruiterFormResponseItem] = []
    for row in response_rows:
        application = applications.get(row.application_id or "")
        candidate_data = application.candidate_data if application else {}
        items.append(
            RecruiterFormResponseItem(
                form_response_id=row.id,
                application_id=row.application_id,
                candidate_name=str(candidate_data.get("employee_name") or candidate_data.get("name") or "New applicant"),
                email=str(candidate_data.get("employee_email") or candidate_data.get("email") or ""),
                location=str(candidate_data.get("location") or ""),
                submitted_at=row.created_at,
                pipeline_stage=application.pipeline_stage if application else "new",
                match_score=float(application.final_score or 0.0) if application else 0.0,
                response_preview=dict(row.responses.get("answers", {}) if isinstance(row.responses, dict) else {}),
            )
        )

    return RecruiterFormResponseListResponse(items=items, total=len(items))


@router.get(
    "/public/forms/{slug}",
    response_model=IntakeFormResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get public intake form",
)
async def get_public_form(slug: str, session: AsyncSession = Depends(get_session)) -> IntakeFormResponse:
    """Return a public intake form by slug."""

    form = await session.scalar(select(IntakeForm).where(IntakeForm.public_slug == slug))
    if form is None:
        raise HTTPException(status_code=404, detail={"error": "form_not_found", "message": "Public form not found."})
    return _form_response(form)


@router.post(
    "/public/forms/{slug}/submit",
    response_model=PublicFormSubmissionResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Submit public intake form",
)
async def submit_public_form(
    slug: str,
    payload: PublicFormSubmissionRequest,
    session: AsyncSession = Depends(get_session),
) -> PublicFormSubmissionResponse:
    """Store a public candidate submission and attach it to the job pipeline."""

    form = await session.scalar(select(IntakeForm).where(IntakeForm.public_slug == slug))
    if form is None:
        raise HTTPException(status_code=404, detail={"error": "form_not_found", "message": "Public form not found."})

    application = CandidateApplication(
        employee_id=None,
        candidate_id=None,
        job_id=form.job_id,
        source="form",
        candidate_data={
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "location": payload.location,
            "open_to_relocation": payload.open_to_relocation,
            "github_url": payload.github_url,
            "linkedin_url": payload.linkedin_url,
            "answers": payload.answers,
        },
        match_result={},
        final_score=0.0,
        pipeline_stage="new",
    )
    session.add(application)
    await session.flush()
    response_row = FormResponse(form_id=form.id, responses=payload.model_dump(), application_id=application.id)
    session.add(response_row)
    form.response_count += 1
    await session.commit()
    return PublicFormSubmissionResponse(form_id=form.id, application_id=application.id, submitted=True)
