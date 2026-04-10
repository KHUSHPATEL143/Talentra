"""Skill normalization agent implementation."""

from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import AgentMessage, AgentTrace, CandidateProfile, NormalizedSkill, SkillProfile
from app.services.taxonomy_service import TaxonomyService
from app.utils.proficiency import estimate_skill_proficiency
from app.utils.skill_inference import SkillInferenceEngine

logger = structlog.get_logger(__name__)


class NormalizationAgent:
    """Normalize raw resume skills to a canonical taxonomy."""

    def __init__(self, taxonomy_service: TaxonomyService, inference_engine: SkillInferenceEngine) -> None:
        """Store taxonomy and inference helpers."""

        self.taxonomy_service = taxonomy_service
        self.inference_engine = inference_engine

    async def run(
        self,
        job_id: str,
        candidate_profile: CandidateProfile,
        raw_text: str,
        session: AsyncSession,
    ) -> AgentMessage:
        """Normalize candidate skills using exact, fuzzy, embedding, and LLM fallbacks."""

        started_at = time.perf_counter()
        logger.info("agent.enter", job_id=job_id, agent_name="normalization_agent")
        normalized_skills: list[NormalizedSkill] = []
        emerging_skills: list[str] = []
        seen: set[str] = set()
        context_text = self._build_context(candidate_profile, raw_text)

        for raw_skill in candidate_profile.skills:
            normalized = await self._normalize_skill(raw_skill, context_text, session)
            if normalized.name not in seen:
                normalized_skills.append(normalized)
                seen.add(normalized.name)
            if normalized.emerging:
                emerging_skills.append(normalized.source_skill)

        canonical_set = {skill.name for skill in normalized_skills}
        inferred_names = self.inference_engine.apply(canonical_set)
        for inferred_name in inferred_names:
            if inferred_name in seen:
                continue
            entry = self.taxonomy_service.exact_match(inferred_name) or {
                "canonical_name": inferred_name,
                "aliases": [inferred_name],
                "category": "Technical",
                "subcategory": "Inferred",
            }
            trigger_weights = [skill.proficiency_weight for skill in normalized_skills if skill.category == entry["category"]]
            avg_weight = sum(trigger_weights) / len(trigger_weights) if trigger_weights else 0.5
            normalized_skills.append(
                NormalizedSkill(
                    name=entry["canonical_name"],
                    aliases=entry.get("aliases", []),
                    category=entry.get("category", "Technical"),
                    subcategory=entry.get("subcategory", "Inferred"),
                    proficiency=self._weight_to_level(avg_weight),
                    proficiency_weight=round(avg_weight, 2),
                    years_experience=0.0,
                    inferred=True,
                    emerging=False,
                    source_skill=inferred_name,
                    confidence=0.9,
                    normalization_tier="exact",
                )
            )
            seen.add(inferred_name)

        total_experience_years = round(
            sum(item.duration_months for item in candidate_profile.experience) / 12 if candidate_profile.experience else 0.0,
            2,
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        quality_score = round(len(normalized_skills) / max(len(candidate_profile.skills), 1), 3)
        skill_profile = SkillProfile(
            raw_skills=candidate_profile.skills,
            normalized_skills=normalized_skills,
            inferred_skills=sorted(inferred_names),
            emerging_skills=emerging_skills,
            total_experience_years=total_experience_years,
        )
        logger.info("agent.exit", job_id=job_id, agent_name="normalization_agent", latency_ms=latency_ms)
        return AgentMessage(
            job_id=job_id,
            stage="normalized",
            payload={"skill_profile": skill_profile.model_dump()},
            trace=AgentTrace(agent="normalization_agent", latency_ms=latency_ms, quality_score=quality_score),
            errors=[],
            partial=False,
        )

    async def _normalize_skill(self, raw_skill: str, context_text: str, session: AsyncSession) -> NormalizedSkill:
        """Normalize a single raw skill against the taxonomy tiers."""

        proficiency, weight, years = estimate_skill_proficiency(raw_skill, context_text)

        exact = self.taxonomy_service.exact_match(raw_skill)
        if exact:
            return self._build_skill(raw_skill, exact, proficiency, weight, years, 1.0, "exact")

        fuzzy, fuzzy_score = self.taxonomy_service.fuzzy_match(raw_skill)
        if fuzzy:
            return self._build_skill(raw_skill, fuzzy, proficiency, weight, years, fuzzy_score, "fuzzy")

        embedding, embedding_score = await self.taxonomy_service.embedding_match(raw_skill)
        if embedding:
            return self._build_skill(raw_skill, embedding, proficiency, weight, years, embedding_score, "embedding")

        llm_result = await self.taxonomy_service.llm_match(raw_skill)
        llm_entry = self.taxonomy_service.exact_match(llm_result.canonical_name)
        if llm_entry and llm_result.confidence >= 0.6:
            return self._build_skill(raw_skill, llm_entry, proficiency, weight, years, llm_result.confidence, "llm")

        await self.taxonomy_service.mark_pending_review(
            session=session,
            raw_skill=raw_skill,
            suggested_canonical=llm_result.canonical_name if llm_result.canonical_name else None,
            confidence=llm_result.confidence,
        )
        return NormalizedSkill(
            name=llm_result.canonical_name or raw_skill,
            aliases=[raw_skill],
            category="Emerging",
            subcategory="Pending Review",
            proficiency=proficiency,
            proficiency_weight=weight,
            years_experience=years,
            inferred=False,
            emerging=True,
            source_skill=raw_skill,
            confidence=llm_result.confidence,
            normalization_tier="emerging",
        )

    def _build_context(self, candidate_profile: CandidateProfile, raw_text: str) -> str:
        """Combine resume sections into a shared context string."""

        blocks: list[str] = [candidate_profile.summary, raw_text]
        for item in candidate_profile.experience:
            blocks.extend([item.role, item.company, " ".join(item.responsibilities), " ".join(item.technologies)])
        for item in candidate_profile.projects:
            blocks.extend([item.name, item.description, " ".join(item.technologies)])
        return "\n".join(part for part in blocks if part)

    def _build_skill(
        self,
        raw_skill: str,
        entry: dict[str, Any],
        proficiency: str,
        weight: float,
        years: float,
        confidence: float,
        tier: str,
    ) -> NormalizedSkill:
        """Construct a normalized skill payload."""

        return NormalizedSkill(
            name=entry["canonical_name"],
            aliases=entry.get("aliases", []),
            category=entry.get("category", "Technical"),
            subcategory=entry.get("subcategory", ""),
            proficiency=proficiency,  # type: ignore[arg-type]
            proficiency_weight=weight,
            years_experience=years,
            inferred=False,
            emerging=False,
            source_skill=raw_skill,
            confidence=round(confidence, 3),
            normalization_tier=tier,  # type: ignore[arg-type]
        )

    def _weight_to_level(self, weight: float) -> str:
        """Convert a proficiency weight into a discrete proficiency level."""

        if weight >= 1.0:
            return "expert"
        if weight >= 0.75:
            return "advanced"
        if weight >= 0.5:
            return "intermediate"
        return "beginner"
