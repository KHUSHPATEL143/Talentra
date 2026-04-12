"""Career coach agent for employee-facing recommendations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_v3 import CareerSuggestion, Employee, JobPosting, SocialProfile, VerifiedSkillProfile


class CareerCoachAgent:
    """Generate skill-gap and next-step recommendations for employees."""

    def __init__(self, role_matcher) -> None:
        """Store the role matcher dependency used for score simulation."""

        self.role_matcher = role_matcher

    async def run(
        self,
        *,
        session: AsyncSession,
        employee: Employee,
        social: SocialProfile,
        verified: VerifiedSkillProfile,
        candidate_context,
    ) -> CareerSuggestion:
        """Create and persist a career suggestion payload."""

        jobs = list(
            (
                await session.execute(
                    select(JobPosting).where(JobPosting.status == "active", JobPosting.visibility == "public").order_by(JobPosting.created_at.desc())
                )
            ).scalars().all()
        )

        ranked_jobs: list[dict[str, Any]] = []
        missing_counter: Counter[str] = Counter()
        trajectories: list[dict[str, Any]] = []

        for job in jobs:
            ranking = await self.role_matcher.score_candidate_for_job(job, candidate_context)
            if ranking is None:
                continue
            ranked_jobs.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "score": ranking.final_score,
                    "grade": ranking.grade,
                    "missing_required": ranking.missing_required,
                }
            )
            for skill in ranking.missing_required:
                missing_counter[skill] += 1

        recommended_skills = [
            {
                "skill": skill,
                "job_count": count,
                "estimated_months": 2 if count >= 3 else 1,
                "reason": f"Shows up as a missing required skill in {count} matching jobs.",
            }
            for skill, count in missing_counter.most_common(5)
        ]

        for item in ranked_jobs[:5]:
            if not item["missing_required"]:
                continue
            next_skill = item["missing_required"][0]
            trajectories.append(
                {
                    "job_id": item["job_id"],
                    "job_title": item["title"],
                    "current_score": item["score"],
                    "recommended_skill": next_skill,
                    "projected_score": min(100.0, round(item["score"] + 12.0, 2)),
                }
            )

        top_jobs = sorted(ranked_jobs, key=lambda item: item["score"], reverse=True)[:8]

        suggestion = await session.scalar(select(CareerSuggestion).where(CareerSuggestion.employee_id == employee.id))
        if suggestion is None:
            suggestion = CareerSuggestion(employee_id=employee.id)
            session.add(suggestion)

        suggestion.recommended_skills = recommended_skills
        suggestion.top_jobs = top_jobs
        suggestion.score_trajectories = trajectories
        await session.commit()
        await session.refresh(suggestion)
        return suggestion
