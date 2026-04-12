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
