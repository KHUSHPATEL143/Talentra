"""Tests for the TalentOS v3 employee verification slice."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.routes.employees_v3 import _verify_claimed_skills
from app.agents.career_coach_agent import CareerCoachAgent
from app.agents.role_matcher import RoleMatcher


class FakeEmbeddingService:
    """Deterministic embeddings for employee job-board tests."""

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text value."""

        return self._vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""

        return [self._vector(text) for text in texts]

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        """Simple dot-product similarity for deterministic tests."""

        return sum(x * y for x, y in zip(left, right))

    def _vector(self, text: str) -> list[float]:
        normalized = (text or "").lower()
        if "react" in normalized:
            return [1.0, 0.0, 0.0]
        if "typescript" in normalized:
            return [0.8, 0.2, 0.0]
        if "python" in normalized:
            return [0.2, 0.8, 0.0]
        return [0.1, 0.1, 0.8]


class FakeTaxonomyService:
    """Small taxonomy stub for verification tests."""

    def exact_match(self, raw_skill: str):
        mapping = {
            "react.js": {"canonical_name": "React"},
            "react": {"canonical_name": "React"},
            "python": {"canonical_name": "Python"},
            "algorithms": {"canonical_name": "Algorithms"},
        }
        return mapping.get(raw_skill.strip().lower())

    def fuzzy_match(self, raw_skill: str, threshold: int = 85):
        return None, 0.0


def test_verify_claimed_skills_promotes_supported_claims() -> None:
    """Project and LinkedIn evidence should upgrade supported skill claims."""

    social = SimpleNamespace(
        github_data={
            "projects": [
                {
                    "name": "React Commerce",
                    "description": "React storefront with reusable components",
                    "languages": ["JavaScript"],
                    "topics": ["react"],
                    "stars": 12,
                    "has_tests": True,
                    "has_ci": True,
                }
            ]
        },
        linkedin_data={"skills_listed": ["React", "Python"], "experience_years": 3},
        leetcode_data={"hard": 42, "languages_used": ["Python"]},
    )

    skills, unverified_claims, verification_score = _verify_claimed_skills(
        ["React.js", "Python", "Algorithms"],
        social,
        FakeTaxonomyService(),
    )

    skill_map = {item["canonical_name"]: item for item in skills}
    assert skill_map["React"]["verification_tier"] == "VERIFIED"
    assert skill_map["React"]["production_grade"] is True
    assert skill_map["Python"]["verification_tier"] in {"CONFIRMED", "SELF_DECLARED"}
    assert skill_map["Algorithms"]["verification_tier"] == "CONFIRMED"
    assert unverified_claims == []
    assert verification_score > 0.7


@pytest.mark.asyncio
async def test_score_candidate_for_job_returns_employee_preview() -> None:
    """The employee job board should be able to score one supplied candidate context."""

    matcher = RoleMatcher(embedding_service=FakeEmbeddingService(), geocoding_service=SimpleNamespace(haversine_km=lambda *args: 8.0))
    candidate = matcher.build_candidate_context(
        candidate_id="employee-1",
        name="Employee One",
        location_label="Ahmedabad, India",
        coordinates=(23.03, 72.58),
        open_to_relocation=False,
        verified_skills=[
            {"canonical_name": "React", "verification_tier": "VERIFIED", "years": 3},
            {"canonical_name": "TypeScript", "verification_tier": "CONFIRMED", "years": 2},
        ],
        total_years=4,
        projects=[{"name": "React Commerce", "description": "React storefront", "technologies": ["React", "TypeScript"]}],
    )
    job = SimpleNamespace(
        id="job-1",
        description="React developer in Ahmedabad",
        radius_km=50,
        accept_relocation=True,
        remote=False,
        lat=23.0225,
        lng=72.5714,
        required_skills=[{"skill": "React", "min_years": 2, "weight": 1.0}],
        preferred_skills=[{"skill": "TypeScript", "min_years": 1, "weight": 0.5}],
        experience_min=2,
        auto_shortlist_threshold=70.0,
        min_coverage_threshold=0.5,
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )

    ranking = await matcher.score_candidate_for_job(job, candidate)

    assert ranking is not None
    assert ranking.location_status == "local"
    assert ranking.final_score > 70
    assert "React" in ranking.top_skills


@pytest.mark.asyncio
async def test_career_coach_agent_recommends_missing_skills() -> None:
    """Career coach should recommend repeated missing skills across matching jobs."""

    matcher = RoleMatcher(embedding_service=FakeEmbeddingService(), geocoding_service=SimpleNamespace(haversine_km=lambda *args: 8.0))
    candidate = matcher.build_candidate_context(
        candidate_id="employee-1",
        name="Employee One",
        location_label="Ahmedabad, India",
        coordinates=(23.03, 72.58),
        open_to_relocation=False,
        verified_skills=[{"canonical_name": "React", "verification_tier": "VERIFIED", "years": 3}],
        total_years=4,
        projects=[{"name": "React Commerce", "description": "React storefront", "technologies": ["React"]}],
    )

    class FakeSession:
        def __init__(self):
            self.saved = None

        async def execute(self, _query):
            jobs = [
                SimpleNamespace(
                    id="job-1",
                    title="Frontend Engineer",
                    company="Acme",
                    description="React and TypeScript role",
                    radius_km=50,
                    accept_relocation=True,
                    remote=False,
                    visibility="public",
                    status="active",
                    lat=23.0225,
                    lng=72.5714,
                    required_skills=[{"skill": "React", "min_years": 2, "weight": 1.0}, {"skill": "TypeScript", "min_years": 1, "weight": 1.0}],
                    preferred_skills=[],
                    experience_min=2,
                    auto_shortlist_threshold=70.0,
                    min_coverage_threshold=0.0,
                    created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                ),
                SimpleNamespace(
                    id="job-2",
                    title="UI Engineer",
                    company="Beta",
                    description="React with TypeScript and design systems",
                    radius_km=50,
                    accept_relocation=True,
                    remote=False,
                    visibility="public",
                    status="active",
                    lat=23.0225,
                    lng=72.5714,
                    required_skills=[{"skill": "React", "min_years": 2, "weight": 1.0}, {"skill": "TypeScript", "min_years": 1, "weight": 1.0}],
                    preferred_skills=[],
                    experience_min=2,
                    auto_shortlist_threshold=70.0,
                    min_coverage_threshold=0.0,
                    created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                ),
            ]
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: jobs))

        async def scalar(self, _query):
            return self.saved

        def add(self, value):
            self.saved = value

        async def commit(self):
            return None

        async def refresh(self, _value):
            return None

    session = FakeSession()
    coach = CareerCoachAgent(role_matcher=matcher)
    suggestion = await coach.run(
        session=session,
        employee=SimpleNamespace(id="emp-1"),
        social=SimpleNamespace(),
        verified=SimpleNamespace(),
        candidate_context=candidate,
    )

    assert suggestion.recommended_skills
    assert suggestion.recommended_skills[0]["skill"] == "TypeScript"
