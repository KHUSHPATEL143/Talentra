"""Location-aware recruiter role matcher for TalentOS v3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Candidate, utcnow
from app.models.db_v3 import CandidateApplication, JobPosting, VerifiedSkillProfile
from app.models.schemas_v3 import (
    MatchScoreBreakdownPayload,
    RankedCandidate,
    RankedSkillBreakdown,
    StrongestProject,
)
from app.services.embedding_service import EmbeddingService
from app.services.geocoding_service import GeocodingService


@dataclass(slots=True)
class CandidateContext:
    """Normalized candidate context used during matching."""

    candidate_id: str
    name: str
    location_label: str
    coordinates: tuple[float, float] | None
    open_to_relocation: bool
    verified_skills: list[dict[str, Any]]
    verification_score: float
    total_years: float
    projects: list[dict[str, Any]]


class RoleMatcher:
    """Rank candidates for a specific job with location-aware filtering."""

    VERIFICATION_WEIGHTS = {
        "VERIFIED": 1.0,
        "CONFIRMED": 0.85,
        "SELF_DECLARED": 0.65,
        "UNVERIFIED": 0.4,
    }

    def __init__(self, embedding_service: EmbeddingService, geocoding_service: GeocodingService) -> None:
        """Store services used by the role matcher."""

        self.embedding_service = embedding_service
        self.geocoding_service = geocoding_service

    async def run(self, session: AsyncSession, job: JobPosting, stage: str | None = None) -> list[RankedCandidate]:
        """Rank the eligible candidate pool for the supplied job."""

        candidates = await self._load_candidate_pool(session)
        rankings: list[RankedCandidate] = []
        for candidate in candidates:
            location_ok, location_status, distance_km = self.location_eligible(candidate, job)
            if not location_ok:
                continue
            ranked = await self._rank_candidate(job, candidate, location_status, distance_km)
            if ranked is None:
                continue
            if stage and ranked.pipeline_stage != stage:
                continue
            rankings.append(ranked)

        rankings.sort(key=lambda item: (item.location_status != "local", -(item.final_score or 0.0)))
        return rankings

    def build_candidate_context(
        self,
        *,
        candidate_id: str,
        name: str,
        location_label: str,
        coordinates: tuple[float, float] | None,
        open_to_relocation: bool,
        verified_skills: list[dict[str, Any]],
        total_years: float,
        projects: list[dict[str, Any]],
    ) -> CandidateContext:
        """Create a candidate context and derive its verification score."""

        return CandidateContext(
            candidate_id=candidate_id,
            name=name,
            location_label=location_label,
            coordinates=coordinates,
            open_to_relocation=open_to_relocation,
            verified_skills=verified_skills,
            verification_score=self._verification_score(verified_skills),
            total_years=total_years,
            projects=projects,
        )

    async def score_candidate_for_job(self, job: JobPosting, candidate: CandidateContext) -> RankedCandidate | None:
        """Score a single supplied candidate context for a job."""

        location_ok, location_status, distance_km = self.location_eligible(candidate, job)
        if not location_ok:
            return None
        return await self._rank_candidate(job, candidate, location_status, distance_km)

    def location_eligible(self, candidate: CandidateContext, job: JobPosting) -> tuple[bool, str, float | None]:
        """Apply the hard location filter before any heavy scoring."""

        if job.remote:
            return True, "remote", 0.0
        if candidate.coordinates is None or job.lat is None or job.lng is None:
            return False, "unknown", None
        distance_km = self.geocoding_service.haversine_km(candidate.coordinates[0], candidate.coordinates[1], job.lat, job.lng)
        if distance_km <= job.radius_km:
            return True, "local", distance_km
        if job.accept_relocation and candidate.open_to_relocation:
            return True, "relocation", distance_km
        return False, "out_of_range", distance_km

    async def _load_candidate_pool(self, session: AsyncSession) -> list[CandidateContext]:
        """Load the bridge pool from parsed v2 candidates plus any verified profiles."""

        candidates = list((await session.execute(select(Candidate))).scalars().all())
        verified_profiles = {
            profile.employee_id: profile
            for profile in list((await session.execute(select(VerifiedSkillProfile))).scalars().all())
        }
        contexts: list[CandidateContext] = []
        for candidate in candidates:
            candidate_profile = candidate.profile_json.get("candidate_profile", {})
            skill_profile = candidate.profile_json.get("skill_profile", {})
            location = candidate_profile.get("location", {})
            location_parts = [location.get("city", ""), location.get("country", "")]
            location_label = ", ".join(part for part in location_parts if part)
            coordinates = await self.geocoding_service.geocode(location_label) if location_label else None
            normalized_skills = skill_profile.get("normalized_skills", [])
            verified_skills = [
                {
                    "canonical_name": item.get("name", ""),
                    "verification_tier": "SELF_DECLARED",
                    "years": float(item.get("years_experience", 0.0)),
                    "proficiency": item.get("proficiency", "intermediate"),
                }
                for item in normalized_skills
                if item.get("name")
            ]
            total_years = float(skill_profile.get("total_experience_years", 0.0))
            contexts.append(
                self.build_candidate_context(
                    candidate_id=candidate.id,
                    name=candidate.name,
                    location_label=location_label,
                    coordinates=coordinates,
                    open_to_relocation=False,
                    verified_skills=verified_skills,
                    total_years=total_years,
                    projects=candidate_profile.get("projects", []),
                )
            )
        return contexts

    async def _rank_candidate(
        self,
        job: JobPosting,
        candidate: CandidateContext,
        location_status: str,
        distance_km: float | None,
    ) -> RankedCandidate | None:
        """Compute a recruiter-facing match result for one candidate."""

        required_skills = job.required_skills or []
        if required_skills:
            matched_required = sum(1 for requirement in required_skills if self._find_skill(candidate.verified_skills, requirement["skill"]))
            if (matched_required / max(len(required_skills), 1)) < float(job.min_coverage_threshold):
                return None

        skill_breakdown: list[RankedSkillBreakdown] = []
        required_score = await self._score_skill_group(candidate, required_skills, True, skill_breakdown)
        preferred_score = await self._score_skill_group(candidate, job.preferred_skills or [], False, skill_breakdown)
        skill_score = (required_score * 0.7) + (preferred_score * 0.3)
        experience_score = min(candidate.total_years / max(job.experience_min, 1), 1.5) if job.experience_min else 1.0
        project_score, strongest_projects = await self._project_relevance(job.description, candidate.projects)
        verification_score = candidate.verification_score
        final_score = min(
            100.0,
            max(
                0.0,
                (
                    skill_score * 0.40
                    + experience_score * 0.25
                    + project_score * 0.20
                    + verification_score * 0.15
                )
                * 100,
            ),
        )
        missing_required = [item["skill"] for item in required_skills if not self._find_skill(candidate.verified_skills, item["skill"])]
        grade = self._grade_for_score(final_score)
        recommendation = (
            f"{'Strong' if final_score >= 75 else 'Developing'} match. "
            f"{candidate.name or 'Candidate'} is {location_status} to the role"
            f"{f' ({distance_km:.1f} km)' if distance_km is not None else ''} and is strongest in "
            f"{', '.join(skill['canonical_name'] for skill in candidate.verified_skills[:3]) or 'core resume skills'}."
        )
        return RankedCandidate(
            candidate_id=candidate.candidate_id,
            job_id=job.id,
            final_score=round(final_score, 2),
            grade=grade,
            location_status=location_status,  # type: ignore[arg-type]
            distance_km=round(distance_km, 2) if distance_km is not None else None,
            candidate_name=candidate.name,
            location_label=candidate.location_label,
            top_skills=[skill["canonical_name"] for skill in candidate.verified_skills[:3]],
            verification_score=round(verification_score * 100, 2),
            skill_breakdown=skill_breakdown,
            missing_required=missing_required,
            strongest_projects=strongest_projects,
            score_breakdown=MatchScoreBreakdownPayload(
                skill_score=round(skill_score * 100, 2),
                experience_score=round(experience_score * 100, 2),
                project_score=round(project_score * 100, 2),
                verification_score=round(verification_score * 100, 2),
            ),
            recommendation=recommendation,
        )

    async def _score_skill_group(
        self,
        candidate: CandidateContext,
        job_skills: list[dict[str, Any]],
        required: bool,
        skill_breakdown: list[RankedSkillBreakdown],
    ) -> float:
        """Score one skill group against the candidate profile."""

        if not job_skills:
            return 0.0

        candidate_embeddings = {
            skill["canonical_name"]: vector
            for skill, vector in zip(
                candidate.verified_skills,
                await self.embedding_service.embed_batch([skill["canonical_name"] for skill in candidate.verified_skills]),
                strict=False,
            )
        }
        required_embeddings = {
            skill["skill"]: vector
            for skill, vector in zip(
                job_skills,
                await self.embedding_service.embed_batch([skill["skill"] for skill in job_skills]),
                strict=False,
            )
        }

        contributions: list[float] = []
        for requirement in job_skills:
            best_score = 0.0
            best_match = None
            required_vector = required_embeddings.get(requirement["skill"], [])
            for candidate_skill in candidate.verified_skills:
                similarity = self.embedding_service.cosine_similarity(
                    candidate_embeddings.get(candidate_skill["canonical_name"], []),
                    required_vector,
                )
                adjusted = similarity * self.VERIFICATION_WEIGHTS.get(candidate_skill["verification_tier"], 0.4)
                if adjusted > best_score:
                    best_score = adjusted
                    best_match = candidate_skill

            candidate_years = float(best_match["years"]) if best_match else 0.0
            exp_multiplier = min(candidate_years / max(float(requirement.get("min_years", 0.0)) or 1.0, 1.0), 1.5)
            contribution = best_score * float(requirement.get("weight", 1.0)) * exp_multiplier
            contributions.append(contribution)
            skill_breakdown.append(
                RankedSkillBreakdown(
                    skill=requirement["skill"],
                    required=required,
                    candidate_has=best_match is not None,
                    verification_tier=(best_match or {}).get("verification_tier", "UNVERIFIED"),
                    candidate_years=candidate_years,
                    required_years=float(requirement.get("min_years", 0.0)),
                    similarity=round(best_score, 4),
                    score_contribution=round(contribution * 100, 2),
                )
            )
        return sum(contributions) / max(len(contributions), 1)

    async def _project_relevance(self, job_description: str, projects: list[dict[str, Any]]) -> tuple[float, list[StrongestProject]]:
        """Score the candidate's strongest projects against the job description."""

        if not projects:
            return 0.0, []
        job_vector = await self.embedding_service.embed_text(job_description)
        project_payloads = [f"{project.get('name', '')} {project.get('description', '')}" for project in projects]
        project_vectors = await self.embedding_service.embed_batch(project_payloads)
        ranked: list[tuple[float, dict[str, Any]]] = []
        for project, vector in zip(projects, project_vectors, strict=False):
            ranked.append((self.embedding_service.cosine_similarity(vector, job_vector), project))
        ranked.sort(key=lambda item: item[0], reverse=True)
        top_projects = [
            StrongestProject(
                name=project.get("name", "Untitled Project"),
                relevance_score=round(score, 4),
                languages=project.get("technologies", []),
                stars=0,
            )
            for score, project in ranked[:3]
        ]
        top_scores = [score for score, _ in ranked[:3]]
        return (sum(top_scores) / len(top_scores) if top_scores else 0.0), top_projects

    def _verification_score(self, verified_skills: list[dict[str, Any]]) -> float:
        """Return the average verification weight across a candidate skill set."""

        if not verified_skills:
            return 0.0
        weights = [self.VERIFICATION_WEIGHTS.get(skill.get("verification_tier", "UNVERIFIED"), 0.4) for skill in verified_skills]
        return sum(weights) / len(weights)

    def _find_skill(self, skills: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
        """Return the candidate skill matching the required canonical name."""

        target_normalized = target.strip().lower()
        for skill in skills:
            if skill.get("canonical_name", "").strip().lower() == target_normalized:
                return skill
        return None

    def _grade_for_score(self, score: float) -> str:
        """Map a numeric recruiter score to the standard grade band."""

        if score >= 95:
            return "A+"
        if score >= 88:
            return "A"
        if score >= 80:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C+"
        if score >= 50:
            return "C"
        return "F"

    async def persist_rankings(self, session: AsyncSession, job: JobPosting, rankings: list[RankedCandidate]) -> tuple[int, int]:
        """Store ranking outputs in candidate_applications for recruiter pipeline use."""

        existing_rows = {
            (row.candidate_id or "", row.job_id): row
            for row in list(
                (
                    await session.execute(
                        select(CandidateApplication).where(CandidateApplication.job_id == job.id)
                    )
                ).scalars().all()
            )
        }
        shortlisted_count = 0
        for ranking in rankings:
            row = existing_rows.get((ranking.candidate_id, job.id))
            pipeline_stage = "shortlisted" if ranking.final_score >= job.auto_shortlist_threshold else (row.pipeline_stage if row else "new")
            if pipeline_stage == "shortlisted":
                shortlisted_count += 1
            if row is None:
                session.add(
                    CandidateApplication(
                        candidate_id=ranking.candidate_id,
                        employee_id=None,
                        job_id=job.id,
                        source="pool",
                        candidate_data={"candidate_id": ranking.candidate_id, "candidate_name": ranking.candidate_name},
                        match_result=ranking.model_dump(),
                        final_score=ranking.final_score,
                        pipeline_stage=pipeline_stage,
                    )
                )
            else:
                row.match_result = ranking.model_dump()
                row.final_score = ranking.final_score
                row.pipeline_stage = pipeline_stage
                row.updated_at = utcnow()
        await session.commit()
        return len(rankings), shortlisted_count
