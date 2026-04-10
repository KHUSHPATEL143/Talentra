"""Pydantic request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class ErrorResponse(BaseModel):
    """Structured API error payload."""

    error: str
    message: str
    trace_id: str
    partial_result: dict[str, Any] | None = None


class Location(BaseModel):
    """Candidate location."""

    city: str = ""
    country: str = ""


class ExperienceItem(BaseModel):
    """Candidate work experience."""

    company: str = ""
    role: str = ""
    start: str = ""
    end: str = ""
    duration_months: int = 0
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    """Candidate education record."""

    institution: str = ""
    degree: str = ""
    field: str = ""
    year: int = 0
    gpa: float | None = None


class CertificationItem(BaseModel):
    """Professional certification."""

    name: str = ""
    issuer: str = ""
    year: int = 0


class ProjectItem(BaseModel):
    """Candidate project entry."""

    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class PublicationItem(BaseModel):
    """Candidate publication entry."""

    title: str = ""
    venue: str = ""
    year: int = 0


class CandidateProfile(BaseModel):
    """Structured candidate profile extracted from a resume."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    email: EmailStr | str = ""
    phone: str = ""
    location: Location = Field(default_factory=Location)
    linkedin: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    publications: list[PublicationItem] = Field(default_factory=list)


class AgentTrace(BaseModel):
    """Execution trace emitted by an agent."""

    agent: str
    latency_ms: int
    quality_score: float = 0.0
    error: str | None = None


class AgentMessage(BaseModel):
    """Shared inter-agent protocol message."""

    job_id: str
    stage: Literal["parsed", "normalized", "matched"]
    payload: dict[str, Any]
    trace: AgentTrace
    errors: list[str] = Field(default_factory=list)
    partial: bool = False


class NormalizedSkill(BaseModel):
    """Normalized canonical skill enriched with metadata."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    category: str
    subcategory: str
    proficiency: Literal["beginner", "intermediate", "advanced", "expert"]
    proficiency_weight: float
    years_experience: float = 0.0
    inferred: bool = False
    emerging: bool = False
    source_skill: str
    confidence: float
    normalization_tier: Literal["exact", "fuzzy", "embedding", "llm", "emerging"]


class SkillProfile(BaseModel):
    """Normalized skill profile for a candidate."""

    raw_skills: list[str] = Field(default_factory=list)
    normalized_skills: list[NormalizedSkill] = Field(default_factory=list)
    inferred_skills: list[str] = Field(default_factory=list)
    emerging_skills: list[str] = Field(default_factory=list)
    total_experience_years: float = 0.0
    embedding_vector: list[float] = Field(default_factory=list)


class ParseResponse(BaseModel):
    """Response payload for synchronous parsing."""

    candidate_id: str
    candidate_profile: CandidateProfile
    skill_profile: SkillProfile
    traces: list[AgentTrace]
    quality_score: float
    partial: bool = False


class CandidateResponse(CandidateProfile):
    """Candidate profile response with identifiers."""

    id: str
    quality_score: float
    source_format: str
    created_at: datetime


class CandidateSkillsResponse(BaseModel):
    """Skill profile response."""

    candidate_id: str
    skill_profile: SkillProfile


class MatchWeights(BaseModel):
    """Configurable weighting between required and preferred skills."""

    required: float = 0.7
    preferred: float = 0.3


class MatchRequest(BaseModel):
    """Request body for semantic candidate matching."""

    candidate_id: str
    job_description: str
    weights: MatchWeights = Field(default_factory=MatchWeights)
    mode: Literal["precision", "recall"] | None = None


class JobRequirementExtraction(BaseModel):
    """Structured job requirement extraction."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    role_level: str = ""


class MatchedSkill(BaseModel):
    """Skill match detail."""

    skill: str
    confidence: float
    candidate_years: float


class MissingSkill(BaseModel):
    """Gap analysis item."""

    skill: str
    importance: Literal["required", "preferred"]
    upskilling: str


class MatchResult(BaseModel):
    """Candidate-job match result."""

    score: float
    grade: str
    matched_skills: list[MatchedSkill] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    experience_match: float
    recommendations: list[str] = Field(default_factory=list)
    parsed_requirements: JobRequirementExtraction


class MatchResponse(MatchResult):
    """Stored match result response."""

    match_id: str
    candidate_id: str
    job_id: str


class TaxonomyEntry(BaseModel):
    """Skill taxonomy item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    category: str
    subcategory: str
    parent_id: int | None = None
    aliases: list[str]


class TaxonomyPage(BaseModel):
    """Paginated taxonomy response."""

    page: int
    page_size: int
    total: int
    items: list[TaxonomyEntry]


class TaxonomySearchResult(BaseModel):
    """Similarity search result for a taxonomy query."""

    canonical_name: str
    category: str
    subcategory: str
    similarity: float


class JobStatusResponse(BaseModel):
    """Batch job status response."""

    job_id: str
    status: Literal["queued", "pending", "processing", "done", "failed"]
    completed_count: int
    total_count: int
    results: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class WebhookRegistrationRequest(BaseModel):
    """Webhook registration body."""

    url: HttpUrl
    events: list[Literal["parse.complete", "match.complete", "batch.complete"]]


class WebhookRegistrationResponse(BaseModel):
    """Webhook registration response."""

    id: str
    url: HttpUrl
    events: list[str]


class JobRequirementsPromptResponse(BaseModel):
    """Internal response model for job extraction prompt."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    role_level: str = ""


class SkillFallbackResponse(BaseModel):
    """Internal response model for LLM skill fallback."""

    canonical_name: str
    confidence: float
    reasoning: str = ""


class RecommendationResponse(BaseModel):
    """Internal response model for recommendation generation."""

    recommendations: list[str] = Field(default_factory=list)
