"""Deterministic job-description parsing and recommendation helpers."""

from __future__ import annotations

import re

from app.models.schemas import JobRequirementExtraction

ROLE_LEVEL_HINTS = {
    "intern": "intern",
    "junior": "junior",
    "associate": "junior",
    "mid": "mid",
    "senior": "senior",
    "staff": "staff",
    "lead": "lead",
    "principal": "principal",
    "manager": "manager",
}


class JobHeuristicService:
    """Extract structured job information without using an LLM when possible."""

    def __init__(self, canonical_skills: list[str]) -> None:
        """Store the canonical skills used for rule-based job parsing."""

        self.canonical_skills = canonical_skills

    def extract_requirements(self, job_description: str) -> JobRequirementExtraction:
        """Extract required/preferred skills, experience, and role level from text."""

        lowered = job_description.lower()
        required_section = self._extract_section(lowered, ["required", "must have", "requirements", "qualification"])
        preferred_section = self._extract_section(lowered, ["preferred", "nice to have", "bonus", "plus"])

        required_skills = self._find_skills(required_section or lowered)
        preferred_skills = self._find_skills(preferred_section)

        if not required_skills:
            all_skills = self._find_skills(lowered)
            required_skills = all_skills[:8]
            preferred_skills = [skill for skill in all_skills[8:12] if skill not in required_skills]

        min_experience_years = self._extract_experience_years(job_description)
        role_level = self._extract_role_level(lowered)

        return JobRequirementExtraction(
            required_skills=required_skills,
            preferred_skills=[skill for skill in preferred_skills if skill not in required_skills],
            min_experience_years=min_experience_years,
            role_level=role_level,
        )

    def generate_recommendations(
        self,
        matched_skills: list[str],
        missing_skills: list[str],
        experience_match: float,
    ) -> list[str]:
        """Generate simple actionable recommendations without an LLM."""

        recommendations: list[str] = []
        if missing_skills:
            recommendations.append(f"Prioritize hands-on experience in {', '.join(missing_skills[:3])}.")
        if experience_match < 0.6:
            recommendations.append("Show deeper project evidence or quantified impact for the target role level.")
        if matched_skills:
            recommendations.append(f"Highlight strong overlap in {', '.join(matched_skills[:3])} at the top of the resume.")
        if not recommendations:
            recommendations.append("Emphasize the strongest matching projects and measurable outcomes during screening.")
        recommendations.append("Tailor the summary section to align directly with the job’s top requirements.")
        return recommendations[:5]

    def _extract_section(self, text: str, labels: list[str]) -> str:
        """Extract a likely subsection of a job description based on headings or phrases."""

        lines = text.splitlines()
        collected: list[str] = []
        capture = False
        label_set = {label.lower() for label in labels}
        for line in lines:
            normalized = line.strip().lower().rstrip(":")
            if normalized in label_set or any(label in normalized for label in label_set):
                capture = True
                continue
            if capture and normalized and len(normalized.split()) <= 4 and normalized.endswith(":"):
                break
            if capture and line.strip():
                collected.append(line.strip())
        return "\n".join(collected)

    def _find_skills(self, text: str) -> list[str]:
        """Find canonical skills mentioned in a block of job-description text."""

        detected: list[str] = []
        lowered = text.lower()
        for skill in self.canonical_skills:
            pattern = rf"\b{re.escape(skill.lower())}\b"
            if re.search(pattern, lowered):
                detected.append(skill)
        return detected

    def _extract_experience_years(self, text: str) -> float:
        """Extract minimum years of experience from the job description."""

        patterns = [
            r"(\d+(?:\.\d+)?)\+?\s+years?\s+of\s+experience",
            r"minimum\s+of\s+(\d+(?:\.\d+)?)\s+years?",
            r"(\d+(?:\.\d+)?)\+?\s+years?\s+experience",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0

    def _extract_role_level(self, lowered_text: str) -> str:
        """Infer role level from common role seniority words."""

        for token, mapped in ROLE_LEVEL_HINTS.items():
            if re.search(rf"\b{re.escape(token)}\b", lowered_text):
                return mapped
        return ""
