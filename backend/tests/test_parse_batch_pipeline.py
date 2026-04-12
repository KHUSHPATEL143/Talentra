"""Tests for recruiter-linked batch parsing helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.routes.parse import _build_parsed_candidate_context, _fallback_candidate_ranking


@pytest.mark.asyncio
async def test_build_parsed_candidate_context_uses_resume_location_and_skills() -> None:
    """Parsed resume data should map into a role-matcher candidate context cleanly."""

    captured = {}

    async def fake_geocode(*_args):
        return (23.02, 72.57)

    class FakeRoleMatcher:
        def build_candidate_context(self, **kwargs):
            captured.update(kwargs)
            return kwargs

    app = SimpleNamespace(
        state=SimpleNamespace(
            geocoding_service=SimpleNamespace(geocode=fake_geocode),
            role_matcher=FakeRoleMatcher(),
        )
    )
    candidate = SimpleNamespace(
        id="candidate-1",
        name="Resume Candidate",
        profile_json={
            "candidate_profile": {
                "location": {"city": "Ahmedabad", "country": "India"},
                "projects": [{"name": "React Console", "technologies": ["React"]}],
            },
            "skill_profile": {
                "normalized_skills": [
                    {"name": "React", "years_experience": 2, "proficiency": "advanced"},
                    {"name": "JavaScript", "years_experience": 3, "proficiency": "advanced"},
                ],
                "total_experience_years": 3,
            },
        },
    )

    context = await _build_parsed_candidate_context(app, candidate)

    assert context["candidate_id"] == "candidate-1"
    assert context["location_label"] == "Ahmedabad, India"
    assert context["coordinates"] == (23.02, 72.57)
    assert [item["canonical_name"] for item in context["verified_skills"]] == ["React", "JavaScript"]
    assert captured["total_years"] == 3


def test_fallback_candidate_ranking_keeps_resume_upload_visible() -> None:
    """Filtered-out recruiter resume uploads should still render as visible fallback rows."""

    candidate = SimpleNamespace(
        id="candidate-2",
        name="Fallback Candidate",
        profile_json={
            "candidate_profile": {"location": {"city": "Pune", "country": "India"}},
            "skill_profile": {"normalized_skills": [{"name": "Python"}]},
        },
    )
    job = SimpleNamespace(id="job-1", remote=False, required_skills=[{"skill": "React"}, {"skill": "JavaScript"}])

    ranking = _fallback_candidate_ranking(candidate, job)

    assert ranking.candidate_id == "candidate-2"
    assert ranking.candidate_name == "Fallback Candidate"
    assert ranking.grade == "F"
    assert ranking.location_status == "local"
    assert ranking.missing_required == ["React", "JavaScript"]
