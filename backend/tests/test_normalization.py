"""Normalization agent tests."""

from __future__ import annotations

import pytest

from app.agents.normalization_agent import NormalizationAgent
from app.models.schemas import CandidateProfile
from app.utils.skill_inference import InferenceRule, SkillInferenceEngine


class FakeTaxonomyService:
    """Test double for taxonomy matching."""

    def __init__(self) -> None:
        """Track fallback usage during normalization tests."""

        self.llm_calls = 0

    def exact_match(self, raw_skill: str):
        """Return exact aliases for known skills."""

        mapping = {
            "python": {"canonical_name": "Python", "aliases": ["py"], "category": "Programming Languages", "subcategory": "Backend"},
            "react": {"canonical_name": "React", "aliases": ["react.js"], "category": "Web Frameworks", "subcategory": "Frontend"},
            "redux": {"canonical_name": "Redux", "aliases": ["redux toolkit"], "category": "Web Frameworks", "subcategory": "Frontend"},
            "docker": {"canonical_name": "Docker", "aliases": ["docker engine"], "category": "DevOps", "subcategory": "Containers"},
        }
        return mapping.get(raw_skill.lower())

    def fuzzy_match(self, raw_skill: str, threshold: int = 85):
        """Return no fuzzy match for this test."""

        return None, 0.0

    async def embedding_match(self, raw_skill: str, threshold: float = 0.82):
        """Return no embedding match for this test."""

        return None, 0.0

    async def llm_match(self, raw_skill: str):
        """Return a low-confidence fallback response for unknown skills."""

        from app.models.schemas import SkillFallbackResponse

        self.llm_calls += 1
        return SkillFallbackResponse(canonical_name=raw_skill, confidence=0.2, reasoning="unknown")

    async def mark_pending_review(self, session, raw_skill: str, suggested_canonical: str | None, confidence: float):
        """No-op pending taxonomy review persistence."""

        return None


class FakeSession:
    """No-op async session used by the normalization agent test."""


@pytest.mark.asyncio
async def test_normalization_agent_applies_inference_rules() -> None:
    """The normalization agent should infer higher-order skills from trigger rules."""

    engine = SkillInferenceEngine([InferenceRule(triggers=["React", "Redux"], infers="Frontend Engineering")])
    agent = NormalizationAgent(taxonomy_service=FakeTaxonomyService(), inference_engine=engine)
    candidate = CandidateProfile(skills=["React", "Redux"])

    message = await agent.run(job_id="job-1", candidate_profile=candidate, raw_text="React expert with Redux since 2020", session=FakeSession())

    normalized_names = {item["name"] for item in message.payload["skill_profile"]["normalized_skills"]}
    assert "React" in normalized_names
    assert "Redux" in normalized_names
    assert "Frontend Engineering" in normalized_names


@pytest.mark.asyncio
async def test_normalization_agent_filters_noisy_skill_tokens() -> None:
    """The normalization agent should clean noisy raw skills before expensive fallbacks."""

    taxonomy = FakeTaxonomyService()
    agent = NormalizationAgent(
        taxonomy_service=taxonomy,
        inference_engine=SkillInferenceEngine([]),
    )
    candidate = CandidateProfile(
        skills=[
            "Skills",
            "Python, React | Docker",
            "Developed APIs for clients",
            "https://linkedin.com/in/demo",
        ]
    )

    message = await agent.run(job_id="job-2", candidate_profile=candidate, raw_text="Python and React developer using Docker", session=FakeSession())

    assert message.payload["skill_profile"]["raw_skills"] == ["Python", "React", "Docker"]
    normalized_names = {item["name"] for item in message.payload["skill_profile"]["normalized_skills"]}
    assert normalized_names == {"Python", "React", "Docker"}
    assert taxonomy.llm_calls == 0
