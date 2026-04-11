"""Structured-output LLM wrappers for candidate and job intelligence."""

from __future__ import annotations

import asyncio
import json
from typing import Any, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

try:
    from google import genai
except ImportError:  # pragma: no cover - exercised in local environments without Gemini SDK
    genai = None

from app.core.config import get_settings
from app.models.schemas import (
    CandidateProfile,
    JobRequirementsPromptResponse,
    RecommendationResponse,
    SkillFallbackResponse,
)

SchemaModel = TypeVar("SchemaModel", bound=BaseModel)


class LLMService:
    """Structured-output LLM wrapper supporting OpenAI and Gemini."""

    def __init__(self) -> None:
        """Initialize configured LLM clients."""

        settings = get_settings()
        self.settings = settings
        self.provider = self._resolve_provider()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key and genai else None

    def _resolve_provider(self) -> str:
        """Resolve the active LLM provider from config and available keys."""

        configured = (self.settings.llm_provider or "").strip().lower()
        if configured in {"openai", "gemini"}:
            return configured
        if self.settings.gemini_api_key:
            return "gemini"
        return "openai"

    async def structured_completion(
        self,
        schema_name: str,
        schema_model: type[SchemaModel],
        system_prompt: str,
        user_prompt: str,
    ) -> SchemaModel:
        """Request a structured JSON response and validate it with Pydantic."""

        schema = schema_model.model_json_schema()
        payload = await self._chat_json(schema_name=schema_name, schema=schema, system_prompt=system_prompt, user_prompt=user_prompt)
        return schema_model.model_validate(payload)

    async def _chat_json(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        retries: int = 3,
    ) -> dict[str, Any]:
        """Call the configured LLM API with exponential backoff."""

        for attempt in range(retries):
            try:
                if self.provider == "gemini":
                    return await self._gemini_chat_json(schema, system_prompt, user_prompt)
                return await self._openai_chat_json(schema_name, schema, system_prompt, user_prompt)
            except Exception:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        return {}

    async def _openai_chat_json(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call OpenAI structured outputs."""

        if not self.openai_client or not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }
        response = await self.openai_client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=0,
            response_format=response_format,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    async def _gemini_chat_json(
        self,
        schema: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Gemini structured outputs using JSON schema."""

        if not self.gemini_client or not self.settings.gemini_api_key:
            if not genai:
                raise ValueError("The Gemini SDK is not installed. Add google-genai to use LLM_PROVIDER=gemini.")
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")

        def _generate() -> str:
            response = self.gemini_client.models.generate_content(
                model=self.settings.gemini_model,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                    "response_json_schema": schema,
                },
            )
            return response.text or "{}"

        content = await asyncio.to_thread(_generate)
        return json.loads(content)

    async def extract_candidate_profile(self, resume_text: str) -> CandidateProfile:
        """Extract a structured candidate profile from raw resume text."""

        system_prompt = (
            "You extract resume data into strict JSON. Handle inconsistent layouts, "
            "multi-column or creative CV designs, implicit date ranges, and skills mentioned "
            "inside work experience or project descriptions. Preserve only factual information. "
            "Return empty strings or empty arrays when a field is absent."
        )
        user_prompt = (
            "Extract the following fields from the resume text: name, email, phone, location, linkedin, "
            "summary, skills, experience, education, certifications, projects, publications.\n\n"
            f"RESUME TEXT:\n{resume_text}"
        )
        return await self.structured_completion("candidate_profile", CandidateProfile, system_prompt, user_prompt)

    async def extract_candidate_profile_with_hints(
        self,
        resume_text: str,
        heuristic_profile: CandidateProfile,
    ) -> CandidateProfile:
        """Extract a candidate profile while preserving deterministic heuristic fields."""

        heuristic_dump = heuristic_profile.model_dump()
        system_prompt = (
            "You extract resume data into strict JSON. Handle inconsistent layouts, multi-column or creative CV designs, "
            "implicit date ranges, and skills mentioned inside work experience or project descriptions. "
            "You are also given deterministic fields extracted locally via regex/layout parsing. "
            "Preserve those heuristic values unless the resume clearly contradicts them."
        )
        user_prompt = (
            "Heuristic fields already extracted locally:\n"
            f"{json.dumps(heuristic_dump, ensure_ascii=False)}\n\n"
            "Extract the complete candidate profile with: name, email, phone, location, linkedin, summary, skills, "
            "experience, education, certifications, projects, publications.\n\n"
            f"RESUME TEXT:\n{resume_text}"
        )
        return await self.structured_completion("candidate_profile", CandidateProfile, system_prompt, user_prompt)

    async def fallback_normalize_skill(self, raw_skill: str, taxonomy_context: list[str]) -> SkillFallbackResponse:
        """Map an unknown skill string to the closest taxonomy skill using the LLM."""

        system_prompt = (
            "You normalize resume skills to a canonical taxonomy. Choose the closest canonical name "
            "from the provided taxonomy context when possible, and return confidence from 0 to 1."
        )
        user_prompt = (
            f"Raw skill: {raw_skill}\n"
            f"Taxonomy context: {', '.join(taxonomy_context[:50])}\n"
            "Return canonical_name, confidence, and reasoning."
        )
        return await self.structured_completion("skill_fallback", SkillFallbackResponse, system_prompt, user_prompt)

    async def parse_job_requirements(self, job_description: str) -> JobRequirementsPromptResponse:
        """Extract structured requirements from a job description."""

        system_prompt = (
            "You analyze job descriptions for recruiting intelligence. Extract required skills, preferred skills, "
            "minimum years of experience, and role level. When uncertain, prefer conservative extraction."
        )
        user_prompt = f"JOB DESCRIPTION:\n{job_description}"
        return await self.structured_completion("job_requirements", JobRequirementsPromptResponse, system_prompt, user_prompt)

    async def generate_recommendations(
        self,
        candidate_summary: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[str]:
        """Generate short actionable candidate-job fit recommendations."""

        system_prompt = (
            "You produce concise, actionable recommendations for improving candidate-job fit. "
            "Return 3 to 5 short bullets as a JSON array."
        )
        user_prompt = (
            f"Candidate summary: {candidate_summary}\n"
            f"Matched skills: {matched_skills}\n"
            f"Missing skills: {missing_skills}"
        )
        response = await self.structured_completion("recommendations", RecommendationResponse, system_prompt, user_prompt)
        return response.recommendations[:5]
