"""Parsing agent tests."""

from __future__ import annotations

import pytest

from app.agents.parsing_agent import ParsingAgent
from app.models.schemas import CandidateProfile
from app.services.resume_heuristics import ResumeHeuristicService


class FakeFileParser:
    """Test double for file parsing."""

    async def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        """Return deterministic resume text."""

        return "Ada Lovelace\nPython\nFastAPI"


class FakeLLMService:
    """Test double for structured extraction."""

    async def extract_candidate_profile_with_hints(self, resume_text: str, heuristic_profile: CandidateProfile) -> CandidateProfile:
        """Return a stable candidate profile."""

        return CandidateProfile(
            name="Ada Lovelace",
            email="ada@example.com",
            skills=["Python", "FastAPI"],
            summary="Backend engineer",
        )


@pytest.mark.asyncio
async def test_parsing_agent_returns_structured_payload() -> None:
    """The parsing agent should wrap extracted profile data in an AgentMessage."""

    agent = ParsingAgent(
        file_parser=FakeFileParser(),
        llm_service=FakeLLMService(),
        heuristic_service=ResumeHeuristicService(),
    )
    message = await agent.run(job_id="job-1", file_bytes=b"resume", mime_type="text/plain")

    assert message.stage == "parsed"
    assert message.payload["candidate_profile"]["name"] == "Ada Lovelace"
    assert message.payload["raw_text"].startswith("Ada")
    assert message.trace.quality_score > 0


@pytest.mark.asyncio
async def test_parsing_agent_falls_back_to_heuristics_when_llm_fails() -> None:
    """The parsing agent should still return basic contact data when the LLM fails."""

    class FailingLLMService:
        async def extract_candidate_profile_with_hints(self, resume_text: str, heuristic_profile: CandidateProfile) -> CandidateProfile:
            raise RuntimeError("llm unavailable")

    class RichFileParser:
        async def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
            return file_bytes.decode("utf-8")

    raw_resume = b"Ada Lovelace\nada@example.com\n+1 555 123 4567\nhttps://linkedin.com/in/adalovelace\nSkills\nPython, FastAPI"

    agent = ParsingAgent(
        file_parser=RichFileParser(),
        llm_service=FailingLLMService(),
        heuristic_service=ResumeHeuristicService(),
    )
    message = await agent.run(job_id="job-2", file_bytes=raw_resume, mime_type="text/plain")

    assert message.payload["candidate_profile"]["email"] == "ada@example.com"
    assert "Python" in message.payload["candidate_profile"]["skills"]
