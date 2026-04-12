"""Matching agent tests."""

from __future__ import annotations

import pytest

from app.agents.matching_agent import MatchingAgent
from app.models.schemas import JobRequirementsPromptResponse, RecommendationResponse, SkillProfile
from app.services.job_heuristics import JobHeuristicService


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

    def __init__(self) -> None:
        self.parse_calls = 0
        self.recommendation_calls = 0

    async def parse_job_requirements(self, job_description: str):
        """Return fixed extracted requirements."""

        self.parse_calls += 1
        return JobRequirementsPromptResponse(
            required_skills=["Python"],
            preferred_skills=["Kubernetes"],
            min_experience_years=2,
            role_level="mid"
        )

    async def generate_recommendations(self, candidate_summary, matched_skills, missing_skills):
        """Return a short deterministic recommendation list."""

        self.recommendation_calls += 1
        return ["Add Kubernetes hands-on experience."]


@pytest.mark.asyncio
async def test_matching_agent_returns_gap_analysis() -> None:
    """The matching agent should produce both matches and missing skills."""

    heuristic_service = JobHeuristicService(["Python", "Kubernetes", "FastAPI"])
    agent = MatchingAgent(
        embedding_service=FakeEmbeddingService(),
        llm_service=FakeLLMService(),
        job_heuristic_service=heuristic_service,
    )
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


@pytest.mark.asyncio
async def test_matching_agent_falls_back_to_heuristics_when_llm_unavailable() -> None:
    """The matching agent should still score a JD when the LLM is unavailable."""

    class FailingLLMService:
        async def parse_job_requirements(self, job_description: str):
            raise RuntimeError("provider unavailable")

        async def generate_recommendations(self, candidate_summary, matched_skills, missing_skills):
            raise RuntimeError("provider unavailable")

    heuristic_service = JobHeuristicService(["Python", "FastAPI", "Docker"])
    agent = MatchingAgent(
        embedding_service=FakeEmbeddingService(),
        llm_service=FailingLLMService(),
        job_heuristic_service=heuristic_service,
    )
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

    message = await agent.run(job_id="job-2", skill_profile=profile, job_description="Senior backend engineer with 3 years of experience in Python and Docker.")

    assert message.payload["match_result"]["parsed_requirements"]["required_skills"]
    assert message.payload["match_result"]["recommendations"]


@pytest.mark.asyncio
async def test_matching_agent_skips_llm_when_heuristics_are_sufficient() -> None:
    """The matching agent should save API usage when the JD is easy to parse heuristically."""

    llm = FakeLLMService()
    heuristic_service = JobHeuristicService(["Python", "FastAPI", "Docker", "PostgreSQL"])
    agent = MatchingAgent(
        embedding_service=FakeEmbeddingService(),
        llm_service=llm,
        job_heuristic_service=heuristic_service,
    )
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
                },
                {
                    "name": "Docker",
                    "aliases": [],
                    "category": "DevOps",
                    "subcategory": "Containers",
                    "proficiency": "intermediate",
                    "proficiency_weight": 0.5,
                    "years_experience": 2,
                    "inferred": False,
                    "emerging": False,
                    "source_skill": "Docker",
                    "confidence": 1.0,
                    "normalization_tier": "exact"
                }
            ]
        }
    )

    message = await agent.run(
        job_id="job-3",
        skill_profile=profile,
        job_description="Senior backend engineer with 3 years of experience in Python, Docker, and PostgreSQL.",
    )

    assert llm.parse_calls == 0
    assert llm.recommendation_calls == 0
    assert message.payload["match_result"]["parsed_requirements"]["required_skills"]
    assert message.payload["match_result"]["recommendations"]
