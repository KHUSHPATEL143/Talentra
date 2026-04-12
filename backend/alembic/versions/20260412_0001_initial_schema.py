"""Initial GARUDA schema.

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 06:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial application schema."""

    op.create_table(
        "candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("source_format", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parsed_requirements_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "execution_traces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pending_taxonomy_review",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("raw_skill", sa.String(length=255), nullable=False),
        sa.Column("suggested_canonical", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "skill_taxonomy",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("subcategory", sa.String(length=100), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["skill_taxonomy.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
    )
    op.create_index("ix_skill_taxonomy_canonical_name", "skill_taxonomy", ["canonical_name"], unique=True)
    op.create_index("ix_skill_taxonomy_category", "skill_taxonomy", ["category"], unique=False)
    op.create_index("ix_skill_taxonomy_subcategory", "skill_taxonomy", ["subcategory"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("rate_limit_per_min", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("owner_key_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_key_id"], ["api_keys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("match_result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the initial application schema."""

    op.drop_table("matches")
    op.drop_table("webhooks")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index("ix_skill_taxonomy_subcategory", table_name="skill_taxonomy")
    op.drop_index("ix_skill_taxonomy_category", table_name="skill_taxonomy")
    op.drop_index("ix_skill_taxonomy_canonical_name", table_name="skill_taxonomy")
    op.drop_table("skill_taxonomy")
    op.drop_table("pending_taxonomy_review")
    op.drop_table("execution_traces")
    op.drop_table("jobs")
    op.drop_table("candidates")
