"""Candidate-job matching routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db import Candidate, ExecutionTrace, Job, Match
from app.models.schemas import ErrorResponse, MatchRequest, MatchResponse, SkillProfile

router = APIRouter(tags=["Matching"])


@router.post(
    "/match",
    summary="Match a candidate to a job",
    description="Run semantic skill matching between a stored candidate profile and a job description.",
    response_model=MatchResponse,
    responses={404: {"model": ErrorResponse}},
)
async def match_candidate(
    request: Request,
    payload: MatchRequest,
    session: AsyncSession = Depends(get_session),
) -> MatchResponse:
    """Compute, persist, and return a candidate-job match result."""

    candidate = await session.get(Candidate, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "candidate_not_found", "message": "Candidate not found."})

    message = await request.app.state.matching_agent.run(
        job_id="",
        skill_profile=SkillProfile.model_validate(candidate.profile_json.get("skill_profile", {})),
        job_description=payload.job_description,
        weights=payload.weights,
        mode=payload.mode,
    )
    job = Job(description=payload.job_description, parsed_requirements_json=message.payload["match_result"]["parsed_requirements"])
    session.add(job)
    await session.flush()

    match = Match(
        candidate_id=candidate.id,
        job_id=job.id,
        score=message.payload["match_result"]["score"],
        grade=message.payload["match_result"]["grade"],
        match_result_json=message.payload["match_result"],
    )
    session.add(match)
    session.add(
        ExecutionTrace(
            job_id=job.id,
            agent_name=message.trace.agent,
            latency_ms=message.trace.latency_ms,
            quality_score=message.trace.quality_score,
            error=message.trace.error,
        )
    )
    await session.commit()
    await session.refresh(match)

    await request.app.state.webhook_service.dispatch_event(
        session=session,
        event_name="match.complete",
        payload={"match_id": match.id, "candidate_id": candidate.id, "job_id": job.id},
    )
    return MatchResponse(match_id=match.id, candidate_id=candidate.id, job_id=job.id, **message.payload["match_result"])
