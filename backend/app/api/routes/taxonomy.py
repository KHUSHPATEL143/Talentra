"""Skill taxonomy routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db import PendingTaxonomyReview, SkillTaxonomy
from app.models.schemas import TaxonomyPage, TaxonomySearchResult

router = APIRouter(tags=["Taxonomy"])


@router.get(
    "/skills/taxonomy/search",
    summary="Search taxonomy",
    description="Search the canonical skill taxonomy using semantic similarity.",
    response_model=list[TaxonomySearchResult],
)
async def search_taxonomy(
    request: Request,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
) -> list[TaxonomySearchResult]:
    """Run semantic taxonomy search against ChromaDB."""

    return await request.app.state.taxonomy_service.search(q, limit)


@router.get(
    "/skills/taxonomy",
    summary="List taxonomy skills",
    description="Return a paginated slice of the canonical skill taxonomy.",
    response_model=TaxonomyPage,
)
async def get_taxonomy(
    request: Request,
    category: str | None = Query(default=None),
    parent_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=250),
    session: AsyncSession = Depends(get_session),
) -> TaxonomyPage:
    """Return paginated taxonomy entries with optional filtering."""

    items, total = await request.app.state.taxonomy_service.list_entries(session, category, parent_id, page, page_size)
    return TaxonomyPage(page=page, page_size=page_size, total=total, items=items)


@router.get(
    "/skills/taxonomy/stats",
    summary="Taxonomy stats",
    description="Return lightweight taxonomy counts for the frontend dashboard.",
)
async def taxonomy_stats(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    """Return taxonomy summary statistics."""

    total_skills = int(await session.scalar(select(func.count()).select_from(SkillTaxonomy)) or 0)
    pending_review = int(await session.scalar(select(func.count()).select_from(PendingTaxonomyReview)) or 0)
    distinct_categories = int(await session.scalar(select(func.count(func.distinct(SkillTaxonomy.category)))) or 0)
    return {
        "total_skills": total_skills,
        "pending_review_count": pending_review,
        "category_count": distinct_categories,
    }
