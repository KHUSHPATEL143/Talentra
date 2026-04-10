"""Matching agent tests."""

from __future__ import annotations

import pytest

from app.agents.matching_agent import MatchingAgent
from app.models.schemas import JobRequirementsPromptResponse, RecommendationResponse, SkillProfile


class FakeEmbeddingService:
    """Test double for embeddings and similarity."""

    async def embed_batch(self, texts):
        """Return deterministic embeddings based on skill name."""

        mapping = {
            "Python": [1.0, 0.0],
            "FastAPI": [0.9, 0.1],
            "Kubernetes": [0.0, 1.0]
        }
        return [mapping.get(text, [0.0, 0.0]) for text in texts]

    def weighted_average(self, vectors, weights):
        """Return the first vector for deterministic assertions."""

        return vectors[0] if vectors else []

    def cosine_similarity(self, left, right):
        """Compute a simple dot-product similarity for tests."""

        if not left or not right:
            return 0.0
        return sum(x * y for x, y in zip(left, right))


class FakeLLMService:
    """Test double for job parsing and recommendations."""

    async def parse_job_requirements(self, job_description: str):
        """Return fixed extracted requirements."""

        return JobRequirementsPromptResponse(
            required_skills=["Python"],
            preferred_skills=["Kubernetes"],
            min_experience_years=2,
            role_level="mid"
        )

    async def generate_recommendations(self, candidate_summary, matched_skills, missing_skills):
        """Return a short deterministic recommendation list."""

        return ["Add Kubernetes hands-on experience."]


@pytest.mark.asyncio
async def test_matching_agent_returns_gap_analysis() -> None:
    """The matching agent should produce both matches and missing skills."""

    agent = MatchingAgent(embedding_service=FakeEmbeddingService(), llm_service=FakeLLMService())
    profile = SkillProfile.model_validate(
        {
            "normalized_skills": [
                {
                    "name": "Python",
                    "aliases": ["py"],
                    "category": "Programming Languages",
                    "subcategory": "General Purpose",
                    "proficiency": "advanced",
                    "proficiency_weight": 0.75,
                    "years_experience": 4,
                    "inferred": False,
                    "emerging": False,
                    "source_skill": "Python",
                    "confidence": 1.0,
                    "normalization_tier": "exact"
                }
            ]
        }
    )

    message = await agent.run(job_id="job-1", skill_profile=profile, job_description="Need Python and Kubernetes")

    assert message.payload["match_result"]["matched_skills"][0]["skill"] == "Python"
    assert message.payload["match_result"]["missing_skills"][0]["skill"] == "Kubernetes"
