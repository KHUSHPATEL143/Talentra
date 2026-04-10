"""Semantic matching agent implementation."""

from __future__ import annotations

import time

import structlog

from app.core.config import get_settings
from app.models.schemas import (
    AgentMessage,
    AgentTrace,
    JobRequirementExtraction,
    MatchResult,
    MatchWeights,
    MatchedSkill,
    MissingSkill,
    SkillProfile,
)
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)

UPSUGGESTIONS = {
    "Kubernetes": "Complete a container orchestration project and deploy it with Helm.",
    "Docker": "Containerize one production-style application and publish the workflow.",
    "TensorFlow": "Build and document an end-to-end deep learning notebook or mini product.",
    "PyTorch": "Train and evaluate a model using PyTorch Lightning or raw PyTorch.",
    "AWS": "Earn a cloud lab badge and deploy a small service on AWS.",
}


class MatchingAgent:
    """Match a normalized candidate skill profile against a job description."""

    def __init__(self, embedding_service: EmbeddingService, llm_service: LLMService) -> None:
        """Store dependencies needed for semantic matching."""

        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.settings = get_settings()

    async def run(
        self,
        job_id: str,
        skill_profile: SkillProfile,
        job_description: str,
        weights: MatchWeights | None = None,
        mode: str | None = None,
    ) -> AgentMessage:
        """Compute semantic fit between a candidate and a job description."""

        started_at = time.perf_counter()
        logger.info("agent.enter", job_id=job_id, agent_name="matching_agent")
        if not job_description.strip():
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            empty = MatchResult(
                score=0.0,
                grade="F",
                matched_skills=[],
                missing_skills=[],
                experience_match=0.0,
                recommendations=[],
                parsed_requirements=JobRequirementExtraction(),
            )
            return AgentMessage(
                job_id=job_id,
                stage="matched",
                payload={"match_result": empty.model_dump()},
                trace=AgentTrace(agent="matching_agent", latency_ms=latency_ms, quality_score=0.0),
                errors=[],
                partial=True,
            )

        parsed_requirements = await self.llm_service.parse_job_requirements(job_description)
        selected_weights = weights or MatchWeights()
        threshold = self._resolve_threshold(mode)
        match_result = await self._calculate_match(skill_profile, parsed_requirements, selected_weights, threshold)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        quality_score = round(match_result.score / 100.0, 3)
        logger.info("agent.exit", job_id=job_id, agent_name="matching_agent", latency_ms=latency_ms)
        return AgentMessage(
            job_id=job_id,
            stage="matched",
            payload={"match_result": match_result.model_dump()},
            trace=AgentTrace(agent="matching_agent", latency_ms=latency_ms, quality_score=quality_score),
            errors=[],
            partial=False,
        )

    def _resolve_threshold(self, mode: str | None) -> float:
        """Resolve similarity threshold from the requested match mode."""

        match_mode = mode or self.settings.default_match_mode
        return self.settings.match_precision_threshold if match_mode == "precision" else self.settings.match_recall_threshold

    async def _calculate_match(
        self,
        skill_profile: SkillProfile,
        requirements: JobRequirementExtraction,
        weights: MatchWeights,
        threshold: float,
    ) -> MatchResult:
        """Calculate the final match score and gap analysis."""

        candidate_names = [skill.name for skill in skill_profile.normalized_skills]
        candidate_embeddings = await self.embedding_service.embed_batch(candidate_names)
        candidate_embedding_map = dict(zip(candidate_names, candidate_embeddings, strict=False))

        candidate_vector = self.embedding_service.weighted_average(
            candidate_embeddings,
            [skill.proficiency_weight for skill in skill_profile.normalized_skills],
        )

        all_job_skills = requirements.required_skills + requirements.preferred_skills
        job_embeddings = await self.embedding_service.embed_batch(all_job_skills)
        job_embedding_map = dict(zip(all_job_skills, job_embeddings, strict=False))
        job_vector = self.embedding_service.weighted_average(job_embeddings, [1.0] * len(job_embeddings))
        experience_match = round(self.embedding_service.cosine_similarity(candidate_vector, job_vector), 3)

        matched_skills: list[MatchedSkill] = []
        missing_skills: list[MissingSkill] = []
        weighted_score = 0.0
        total_weight = 0.0

        for importance, job_skills, bucket_weight in (
            ("required", requirements.required_skills, weights.required),
            ("preferred", requirements.preferred_skills, weights.preferred),
        ):
            for job_skill in job_skills:
                total_weight += bucket_weight
                best_skill, best_score = self._best_candidate_match(
                    job_embedding_map.get(job_skill, []),
                    skill_profile,
                    candidate_embedding_map,
                )
                if best_skill and best_score >= threshold:
                    experience_multiplier = min(
                        (best_skill.years_experience or skill_profile.total_experience_years or 0.0)
                        / max(requirements.min_experience_years, 1.0),
                        1.5,
                    )
                    contribution = min(best_score * experience_multiplier, 1.0) * bucket_weight
                    weighted_score += contribution
                    matched_skills.append(
                        MatchedSkill(
                            skill=best_skill.name,
                            confidence=round(best_score, 3),
                            candidate_years=round(best_skill.years_experience, 2),
                        )
                    )
                else:
                    missing_skills.append(
                        MissingSkill(
                            skill=job_skill,
                            importance=importance,  # type: ignore[arg-type]
                            upskilling=UPSUGGESTIONS.get(
                                job_skill,
                                f"Build a focused project or certification path that demonstrates {job_skill}.",
                            ),
                        )
                    )

        score = round((weighted_score / total_weight) * 100 if total_weight else 0.0, 1)
        grade = self._score_to_grade(score)
        recommendations = await self.llm_service.generate_recommendations(
            candidate_summary=", ".join(candidate_names),
            matched_skills=[item.skill for item in matched_skills],
            missing_skills=[item.skill for item in missing_skills],
        )
        return MatchResult(
            score=score,
            grade=grade,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_match=experience_match,
            recommendations=recommendations,
            parsed_requirements=JobRequirementExtraction.model_validate(requirements.model_dump()),
        )

    def _best_candidate_match(
        self,
        job_embedding: list[float],
        skill_profile: SkillProfile,
        candidate_embedding_map: dict[str, list[float]],
    ) -> tuple[object | None, float]:
        """Return the best candidate skill match for one job skill embedding."""

        best_skill = None
        best_score = 0.0
        for candidate_skill in skill_profile.normalized_skills:
            candidate_embedding = candidate_embedding_map.get(candidate_skill.name, [])
            similarity = self.embedding_service.cosine_similarity(job_embedding, candidate_embedding)
            if similarity > best_score:
                best_score = similarity
                best_skill = candidate_skill
        return best_skill, best_score

    def _score_to_grade(self, score: float) -> str:
        """Map a numeric score to the user-facing grade band."""

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
