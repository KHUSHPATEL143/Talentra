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

    def __init__(self) -> None:
        self.calls = 0

    async def extract_candidate_profile_with_hints(self, resume_text: str, heuristic_profile: CandidateProfile) -> CandidateProfile:
        """Return a stable candidate profile."""

        self.calls += 1
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
    assert message.payload["candidate_profile"]["linkedin"] == "https://linkedin.com/in/adalovelace"


@pytest.mark.asyncio
async def test_parsing_agent_extracts_github_profile_from_heuristics() -> None:
    """The parsing agent should preserve a GitHub profile URL in the candidate payload."""

    class FailingLLMService:
        async def extract_candidate_profile_with_hints(self, resume_text: str, heuristic_profile: CandidateProfile) -> CandidateProfile:
            raise RuntimeError("llm unavailable")

    class RichFileParser:
        async def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
            return file_bytes.decode("utf-8")

    raw_resume = (
        b"Ada Lovelace\n"
        b"ada@example.com\n"
        b"https://linkedin.com/in/adalovelace\n"
        b"https://github.com/adalovelace\n"
        b"Skills\nPython, FastAPI\n"
    )

    agent = ParsingAgent(
        file_parser=RichFileParser(),
        llm_service=FailingLLMService(),
        heuristic_service=ResumeHeuristicService(),
    )
    message = await agent.run(job_id="job-2b", file_bytes=raw_resume, mime_type="text/plain")

    assert message.payload["candidate_profile"]["github"] == "https://github.com/adalovelace"


@pytest.mark.asyncio
async def test_parsing_agent_skips_llm_for_high_quality_simple_resume() -> None:
    """The parsing agent should avoid an LLM call when heuristics already look strong."""

    class SimpleResumeParser:
        async def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
            return (
                "Ada Lovelace\n"
                "London, UK\n"
                "ada@example.com\n"
                "+1 555 123 4567\n"
                "linkedin.com/in/adalovelace\n\n"
                "github.com/adalovelace\n\n"
                "Summary\n"
                "Backend engineer building reliable Python APIs and ML tooling.\n\n"
                "Skills\n"
                "Python, FastAPI, Docker, PostgreSQL, AWS\n"
            )

    llm = FakeLLMService()
    agent = ParsingAgent(
        file_parser=SimpleResumeParser(),
        llm_service=llm,
        heuristic_service=ResumeHeuristicService(),
    )

    message = await agent.run(job_id="job-3", file_bytes=b"resume", mime_type="text/plain")

    assert llm.calls == 0
    assert message.payload["candidate_profile"]["name"] == "Ada Lovelace"
    assert len(message.payload["candidate_profile"]["skills"]) >= 4
    assert message.payload["candidate_profile"]["github"] == "https://github.com/adalovelace"
