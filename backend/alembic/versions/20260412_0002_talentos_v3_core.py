"""TalentOS v3 core recruiter and auth schema.

Revision ID: 20260412_0002
Revises: 20260412_0001
Create Date: 2026-04-12 16:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0002"
down_revision = "20260412_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the TalentOS v3 schema additions."""

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "employees",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("location_city", sa.String(length=120), nullable=True),
        sa.Column("location_country", sa.String(length=120), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("open_to_relocation", sa.Boolean(), nullable=False),
        sa.Column("desired_salary_min", sa.Integer(), nullable=True),
        sa.Column("desired_salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("profile_completeness", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "recruiters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_logo_url", sa.String(length=512), nullable=True),
        sa.Column("subscription_tier", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "social_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("github_username", sa.String(length=100), nullable=True),
        sa.Column("linkedin_url", sa.String(length=512), nullable=True),
        sa.Column("leetcode_username", sa.String(length=100), nullable=True),
        sa.Column("github_data", sa.JSON(), nullable=False),
        sa.Column("linkedin_data", sa.JSON(), nullable=False),
        sa.Column("leetcode_data", sa.JSON(), nullable=False),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scrape_status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id"),
    )

    op.create_table(
        "verified_skill_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("unverified_claims", sa.JSON(), nullable=False),
        sa.Column("verification_score", sa.Float(), nullable=False),
        sa.Column("profile_completeness", sa.Float(), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id"),
    )

    op.create_table(
        "generated_resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("template_name", sa.String(length=50), nullable=False),
        sa.Column("pdf_path", sa.String(length=255), nullable=True),
        sa.Column("docx_path", sa.String(length=255), nullable=True),
        sa.Column("public_url", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_url"),
    )

    op.create_table(
        "job_postings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recruiter_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("structured_requirements", sa.JSON(), nullable=False),
        sa.Column("location_city", sa.String(length=120), nullable=True),
        sa.Column("location_state", sa.String(length=120), nullable=True),
        sa.Column("location_country", sa.String(length=120), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("radius_km", sa.Integer(), nullable=False),
        sa.Column("accept_relocation", sa.Boolean(), nullable=False),
        sa.Column("remote", sa.Boolean(), nullable=False),
        sa.Column("hybrid", sa.Boolean(), nullable=False),
        sa.Column("employment_type", sa.String(length=30), nullable=False),
        sa.Column("experience_min", sa.Integer(), nullable=False),
        sa.Column("experience_max", sa.Integer(), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("preferred_skills", sa.JSON(), nullable=False),
        sa.Column("auto_shortlist_threshold", sa.Float(), nullable=False),
        sa.Column("min_coverage_threshold", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("job_embedding_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "candidate_applications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=True),
        sa.Column("candidate_id", sa.String(length=36), nullable=True),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("candidate_data", sa.JSON(), nullable=False),
        sa.Column("match_result", sa.JSON(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("pipeline_stage", sa.String(length=30), nullable=False),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "intake_forms",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recruiter_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("form_schema", sa.JSON(), nullable=False),
        sa.Column("public_slug", sa.String(length=50), nullable=False),
        sa.Column("response_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"]),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_slug"),
    )

    op.create_table(
        "form_responses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("responses", sa.JSON(), nullable=False),
        sa.Column("resume_path", sa.String(length=255), nullable=True),
        sa.Column("application_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"]),
        sa.ForeignKeyConstraint(["form_id"], ["intake_forms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pool_access_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("recruiter_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"]),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "career_suggestions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("recommended_skills", sa.JSON(), nullable=False),
        sa.Column("top_jobs", sa.JSON(), nullable=False),
        sa.Column("score_trajectories", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the TalentOS v3 schema additions."""

    op.drop_table("career_suggestions")
    op.drop_table("pool_access_requests")
    op.drop_table("form_responses")
    op.drop_table("intake_forms")
    op.drop_table("candidate_applications")
    op.drop_table("job_postings")
    op.drop_table("generated_resumes")
    op.drop_table("verified_skill_profiles")
    op.drop_table("social_profiles")
    op.drop_table("recruiters")
    op.drop_table("employees")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
