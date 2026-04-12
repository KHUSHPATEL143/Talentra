"""Tests for recruiter pipeline application merging."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.routes.jobs_v3 import _application_pipeline_identifier, _merge_rankings_with_applications
from app.models.schemas_v3 import RankedCandidate


def _job(remote: bool = False):
    """Build a tiny job stub for recruiter pipeline tests."""

    return SimpleNamespace(id="job-1", remote=remote)


def _ranking(candidate_id: str, pipeline_stage: str = "new") -> RankedCandidate:
    """Build a minimal ranked-candidate payload for merge tests."""

    return RankedCandidate.model_validate(
        {
            "candidate_id": candidate_id,
            "job_id": "job-1",
            "final_score": 82.5,
            "grade": "A",
            "location_status": "local",
            "distance_km": 8.0,
            "pipeline_stage": pipeline_stage,
            "candidate_name": "Existing Candidate",
            "location_label": "Ahmedabad, India",
            "top_skills": ["React"],
            "verification_score": 85.0,
            "skill_breakdown": [],
            "missing_required": [],
            "strongest_projects": [],
            "score_breakdown": {
                "skill_score": 80.0,
                "experience_score": 85.0,
                "project_score": 78.0,
                "verification_score": 85.0,
            },
            "recommendation": "Strong match.",
        }
    )


def test_merge_rankings_with_applications_keeps_direct_apply_entries() -> None:
    """Direct employee applications should appear even when live matcher output is empty."""

    application = SimpleNamespace(
        id="app-1",
        employee_id="employee-1",
        candidate_id=None,
        job_id="job-1",
        source="direct_apply",
        candidate_data={"employee_name": "Employee One", "location": "Ahmedabad, India"},
        match_result={
            "candidate_id": "employee-1",
            "job_id": "job-1",
            "final_score": 0.0,
            "grade": "F",
            "location_status": "local",
            "distance_km": None,
            "pipeline_stage": "new",
            "candidate_name": "Employee One",
            "location_label": "Ahmedabad, India",
            "top_skills": ["React"],
            "verification_score": 78.0,
            "skill_breakdown": [],
            "missing_required": ["Python"],
            "strongest_projects": [],
            "score_breakdown": {
                "skill_score": 0.0,
                "experience_score": 0.0,
                "project_score": 0.0,
                "verification_score": 78.0,
            },
            "recommendation": "Application received.",
        },
        final_score=0.0,
        pipeline_stage="new",
    )

    merged = _merge_rankings_with_applications(_job(), [], [application])

    assert len(merged) == 1
    assert merged[0].candidate_id == "employee-1"
    assert merged[0].candidate_name == "Employee One"
    assert merged[0].pipeline_stage == "new"


def test_merge_rankings_with_applications_uses_application_id_for_form_submissions() -> None:
    """Anonymous public-form submissions should still get a stable pipeline identifier."""

    application = SimpleNamespace(
        id="app-form-1",
        employee_id=None,
        candidate_id=None,
        job_id="job-1",
        source="form",
        candidate_data={"name": "Form Applicant", "location": "Pune, India"},
        match_result={},
        final_score=0.0,
        pipeline_stage="new",
    )

    merged = _merge_rankings_with_applications(_job(remote=True), [], [application])

    assert len(merged) == 1
    assert _application_pipeline_identifier(application) == "app-form-1"
    assert merged[0].candidate_id == "app-form-1"
    assert merged[0].candidate_name == "Form Applicant"
    assert merged[0].grade == "Pending"
    assert merged[0].location_status == "remote"


def test_merge_rankings_with_applications_overlays_pipeline_stage() -> None:
    """Existing ranked candidates should inherit their persisted recruiter stage."""

    application = SimpleNamespace(
        id="app-2",
        employee_id="employee-1",
        candidate_id=None,
        job_id="job-1",
        source="direct_apply",
        candidate_data={"employee_name": "Employee One"},
        match_result={},
        final_score=81.0,
        pipeline_stage="interview",
    )

    merged = _merge_rankings_with_applications(_job(), [_ranking("employee-1")], [application])

    assert len(merged) == 1
    assert merged[0].candidate_id == "employee-1"
    assert merged[0].pipeline_stage == "interview"
