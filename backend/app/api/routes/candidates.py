"""Candidate profile routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db import Candidate
from app.models.schemas import CandidateResponse, CandidateSkillsResponse, ErrorResponse

router = APIRouter(tags=["Candidates"])


@router.get(
    "/candidates/{candidate_id}",
    summary="Get candidate profile",
    description="Fetch the stored candidate profile by candidate ID.",
    response_model=CandidateResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_candidate(candidate_id: str, session: AsyncSession = Depends(get_session)) -> CandidateResponse:
    """Return a stored candidate profile."""

    candidate = await session.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "candidate_not_found", "message": "Candidate not found."})

    payload = candidate.profile_json.get("candidate_profile", {})
    return CandidateResponse(
        id=candidate.id,
        quality_score=candidate.quality_score,
        source_format=candidate.source_format,
        created_at=candidate.created_at,
        **payload,
    )


@router.get(
    "/candidates/{candidate_id}/skills",
    summary="Get candidate skills",
    description="Fetch the normalized skill profile for a stored candidate.",
    response_model=CandidateSkillsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_candidate_skills(candidate_id: str, session: AsyncSession = Depends(get_session)) -> CandidateSkillsResponse:
    """Return normalized skills for a candidate."""

    candidate = await session.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "candidate_not_found", "message": "Candidate not found."})
    return CandidateSkillsResponse(candidate_id=candidate_id, skill_profile=candidate.profile_json.get("skill_profile", {}))
