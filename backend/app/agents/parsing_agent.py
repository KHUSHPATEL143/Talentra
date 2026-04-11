"""Resume parsing agent implementation."""

from __future__ import annotations

import time
from typing import Any

import structlog

from app.models.schemas import AgentMessage, AgentTrace, CandidateProfile
from app.services.file_parser import FileParserService
from app.services.llm_service import LLMService
from app.services.resume_heuristics import ResumeHeuristicService

logger = structlog.get_logger(__name__)


class ParsingAgent:
    """Extract structured candidate profiles from raw resume files."""

    def __init__(
        self,
        file_parser: FileParserService,
        llm_service: LLMService,
        heuristic_service: ResumeHeuristicService,
    ) -> None:
        """Store dependencies needed for parsing."""

        self.file_parser = file_parser
        self.llm_service = llm_service
        self.heuristic_service = heuristic_service

    async def run(self, job_id: str, file_bytes: bytes, mime_type: str) -> AgentMessage:
        """Parse a resume file into a validated candidate profile."""

        started_at = time.perf_counter()
        logger.info("agent.enter", job_id=job_id, agent_name="parsing_agent")
        raw_text = await self.file_parser.extract_text(file_bytes, mime_type)
        heuristic_profile = self.heuristic_service.extract_profile(raw_text)
        try:
            candidate_profile = await self.llm_service.extract_candidate_profile_with_hints(raw_text, heuristic_profile)
            candidate_profile = self.heuristic_service.merge_profiles(heuristic_profile, candidate_profile)
        except Exception:
            if self._has_usable_heuristics(heuristic_profile):
                candidate_profile = heuristic_profile
            else:
                raise
        quality_score = self._compute_quality_score(candidate_profile)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info("agent.exit", job_id=job_id, agent_name="parsing_agent", latency_ms=latency_ms)
        return AgentMessage(
            job_id=job_id,
            stage="parsed",
            payload={
                "candidate_profile": candidate_profile.model_dump(),
                "raw_text": raw_text,
            },
            trace=AgentTrace(agent="parsing_agent", latency_ms=latency_ms, quality_score=quality_score),
            errors=[],
            partial=False,
        )

    def _compute_quality_score(self, candidate_profile: CandidateProfile) -> float:
        """Compute ratio of populated top-level fields."""

        payload = candidate_profile.model_dump()
        total = len(payload)
        populated = 0
        for value in payload.values():
            if isinstance(value, dict):
                populated += int(any(str(item).strip() for item in value.values()))
            elif isinstance(value, list):
                populated += int(len(value) > 0)
            else:
                populated += int(str(value).strip() != "")
        return round(populated / total if total else 0.0, 3)

    def _has_usable_heuristics(self, candidate_profile: CandidateProfile) -> bool:
        """Return whether deterministic extraction found enough data to return safely."""

        return bool(
            candidate_profile.name
            or candidate_profile.email
            or candidate_profile.phone
            or candidate_profile.linkedin
            or candidate_profile.skills
        )
