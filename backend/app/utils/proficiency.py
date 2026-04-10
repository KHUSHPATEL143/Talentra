"""Skill proficiency estimation helpers."""

from __future__ import annotations

import re
from datetime import datetime

PROFICIENCY_WEIGHTS: dict[str, float] = {
    "beginner": 0.25,
    "intermediate": 0.5,
    "advanced": 0.75,
    "expert": 1.0,
}


def _contains_near_skill(text: str, skill: str, pattern: str) -> bool:
    """Check whether a skill appears close to a specific qualifier pattern."""

    escaped = re.escape(skill)
    combined = rf"({escaped}.{{0,40}}{pattern}|{pattern}.{{0,40}}{escaped})"
    return re.search(combined, text, flags=re.IGNORECASE) is not None


def estimate_skill_proficiency(skill: str, context_text: str) -> tuple[str, float, float]:
    """Estimate proficiency level, weight, and years of experience for a skill."""

    normalized_text = context_text or ""
    years = 0.0

    direct_years_pattern = re.compile(rf"(\d+(?:\.\d+)?)\+?\s+years?\s+(?:of\s+)?{re.escape(skill)}", re.IGNORECASE)
    direct_match = direct_years_pattern.search(normalized_text)
    if direct_match:
        years = float(direct_match.group(1))

    if years == 0.0:
        since_pattern = re.compile(rf"{re.escape(skill)}\s+since\s+(\d{{4}})", re.IGNORECASE)
        since_match = since_pattern.search(normalized_text)
        if since_match:
            years = max(datetime.utcnow().year - int(since_match.group(1)), 0)

    if _contains_near_skill(normalized_text, skill, r"expert|specialist|authority|guru"):
        level = "expert"
        years = max(years, 6.0)
    elif years >= 6 or _contains_near_skill(normalized_text, skill, r"advanced|proficient|strong"):
        level = "advanced" if years < 6 else "expert"
    elif 1 <= years < 3:
        level = "intermediate"
    elif 3 <= years < 6:
        level = "advanced"
    elif _contains_near_skill(normalized_text, skill, r"familiar|exposure|basic"):
        level = "beginner"
        years = max(years, 0.5)
    else:
        level = "beginner" if years < 1 else "intermediate"

    weight = PROFICIENCY_WEIGHTS[level]
    return level, weight, round(years, 2)
