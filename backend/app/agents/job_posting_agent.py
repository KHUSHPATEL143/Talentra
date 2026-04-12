"""Agent for structuring recruiter job postings into normalized data."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas_v3 import JobPostingCreateRequest, JobPostingExtraction, JobPostingStructuredInput
from app.services.geocoding_service import GeocodingService
from app.services.llm_service import LLMService
from app.services.taxonomy_service import TaxonomyService


@dataclass(slots=True)
class StructuredJobPosting:
    """Normalized recruiter job payload ready for persistence."""

    title: str
    company: str
    description: str
    location_city: str
    location_state: str
    location_country: str
    lat: float | None
    lng: float | None
    radius_km: int
    accept_relocation: bool
    remote: bool
    hybrid: bool
    employment_type: str
    experience_min: int
    experience_max: int | None
    salary_min: int | None
    salary_max: int | None
    currency: str
    required_skills: list[dict]
    preferred_skills: list[dict]
    auto_shortlist_threshold: float
    structured_requirements: dict
    application_deadline: object | None


class JobPostingAgent:
    """Convert pasted or form-based JDs into structured recruiter jobs."""

    def __init__(
        self,
        llm_service: LLMService,
        taxonomy_service: TaxonomyService,
        geocoding_service: GeocodingService,
    ) -> None:
        """Store the shared services used during job creation."""

        self.llm_service = llm_service
        self.taxonomy_service = taxonomy_service
        self.geocoding_service = geocoding_service

    async def run(self, payload: JobPostingCreateRequest, company_name: str) -> StructuredJobPosting:
        """Normalize a recruiter job creation request."""

        if payload.structured:
            structured = payload.structured
        elif payload.raw_jd:
            structured = await self._parse_raw_jd(payload.raw_jd, company_name)
        else:
            raise ValueError("Either raw_jd or structured job data is required.")

        location_text = ", ".join(
            part for part in [structured.location_city, structured.location_state, structured.location_country] if part
        )
        coordinates = await self.geocoding_service.geocode(location_text)
        normalized_required = await self._normalize_skill_requirements(structured.required_skills)
        normalized_preferred = await self._normalize_skill_requirements(structured.preferred_skills)
        structured_requirements = {
            "required_skills": normalized_required,
            "preferred_skills": normalized_preferred,
            "experience_min": structured.experience_min,
            "experience_max": structured.experience_max,
            "employment_type": structured.employment_type,
        }
        return StructuredJobPosting(
            title=structured.title,
            company=structured.company or company_name,
            description=structured.description,
            location_city=structured.location_city,
            location_state=structured.location_state,
            location_country=structured.location_country,
            lat=coordinates[0] if coordinates else None,
            lng=coordinates[1] if coordinates else None,
            radius_km=structured.radius_km,
            accept_relocation=structured.accept_relocation,
            remote=structured.remote,
            hybrid=structured.hybrid,
            employment_type=structured.employment_type,
            experience_min=structured.experience_min,
            experience_max=structured.experience_max,
            salary_min=structured.salary_min,
            salary_max=structured.salary_max,
            currency=structured.currency,
            required_skills=normalized_required,
            preferred_skills=normalized_preferred,
            auto_shortlist_threshold=structured.auto_shortlist_threshold,
            structured_requirements=structured_requirements,
            application_deadline=structured.application_deadline,
        )

    async def _parse_raw_jd(self, raw_jd: str, company_name: str) -> JobPostingStructuredInput:
        """Use the LLM to extract a structured job payload from freeform text."""

        system_prompt = (
            "You structure recruiter job descriptions into strict JSON. Extract title, company, location, "
            "work mode, experience range, salary, responsibilities, qualifications, benefits, required skills, "
            "and preferred skills. Prefer conservative extraction and leave optional values empty if missing."
        )
        user_prompt = f"JOB DESCRIPTION:\n{raw_jd}"
        extracted = await self.llm_service.structured_completion(
            "job_posting_extraction",
            JobPostingExtraction,
            system_prompt,
            user_prompt,
        )
        return JobPostingStructuredInput(
            title=extracted.title or "Untitled Role",
            company=extracted.company or company_name,
            description=raw_jd,
            location_city=extracted.location_city,
            location_state=extracted.location_state,
            location_country=extracted.location_country,
            remote=extracted.remote,
            hybrid=extracted.hybrid,
            accept_relocation=extracted.accept_relocation,
            employment_type=extracted.employment_type,
            experience_min=extracted.experience_min,
            experience_max=extracted.experience_max,
            salary_min=extracted.salary_min,
            salary_max=extracted.salary_max,
            currency=extracted.currency,
            required_skills=extracted.required_skills,
            preferred_skills=extracted.preferred_skills,
            auto_shortlist_threshold=extracted.auto_shortlist_threshold,
            radius_km=extracted.radius_km,
            application_deadline=extracted.application_deadline,
        )

    async def _normalize_skill_requirements(self, requirements: list) -> list[dict]:
        """Map recruiter-entered skills into the canonical taxonomy when possible."""

        normalized: list[dict] = []
        for requirement in requirements:
            match = self.taxonomy_service.exact_match(requirement.skill)
            if not match:
                match, _ = self.taxonomy_service.fuzzy_match(requirement.skill)
            canonical_name = match["canonical_name"] if match else requirement.skill
            normalized.append(
                {
                    "skill": canonical_name,
                    "min_years": requirement.min_years,
                    "weight": requirement.weight,
                }
            )
        return normalized
