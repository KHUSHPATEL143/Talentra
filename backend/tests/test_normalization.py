"""Normalization agent tests."""

from __future__ import annotations

import pytest

from app.agents.normalization_agent import NormalizationAgent
from app.models.schemas import CandidateProfile
from app.utils.skill_inference import InferenceRule, SkillInferenceEngine


class FakeTaxonomyService:
    """Test double for taxonomy matching."""

    def exact_match(self, raw_skill: str):
        """Return exact aliases for known skills."""

        mapping = {
            "react": {"canonical_name": "React", "aliases": ["react.js"], "category": "Web Frameworks", "subcategory": "Frontend"},
            "redux": {"canonical_name": "Redux", "aliases": ["redux toolkit"], "category": "Web Frameworks", "subcategory": "Frontend"},
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
