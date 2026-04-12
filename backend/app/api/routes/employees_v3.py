"""Employee profile, verification, and job-board routes for TalentOS v3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db_v3 import Employee, JobPosting, SocialProfile, VerifiedSkillProfile
from app.models.schemas_v3 import (
    EmployeeJobBoardItem,
    EmployeeJobBoardResponse,
    EmployeeJobMatchPreview,
    EmployeeProfileResponse,
    EmployeeProfileUpdateRequest,
    JobSkillRequirement,
)
from app.services.auth_service import require_employee

router = APIRouter(tags=["TalentOS Employee"])

LANGUAGE_SKILL_MAP = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "react": "javascript",
    "next.js": "javascript",
    "nextjs": "javascript",
    "vue.js": "javascript",
    "angular": "typescript",
    "fastapi": "python",
    "django": "python",
    "flask": "python",
    "pytorch": "python",
    "tensorflow": "python",
    "node.js": "javascript",
    "nodejs": "javascript",
}

VERIFICATION_WEIGHTS = {
    "VERIFIED": 1.0,
    "CONFIRMED": 0.85,
    "SELF_DECLARED": 0.65,
    "UNVERIFIED": 0.4,
}


def _empty_social_payload() -> dict[str, Any]:
    """Return the default JSON payload used for new social profiles."""

    return {"claimed_skills": [], "projects": []}


async def _get_or_create_social_profile(session: AsyncSession, employee: Employee) -> SocialProfile:
    """Load or initialize the employee social profile row."""

    social = await session.scalar(select(SocialProfile).where(SocialProfile.employee_id == employee.id))
    if social is not None:
        social.github_data = social.github_data or _empty_social_payload()
        social.linkedin_data = social.linkedin_data or {}
        social.leetcode_data = social.leetcode_data or {}
        return social

    social = SocialProfile(
        employee_id=employee.id,
        github_data=_empty_social_payload(),
        linkedin_data={},
        leetcode_data={},
        scrape_status="pending",
    )
    session.add(social)
    await session.flush()
    return social


async def _get_or_create_verified_profile(session: AsyncSession, employee: Employee) -> VerifiedSkillProfile:
    """Load or initialize the employee verified skill profile row."""

    profile = await session.scalar(select(VerifiedSkillProfile).where(VerifiedSkillProfile.employee_id == employee.id))
    if profile is not None:
        return profile
    profile = VerifiedSkillProfile(employee_id=employee.id, skills=[], unverified_claims=[], verification_score=0.0, profile_completeness=0.0)
    session.add(profile)
    await session.flush()
    return profile


def _location_label(employee: Employee) -> str:
    """Build a display label for the employee location."""

    return ", ".join(part for part in [employee.location_city, employee.location_country] if part)


def _project_payload(project: dict[str, Any]) -> dict[str, Any]:
    """Normalize project JSON shape for API responses."""

    return {
        "name": project.get("name", ""),
        "description": project.get("description", ""),
        "url": project.get("url", ""),
        "languages": list(project.get("languages", [])),
        "topics": list(project.get("topics", [])),
        "stars": int(project.get("stars", 0) or 0),
        "has_tests": bool(project.get("has_tests", False)),
        "has_ci": bool(project.get("has_ci", False)),
    }


def _compute_profile_completeness(employee: Employee, social: SocialProfile, verified: VerifiedSkillProfile) -> float:
    """Estimate overall employee profile completeness."""

    claimed_skills = social.github_data.get("claimed_skills", [])
    projects = social.github_data.get("projects", [])
    linkedin_data = social.linkedin_data or {}
    leetcode_data = social.leetcode_data or {}
    checks = [
        bool(employee.location_city),
        bool(claimed_skills),
        bool(social.github_username or projects),
        bool(linkedin_data.get("current_role") or social.linkedin_url),
        bool(social.leetcode_username or leetcode_data.get("languages_used")),
        bool(verified.skills),
    ]
    return round(sum(1 for item in checks if item) / len(checks), 2)


def _canonicalize_skill(raw_skill: str, taxonomy_service) -> str:
    """Resolve a skill name to the closest canonical taxonomy entry."""

    stripped = raw_skill.strip()
    if not stripped:
        return ""
    exact = taxonomy_service.exact_match(stripped)
    if exact:
        return exact["canonical_name"]
    fuzzy, score = taxonomy_service.fuzzy_match(stripped)
    if fuzzy and score >= 0.8:
        return fuzzy["canonical_name"]
    return stripped


def _skill_matches(project: dict[str, Any], skill_name: str) -> tuple[bool, str]:
    """Check whether a project provides evidence for a skill and at what strength."""

    normalized_skill = skill_name.strip().lower()
    languages = [str(item).strip().lower() for item in project.get("languages", [])]
    topics = [str(item).strip().lower() for item in project.get("topics", [])]
    haystack = " ".join(
        [
            str(project.get("name", "")),
            str(project.get("description", "")),
            " ".join(topics),
        ]
    ).lower()
    mapped_language = LANGUAGE_SKILL_MAP.get(normalized_skill)

    if normalized_skill in languages or (mapped_language and mapped_language in languages):
        return True, "STRONG"
    if normalized_skill in topics:
        return True, "MODERATE"
    if normalized_skill and normalized_skill in haystack:
        return True, "WEAK"
    return False, ""


def _verification_tier(evidence: list[dict[str, Any]]) -> str:
    """Assign the final verification tier from evidence rows."""

    strong_count = sum(1 for item in evidence if item["strength"] == "STRONG")
    moderate_count = sum(1 for item in evidence if item["strength"] in {"STRONG", "MODERATE"})
    if strong_count >= 2:
        return "VERIFIED"
    if strong_count >= 1 and moderate_count >= 2:
        return "VERIFIED"
    if strong_count >= 1:
        return "CONFIRMED"
    if moderate_count >= 2:
        return "CONFIRMED"
    if evidence:
        return "SELF_DECLARED"
    return "UNVERIFIED"


def _verify_claimed_skills(claimed_skills: list[str], social: SocialProfile, taxonomy_service) -> tuple[list[dict[str, Any]], list[str], float]:
    """Build a verified skill profile from manual social evidence."""

    github_projects = [
        _project_payload(project)
        for project in social.github_data.get("projects", [])
        if isinstance(project, dict)
    ]
    linkedin_skills = {str(item).strip().lower() for item in social.linkedin_data.get("skills_listed", [])}
    linkedin_years = float(social.linkedin_data.get("experience_years", 0.0) or 0.0)
    leetcode_languages = {str(item).strip().lower() for item in social.leetcode_data.get("languages_used", [])}
    leetcode_hard = int(social.leetcode_data.get("hard", 0) or 0)

    verified_skills: list[dict[str, Any]] = []
    for raw_skill in claimed_skills:
        canonical_name = _canonicalize_skill(raw_skill, taxonomy_service)
        if not canonical_name:
            continue
        evidence: list[dict[str, Any]] = []
        matching_projects: list[dict[str, Any]] = []
        for project in github_projects:
            matched, strength = _skill_matches(project, canonical_name)
            if matched:
                evidence.append(
                    {
                        "source": "github",
                        "repo": project["name"],
                        "type": "project_signal",
                        "strength": strength,
                    }
                )
                matching_projects.append(project)

        normalized_skill = canonical_name.strip().lower()
        if normalized_skill in linkedin_skills:
            evidence.append({"source": "linkedin", "type": "listed_skill", "strength": "WEAK"})
        if normalized_skill in leetcode_languages and normalized_skill in {"python", "javascript", "java", "c++"}:
            evidence.append({"source": "leetcode", "type": "language_practice", "strength": "MODERATE"})
        if normalized_skill in {"algorithms", "data structures"} and leetcode_hard > 30:
            evidence.append({"source": "leetcode", "type": "hard_problems", "strength": "STRONG"})

        tier = _verification_tier(evidence)
        strongest_projects = [project for project in matching_projects if any(item["strength"] == "STRONG" and item.get("repo") == project["name"] for item in evidence)]
        verified_skills.append(
            {
                "canonical_name": canonical_name,
                "verification_tier": tier,
                "evidence": evidence,
                "proficiency": "advanced" if tier == "VERIFIED" else "intermediate" if tier == "CONFIRMED" else "developing",
                "years": linkedin_years,
                "production_grade": any(project["has_tests"] and project["has_ci"] and project["stars"] > 5 for project in strongest_projects),
                "community_validation": any(project["stars"] > 20 for project in strongest_projects),
            }
        )

    unverified_claims = [item["canonical_name"] for item in verified_skills if item["verification_tier"] == "UNVERIFIED"]
    kept_skills = [item for item in verified_skills if item["canonical_name"]]
    score = round(
        sum(VERIFICATION_WEIGHTS.get(item["verification_tier"], 0.4) for item in kept_skills) / max(len(kept_skills), 1),
        2,
    ) if kept_skills else 0.0
    return kept_skills, unverified_claims, score


def _employee_response(employee: Employee, social: SocialProfile, verified: VerifiedSkillProfile) -> EmployeeProfileResponse:
    """Serialize an employee dashboard response."""

    return EmployeeProfileResponse(
        employee_id=employee.id,
        name=employee.name,
        email=employee.email,
        location=_location_label(employee),
        coordinates={"lat": employee.lat, "lng": employee.lng} if employee.lat is not None and employee.lng is not None else None,
        open_to_relocation=employee.open_to_relocation,
        claimed_skills=list(social.github_data.get("claimed_skills", [])),
        github_username=social.github_username or "",
        linkedin_url=social.linkedin_url or "",
        leetcode_username=social.leetcode_username or "",
        github_projects=[_project_payload(project) for project in social.github_data.get("projects", []) if isinstance(project, dict)],
        linkedin_manual=social.linkedin_data or {},
        leetcode_manual=social.leetcode_data or {},
        scrape_status=social.scrape_status,
        profile_completeness=employee.profile_completeness,
        verification_score=verified.verification_score,
        verified_skills=verified.skills,
        unverified_claims=verified.unverified_claims,
    )


async def _build_employee_candidate_context(employee: Employee, social: SocialProfile, verified: VerifiedSkillProfile, request: Request):
    """Build a RoleMatcher candidate context from employee-owned profile data."""

    verified_skills = list(verified.skills or [])
    if not verified_skills:
        verified_skills = [
            {
                "canonical_name": skill,
                "verification_tier": "SELF_DECLARED",
                "years": float((social.linkedin_data or {}).get("experience_years", 0.0) or 0.0),
                "proficiency": "developing",
            }
            for skill in social.github_data.get("claimed_skills", [])
        ]
    projects = [_project_payload(project) for project in social.github_data.get("projects", []) if isinstance(project, dict)]
    return request.app.state.role_matcher.build_candidate_context(
        candidate_id=employee.id,
        name=employee.name,
        location_label=_location_label(employee),
        coordinates=(employee.lat, employee.lng) if employee.lat is not None and employee.lng is not None else None,
        open_to_relocation=employee.open_to_relocation,
        verified_skills=verified_skills,
        total_years=float((social.linkedin_data or {}).get("experience_years", 0.0) or 0.0),
        projects=projects,
    )


@router.get("/employee/profile", response_model=EmployeeProfileResponse, summary="Get employee profile")
async def get_employee_profile(
    employee: Employee = Depends(require_employee),
    session: AsyncSession = Depends(get_session),
) -> EmployeeProfileResponse:
    """Return the authenticated employee dashboard payload."""

    social = await _get_or_create_social_profile(session, employee)
    verified = await _get_or_create_verified_profile(session, employee)
    employee.profile_completeness = _compute_profile_completeness(employee, social, verified)
    await session.commit()
    return _employee_response(employee, social, verified)


@router.put("/employee/profile", response_model=EmployeeProfileResponse, summary="Update employee profile")
async def update_employee_profile(
    request: Request,
    payload: EmployeeProfileUpdateRequest,
    employee: Employee = Depends(require_employee),
    session: AsyncSession = Depends(get_session),
) -> EmployeeProfileResponse:
    """Persist employee profile and manual social evidence fields."""

    social = await _get_or_create_social_profile(session, employee)
    verified = await _get_or_create_verified_profile(session, employee)

    employee.open_to_relocation = payload.open_to_relocation
    location_value = payload.location.strip()
    if location_value:
        employee.location_city = location_value
        employee.location_country = "India"
        coordinates = await request.app.state.geocoding_service.geocode(location_value)
        employee.lat = coordinates[0] if coordinates else None
        employee.lng = coordinates[1] if coordinates else None

    social.github_username = payload.github_username.strip() or None
    social.linkedin_url = payload.linkedin_url.strip() or None
    social.leetcode_username = payload.leetcode_username.strip() or None
    social.github_data = {
        "claimed_skills": [item.strip() for item in payload.claimed_skills if item.strip()],
        "projects": [item.model_dump() for item in payload.github_projects],
    }
    social.linkedin_data = payload.linkedin_manual.model_dump()
    social.leetcode_data = payload.leetcode_manual.model_dump()
    social.scrape_status = "manual_ready"

    employee.profile_completeness = _compute_profile_completeness(employee, social, verified)
    verified.profile_completeness = employee.profile_completeness
    await session.commit()
    await session.refresh(employee)
    return _employee_response(employee, social, verified)


@router.post("/employee/verify", response_model=EmployeeProfileResponse, summary="Verify employee skills")
async def verify_employee_profile(
    request: Request,
    employee: Employee = Depends(require_employee),
    session: AsyncSession = Depends(get_session),
) -> EmployeeProfileResponse:
    """Run the employee verification pass using stored manual social evidence."""

    social = await _get_or_create_social_profile(session, employee)
    verified = await _get_or_create_verified_profile(session, employee)
    claimed_skills = list(social.github_data.get("claimed_skills", []))
    skills, unverified_claims, verification_score = _verify_claimed_skills(claimed_skills, social, request.app.state.taxonomy_service)
    verified.skills = skills
    verified.unverified_claims = unverified_claims
    verified.verification_score = verification_score
    verified.profile_completeness = _compute_profile_completeness(employee, social, verified)
    social.scrape_status = "verified" if skills else "manual_ready"
    employee.profile_completeness = verified.profile_completeness
    await session.commit()
    await session.refresh(employee)
    return _employee_response(employee, social, verified)


@router.get("/employee/jobs", response_model=EmployeeJobBoardResponse, summary="List employee job board")
async def list_employee_jobs(
    request: Request,
    employee: Employee = Depends(require_employee),
    session: AsyncSession = Depends(get_session),
) -> EmployeeJobBoardResponse:
    """Return active public jobs with employee-specific match previews when possible."""

    social = await _get_or_create_social_profile(session, employee)
    verified = await _get_or_create_verified_profile(session, employee)
    candidate = await _build_employee_candidate_context(employee, social, verified, request)

    jobs = list(
        (
            await session.execute(
                select(JobPosting).where(JobPosting.status == "active", JobPosting.visibility == "public").order_by(JobPosting.created_at.desc())
            )
        ).scalars().all()
    )
    items: list[EmployeeJobBoardItem] = []
    for job in jobs:
        ranking = await request.app.state.role_matcher.score_candidate_for_job(job, candidate)
        match_preview = None
        if ranking is not None:
            match_preview = EmployeeJobMatchPreview(
                score=ranking.final_score,
                grade=ranking.grade,
                location_status=ranking.location_status,
                distance_km=ranking.distance_km,
                top_skills=ranking.top_skills,
                missing_required=ranking.missing_required,
                recommendation=ranking.recommendation,
            )
        items.append(
            EmployeeJobBoardItem(
                id=job.id,
                title=job.title,
                company=job.company,
                location_label=", ".join(part for part in [job.location_city, job.location_state, job.location_country] if part) or "Remote",
                employment_type=job.employment_type,
                required_skills=[JobSkillRequirement.model_validate(skill) for skill in (job.required_skills or [])],
                preferred_skills=[JobSkillRequirement.model_validate(skill) for skill in (job.preferred_skills or [])],
                remote=job.remote,
                hybrid=job.hybrid,
                match_preview=match_preview,
            )
        )
    return EmployeeJobBoardResponse(items=items, total=len(items))
