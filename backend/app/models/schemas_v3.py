"""Pydantic schemas for TalentOS v3 recruiter and employee flows."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthTokenResponse(BaseModel):
    """JWT login response."""

    access_token: str
    token_type: str = "bearer"
    role: Literal["employee", "recruiter"]


class LoginRequest(BaseModel):
    """Email/password login request."""

    email: EmailStr
    password: str = Field(min_length=6)


class RecruiterRegistrationRequest(BaseModel):
    """Recruiter registration payload."""

    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)
    company_name: str = Field(min_length=1)


class EmployeeRegistrationRequest(BaseModel):
    """Employee registration payload."""

    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)
    location: str = ""
    open_to_relocation: bool = False


class RecruiterIdentity(BaseModel):
    """Authenticated recruiter identity payload."""

    user_id: str
    recruiter_id: str
    name: str
    email: EmailStr
    company_name: str
    role: Literal["recruiter"] = "recruiter"


class EmployeeIdentity(BaseModel):
    """Authenticated employee identity payload."""

    user_id: str
    employee_id: str
    name: str
    email: EmailStr
    location: str = ""
    open_to_relocation: bool = False
    role: Literal["employee"] = "employee"


class CoordinatePoint(BaseModel):
    """Latitude/longitude pair."""

    lat: float
    lng: float


class JobSkillRequirement(BaseModel):
    """Skill requirement with years and weight."""

    skill: str
    min_years: float = 0.0
    weight: float = 1.0


class JobLocationFilters(BaseModel):
    """Location controls for a posted role."""

    radius_km: int = 50
    accept_relocation: bool = True
    accept_remote: bool = False


class JobPostingStructuredInput(BaseModel):
    """Manual recruiter job creation payload."""

    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    description: str = Field(min_length=1)
    location_city: str = ""
    location_state: str = ""
    location_country: str = "India"
    remote: bool = False
    hybrid: bool = False
    accept_relocation: bool = True
    employment_type: str = "full_time"
    experience_min: int = 0
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str = "INR"
    required_skills: list[JobSkillRequirement] = Field(default_factory=list)
    preferred_skills: list[JobSkillRequirement] = Field(default_factory=list)
    auto_shortlist_threshold: float = 70.0
    radius_km: int = 50
    application_deadline: date | None = None


class JobPostingCreateRequest(BaseModel):
    """Combined job creation request supporting raw JD or structured form."""

    raw_jd: str | None = None
    structured: JobPostingStructuredInput | None = None


class JobPostingExtraction(BaseModel):
    """LLM-extracted recruiter job payload."""

    title: str = ""
    company: str = ""
    location_city: str = ""
    location_state: str = ""
    location_country: str = "India"
    remote: bool = False
    hybrid: bool = False
    accept_relocation: bool = True
    employment_type: str = "full_time"
    experience_min: int = 0
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str = "INR"
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    required_skills: list[JobSkillRequirement] = Field(default_factory=list)
    preferred_skills: list[JobSkillRequirement] = Field(default_factory=list)
    auto_shortlist_threshold: float = 70.0
    radius_km: int = 50
    application_deadline: date | None = None


class JobPostingResponse(BaseModel):
    """Recruiter job posting response."""

    id: str
    recruiter_id: str
    title: str
    company: str
    description: str
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    coordinates: CoordinatePoint | None = None
    radius_km: int
    accept_relocation: bool
    remote: bool
    hybrid: bool
    employment_type: str
    experience_min: int
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str
    required_skills: list[JobSkillRequirement]
    preferred_skills: list[JobSkillRequirement]
    auto_shortlist_threshold: float
    status: str
    visibility: str
    application_deadline: date | None = None
    created_at: datetime


class JobPostingListResponse(BaseModel):
    """Paginated recruiter jobs listing."""

    items: list[JobPostingResponse]
    total: int


class JobPostingPatchRequest(BaseModel):
    """Partial job update request."""

    status: str | None = None
    auto_shortlist_threshold: float | None = None
    radius_km: int | None = None
    accept_relocation: bool | None = None
    remote: bool | None = None
    hybrid: bool | None = None
    employment_type: str | None = None
    required_skills: list[JobSkillRequirement] | None = None
    preferred_skills: list[JobSkillRequirement] | None = None


class RankedSkillBreakdown(BaseModel):
    """Per-skill explanation row for role matching."""

    skill: str
    required: bool
    candidate_has: bool
    verification_tier: Literal["VERIFIED", "CONFIRMED", "SELF_DECLARED", "UNVERIFIED"]
    candidate_years: float
    required_years: float
    similarity: float
    score_contribution: float


class StrongestProject(BaseModel):
    """Most relevant candidate project for the role."""

    name: str
    relevance_score: float
    url: str | None = None
    languages: list[str] = Field(default_factory=list)
    stars: int = 0


class MatchScoreBreakdownPayload(BaseModel):
    """Composite score subcomponents."""

    skill_score: float
    experience_score: float
    project_score: float
    verification_score: float


class RankedCandidate(BaseModel):
    """Final candidate ranking payload returned to recruiters."""

    candidate_id: str
    job_id: str
    final_score: float
    grade: str
    location_status: Literal["local", "relocation", "remote"]
    distance_km: float | None = None
    pipeline_stage: str = "new"
    candidate_name: str = ""
    location_label: str = ""
    top_skills: list[str] = Field(default_factory=list)
    verification_score: float = 0.0
    skill_breakdown: list[RankedSkillBreakdown] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    strongest_projects: list[StrongestProject] = Field(default_factory=list)
    score_breakdown: MatchScoreBreakdownPayload
    recommendation: str


class RankedCandidateListResponse(BaseModel):
    """Recruiter candidate ranking list."""

    items: list[RankedCandidate]
    total: int


class CandidateStageUpdateRequest(BaseModel):
    """Recruiter pipeline stage change request."""

    stage: Literal["new", "reviewed", "shortlisted", "interview", "offer", "hired", "rejected"]
    note: str | None = None


class CandidateStageUpdateResponse(BaseModel):
    """Updated pipeline state for one candidate application."""

    application_id: str
    candidate_id: str
    job_id: str
    pipeline_stage: str
    recruiter_notes: str | None = None


class RunMatchingResponse(BaseModel):
    """Summary of a matching run."""

    matched_count: int
    shortlisted_count: int
    job_id: str


class RecruiterJobCandidateQuery(BaseModel):
    """Internal response model for recruiter candidate query filters."""

    items: list[RankedCandidate] = Field(default_factory=list)
    total: int = 0


class SocialRepoProjectInput(BaseModel):
    """Manual GitHub/project evidence captured from the employee side."""

    name: str = Field(min_length=1)
    description: str = ""
    url: str = ""
    languages: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    stars: int = 0
    has_tests: bool = False
    has_ci: bool = False


class LinkedInManualProfileInput(BaseModel):
    """Structured LinkedIn fallback payload."""

    current_role: str = ""
    company: str = ""
    location: str = ""
    experience_years: float = 0.0
    skills_listed: list[str] = Field(default_factory=list)


class LeetCodeManualProfileInput(BaseModel):
    """Structured LeetCode fallback payload."""

    easy: int = 0
    medium: int = 0
    hard: int = 0
    languages_used: list[str] = Field(default_factory=list)


class EmployeeProfileUpdateRequest(BaseModel):
    """Employee profile and social verification input payload."""

    location: str = ""
    open_to_relocation: bool = False
    claimed_skills: list[str] = Field(default_factory=list)
    github_username: str = ""
    linkedin_url: str = ""
    leetcode_username: str = ""
    github_projects: list[SocialRepoProjectInput] = Field(default_factory=list)
    linkedin_manual: LinkedInManualProfileInput = Field(default_factory=LinkedInManualProfileInput)
    leetcode_manual: LeetCodeManualProfileInput = Field(default_factory=LeetCodeManualProfileInput)


class EmployeeProfileResponse(BaseModel):
    """Employee dashboard payload."""

    employee_id: str
    name: str
    email: EmailStr
    location: str = ""
    coordinates: CoordinatePoint | None = None
    open_to_relocation: bool = False
    claimed_skills: list[str] = Field(default_factory=list)
    github_username: str = ""
    linkedin_url: str = ""
    leetcode_username: str = ""
    github_projects: list[SocialRepoProjectInput] = Field(default_factory=list)
    linkedin_manual: LinkedInManualProfileInput = Field(default_factory=LinkedInManualProfileInput)
    leetcode_manual: LeetCodeManualProfileInput = Field(default_factory=LeetCodeManualProfileInput)
    scrape_status: str = "pending"
    profile_completeness: float = 0.0
    verification_score: float = 0.0
    verified_skills: list[dict[str, Any]] = Field(default_factory=list)
    unverified_claims: list[str] = Field(default_factory=list)


class EmployeeJobMatchPreview(BaseModel):
    """Employee-facing job-card match preview."""

    score: float | None = None
    grade: str | None = None
    location_status: Literal["local", "relocation", "remote", "out_of_range", "unknown"] | None = None
    distance_km: float | None = None
    top_skills: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    recommendation: str = ""


class EmployeeJobBoardItem(BaseModel):
    """Public job listing with optional employee-specific match preview."""

    id: str
    title: str
    company: str
    location_label: str = ""
    employment_type: str
    required_skills: list[JobSkillRequirement] = Field(default_factory=list)
    preferred_skills: list[JobSkillRequirement] = Field(default_factory=list)
    remote: bool = False
    hybrid: bool = False
    match_preview: EmployeeJobMatchPreview | None = None


class EmployeeJobBoardResponse(BaseModel):
    """Employee-facing public jobs feed."""

    items: list[EmployeeJobBoardItem] = Field(default_factory=list)
    total: int = 0


class SocialSyncResponse(BaseModel):
    """Employee social-sync response payload."""

    scrape_status: str
    github: dict[str, Any] = Field(default_factory=dict)
    linkedin: dict[str, Any] = Field(default_factory=dict)
    leetcode: dict[str, Any] = Field(default_factory=dict)


class CareerSuggestionResponse(BaseModel):
    """Employee-facing career coach payload."""

    recommended_skills: list[dict[str, Any]] = Field(default_factory=list)
    top_jobs: list[dict[str, Any]] = Field(default_factory=list)
    score_trajectories: list[dict[str, Any]] = Field(default_factory=list)


class ResumeGenerateRequest(BaseModel):
    """Employee request to generate a resume artifact."""

    template: Literal["classic", "modern", "technical", "academic"] = "classic"
    format: Literal["pdf", "docx", "both"] = "both"


class ResumeArtifactResponse(BaseModel):
    """Generated resume metadata and download endpoints."""

    resume_id: str
    template_name: str
    pdf_url: str | None = None
    docx_url: str | None = None
    public_url: str | None = None
    created_at: datetime


class ResumeArtifactListResponse(BaseModel):
    """Collection of generated resumes owned by the employee."""

    items: list[ResumeArtifactResponse] = Field(default_factory=list)
    total: int = 0


class EmployeeApplyRequest(BaseModel):
    """Employee one-click apply payload."""

    cover_note: str = ""
    resume_id: str | None = None


class EmployeeApplicationItem(BaseModel):
    """Employee-facing application tracker row."""

    application_id: str
    job_id: str
    job_title: str
    company: str
    applied_at: datetime
    pipeline_stage: str
    match_score: float = 0.0
    grade: str = ""
    source: str = "direct_apply"
    cover_note: str = ""


class EmployeeApplicationListResponse(BaseModel):
    """Employee application tracker payload."""

    items: list[EmployeeApplicationItem] = Field(default_factory=list)
    total: int = 0


class IntakeFormField(BaseModel):
    """Recruiter-configurable intake field."""

    key: str
    label: str
    field_type: Literal["text", "textarea", "dropdown", "multi_select", "yes_no", "location", "file"] = "text"
    required: bool = False
    options: list[str] = Field(default_factory=list)


class IntakeFormCreateRequest(BaseModel):
    """Create or replace a recruiter intake form."""

    fields: list[IntakeFormField] = Field(default_factory=list)


class IntakeFormResponse(BaseModel):
    """Recruiter or public view of an intake form."""

    id: str
    job_id: str
    public_slug: str
    response_count: int
    fields: list[IntakeFormField] = Field(default_factory=list)


class RecruiterFormResponseItem(BaseModel):
    """Recruiter-visible form submission row."""

    form_response_id: str
    application_id: str | None = None
    candidate_name: str = ""
    email: str = ""
    location: str = ""
    submitted_at: datetime
    pipeline_stage: str = "new"
    match_score: float = 0.0
    response_preview: dict[str, Any] = Field(default_factory=dict)


class RecruiterFormResponseListResponse(BaseModel):
    """Recruiter-facing list of intake-form submissions."""

    items: list[RecruiterFormResponseItem] = Field(default_factory=list)
    total: int = 0


class PublicFormSubmissionRequest(BaseModel):
    """Public candidate submission payload for an intake form."""

    name: str = Field(min_length=1)
    email: EmailStr
    phone: str = ""
    location: str = ""
    open_to_relocation: bool = False
    github_url: str = ""
    linkedin_url: str = ""
    answers: dict[str, Any] = Field(default_factory=dict)


class PublicFormSubmissionResponse(BaseModel):
    """Public intake submission confirmation."""

    form_id: str
    application_id: str
    submitted: bool = True


class PoolCandidateResponse(BaseModel):
    """Recruiter-visible candidate row from the TalentOS pool."""

    employee_id: str
    name: str
    location: str = ""
    open_to_relocation: bool = False
    verification_score: float = 0.0
    profile_completeness: float = 0.0
    top_skills: list[str] = Field(default_factory=list)
    github_username: str = ""
    linkedin_url: str = ""


class PoolCandidateListResponse(BaseModel):
    """Recruiter pool search response."""

    items: list[PoolCandidateResponse] = Field(default_factory=list)
    total: int = 0


class PoolAccessRequestPayload(BaseModel):
    """Recruiter contact request payload."""

    job_id: str | None = None
    message: str = ""


class PoolAccessRequestResponse(BaseModel):
    """Recruiter contact request response."""

    id: str
    employee_id: str
    recruiter_id: str
    status: str
    message: str


class RecruiterAnalyticsResponse(BaseModel):
    """Recruiter analytics summary payload."""

    active_jobs: int = 0
    total_pipeline_candidates: int = 0
    shortlisted_candidates: int = 0
    hired_candidates: int = 0
    average_score: float = 0.0
    skill_distribution: list[dict[str, Any]] = Field(default_factory=list)


class JwtPrincipal(BaseModel):
    """Decoded JWT principal shared across route dependencies."""

    model_config = ConfigDict(extra="ignore")

    sub: str
    role: Literal["employee", "recruiter"]
    email: EmailStr
    exp: int
