"""OpenAI structured output wrapper with retry support."""

from __future__ import annotations

import asyncio
import json
from typing import Any, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.schemas import (
    CandidateProfile,
    JobRequirementsPromptResponse,
    RecommendationResponse,
    SkillFallbackResponse,
)

SchemaModel = TypeVar("SchemaModel", bound=BaseModel)


class LLMService:
    """Thin async wrapper around OpenAI chat completions with JSON schema outputs."""

    def __init__(self) -> None:
        """Initialize the async OpenAI client."""

        settings = get_settings()
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

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
        """Call the chat completion API with exponential backoff."""

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM-powered workflows.")

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }

        for attempt in range(retries):
            try:
                response = await self.client.chat.completions.create(
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
            except Exception:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        return {}

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
