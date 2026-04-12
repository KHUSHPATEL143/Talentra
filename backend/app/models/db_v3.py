"""Additional SQLAlchemy ORM models for TalentOS v3."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db import Base, utcnow


class User(Base):
    """Application user with a role-specific profile."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    employee: Mapped["Employee | None"] = relationship(back_populates="user", uselist=False)
    recruiter: Mapped["Recruiter | None"] = relationship(back_populates="user", uselist=False)


class Employee(Base):
    """Employee marketplace profile."""

    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    location_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_to_relocation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    desired_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    profile_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="employee")


class Recruiter(Base):
    """Recruiter workspace profile."""

    __tablename__ = "recruiters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="basic")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="recruiter")
    jobs: Mapped[list["JobPosting"]] = relationship(back_populates="recruiter")


class SocialProfile(Base):
    """Structured social profile payloads collected for an employee."""

    __tablename__ = "social_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False, unique=True)
    github_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    leetcode_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    linkedin_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    leetcode_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scrape_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")


class VerifiedSkillProfile(Base):
    """Verified skill evidence profile for an employee."""

    __tablename__ = "verified_skill_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False, unique=True)
    skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    unverified_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    verification_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    profile_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GeneratedResume(Base):
    """Generated resume artifacts for an employee."""

    __tablename__ = "generated_resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    template_name: Mapped[str] = mapped_column(String(50), nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    docx_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_url: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class JobPosting(Base):
    """Recruiter-created job posting used by the v3 marketplace."""

    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id: Mapped[str] = mapped_column(ForeignKey("recruiters.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    structured_requirements: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    location_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_km: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    accept_relocation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hybrid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="full_time")
    experience_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    required_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    preferred_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    auto_shortlist_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=70.0)
    min_coverage_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    job_embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    recruiter: Mapped[Recruiter] = relationship(back_populates="jobs")
    applications: Mapped[list["CandidateApplication"]] = relationship(back_populates="job")


class CandidateApplication(Base):
    """Candidate-to-job application or recruiter-side pool entry."""

    __tablename__ = "candidate_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    candidate_id: Mapped[str | None] = mapped_column(ForeignKey("candidates.id"), nullable=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="pool")
    candidate_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    match_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pipeline_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="new")
    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    job: Mapped[JobPosting] = relationship(back_populates="applications")


class IntakeForm(Base):
    """Recruiter-owned public intake form."""

    __tablename__ = "intake_forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id: Mapped[str] = mapped_column(ForeignKey("recruiters.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id"), nullable=False)
    form_schema: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    public_slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    response_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class FormResponse(Base):
    """Public form submission stored before recruiter review."""

    __tablename__ = "form_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id: Mapped[str] = mapped_column(ForeignKey("intake_forms.id"), nullable=False)
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    resume_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("candidate_applications.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PoolAccessRequest(Base):
    """Recruiter request to contact a candidate from the shared pool."""

    __tablename__ = "pool_access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id: Mapped[str] = mapped_column(ForeignKey("recruiters.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_postings.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CareerSuggestion(Base):
    """Stored career-coach output for an employee."""

    __tablename__ = "career_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    recommended_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    top_jobs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    score_trajectories: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
