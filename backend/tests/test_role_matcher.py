"""Tests for the TalentOS v3 role matcher."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.role_matcher import CandidateContext, RoleMatcher


class FakeEmbeddingService:
    """Deterministic embeddings for recruiter ranking tests."""

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


@pytest.mark.asyncio
async def test_role_matcher_sorts_local_candidates_before_relocation() -> None:
    """Local qualified candidates should rank ahead of relocation candidates."""

    matcher = RoleMatcher(embedding_service=FakeEmbeddingService(), geocoding_service=SimpleNamespace(haversine_km=lambda *args: 12.0))
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

    local_strong = CandidateContext(
        candidate_id="cand-local-1",
        name="Local Strong",
        location_label="Ahmedabad, India",
        coordinates=(23.03, 72.58),
        open_to_relocation=False,
        verified_skills=[
            {"canonical_name": "React", "verification_tier": "VERIFIED", "years": 3},
            {"canonical_name": "TypeScript", "verification_tier": "CONFIRMED", "years": 2},
        ],
        verification_score=0.92,
        total_years=4,
        projects=[{"name": "React Commerce", "description": "React storefront", "technologies": ["React", "TypeScript"]}],
    )
    local_mid = CandidateContext(
        candidate_id="cand-local-2",
        name="Local Mid",
        location_label="Ahmedabad, India",
        coordinates=(23.02, 72.57),
        open_to_relocation=False,
        verified_skills=[{"canonical_name": "React", "verification_tier": "CONFIRMED", "years": 2}],
        verification_score=0.8,
        total_years=2.5,
        projects=[{"name": "React Dashboard", "description": "React admin app", "technologies": ["React"]}],
    )
    relocation = CandidateContext(
        candidate_id="cand-relocate",
        name="Relocation Candidate",
        location_label="Mumbai, India",
        coordinates=(19.07, 72.87),
        open_to_relocation=True,
        verified_skills=[
            {"canonical_name": "React", "verification_tier": "VERIFIED", "years": 4},
            {"canonical_name": "TypeScript", "verification_tier": "VERIFIED", "years": 3},
        ],
        verification_score=1.0,
        total_years=5,
        projects=[{"name": "React Platform", "description": "Advanced React and TypeScript app", "technologies": ["React", "TypeScript"]}],
    )
    too_far = CandidateContext(
        candidate_id="cand-too-far",
        name="Too Far",
        location_label="Delhi, India",
        coordinates=(28.61, 77.20),
        open_to_relocation=False,
        verified_skills=[{"canonical_name": "React", "verification_tier": "VERIFIED", "years": 5}],
        verification_score=1.0,
        total_years=5,
        projects=[],
    )
    underqualified = CandidateContext(
        candidate_id="cand-underqualified",
        name="Underqualified",
        location_label="Ahmedabad, India",
        coordinates=(23.02, 72.57),
        open_to_relocation=False,
        verified_skills=[{"canonical_name": "Python", "verification_tier": "VERIFIED", "years": 4}],
        verification_score=1.0,
        total_years=4,
        projects=[],
    )

    async def fake_pool(_session):
        return [relocation, too_far, local_mid, local_strong, underqualified]

    matcher._load_candidate_pool = fake_pool  # type: ignore[method-assign]
    matcher.location_eligible = lambda candidate, _: (
        (True, "local", 12.0)
        if candidate.candidate_id.startswith("cand-local")
        else (True, "relocation", 440.0)
        if candidate.candidate_id == "cand-relocate"
        else (False, "out_of_range", 900.0)
    )

    rankings = await matcher.run(session=None, job=job)

    assert [item.candidate_id for item in rankings] == ["cand-local-1", "cand-local-2", "cand-relocate"]
    assert rankings[0].location_status == "local"
    assert rankings[-1].location_status == "relocation"
