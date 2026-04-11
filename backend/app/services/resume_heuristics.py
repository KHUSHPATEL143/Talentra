"""Deterministic resume field extraction for low-cost parsing."""

from __future__ import annotations

import re

from app.models.schemas import CandidateProfile, Location

HEADING_PATTERNS = [
    "summary",
    "profile",
    "professional summary",
    "about",
    "objective",
    "experience",
    "work experience",
    "education",
    "projects",
    "certifications",
    "publications",
    "skills",
    "technical skills",
    "core competencies",
]

COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "node",
    "fastapi",
    "flask",
    "django",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "langchain",
    "openai api",
    "git",
    "github actions",
    "jenkins",
    "html",
    "css",
    "tailwind",
}


class ResumeHeuristicService:
    """Extract easy resume fields locally to reduce LLM usage."""

    def extract_profile(self, raw_text: str) -> CandidateProfile:
        """Return a lightweight candidate profile built from regex and section parsing."""

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        email = self._extract_email(raw_text)
        phone = self._extract_phone(raw_text)
        linkedin = self._extract_linkedin(raw_text)
        name = self._extract_name(lines)
        location = self._extract_location(lines)
        summary = self._extract_summary(raw_text)
        skills = self._extract_skills(raw_text)
        return CandidateProfile(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin=linkedin,
            summary=summary,
            skills=skills,
        )

    def merge_profiles(self, heuristic: CandidateProfile, llm_profile: CandidateProfile) -> CandidateProfile:
        """Merge deterministic fields into the LLM profile, preferring local basics when missing."""

        merged = llm_profile.model_dump()
        heuristic_dump = heuristic.model_dump()

        for key in ("name", "email", "phone", "linkedin", "summary"):
            if not merged.get(key) and heuristic_dump.get(key):
                merged[key] = heuristic_dump[key]

        if not any(merged.get("location", {}).values()) and any(heuristic_dump.get("location", {}).values()):
            merged["location"] = heuristic_dump["location"]

        if not merged.get("skills") and heuristic_dump.get("skills"):
            merged["skills"] = heuristic_dump["skills"]
        elif heuristic_dump.get("skills"):
            merged["skills"] = self._dedupe_strings([*heuristic_dump["skills"], *merged["skills"]])

        return CandidateProfile.model_validate(merged)

    def _extract_email(self, text: str) -> str:
        """Extract the first email address."""

        match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, flags=re.IGNORECASE)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """Extract a plausible phone number."""

        matches = re.findall(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}", text)
        for match in matches:
            digits = re.sub(r"\D", "", match)
            if 10 <= len(digits) <= 15:
                return match.strip()
        return ""

    def _extract_linkedin(self, text: str) -> str:
        """Extract a LinkedIn URL or handle."""

        match = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s|]+", text, flags=re.IGNORECASE)
        if match:
            value = match.group(0)
            return value if value.startswith("http") else f"https://{value}"
        return ""

    def _extract_name(self, lines: list[str]) -> str:
        """Infer candidate name from the header lines."""

        for line in lines[:8]:
            lowered = line.lower()
            if any(token in lowered for token in ("resume", "curriculum", "linkedin", "github", "@", "http")):
                continue
            if any(char.isdigit() for char in line):
                continue
            words = re.findall(r"[A-Za-z]+", line)
            if 2 <= len(words) <= 4 and all(len(word) > 1 for word in words):
                return " ".join(word.capitalize() for word in words)
        return ""

    def _extract_location(self, lines: list[str]) -> Location:
        """Extract a simple city/country style location from header lines."""

        for line in lines[:10]:
            lowered = line.lower()
            if any(token in lowered for token in ("linkedin", "github", "@", "http")):
                continue
            if re.search(r"\d", line):
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if 2 <= len(parts) <= 3 and all(len(part) > 1 for part in parts):
                return Location(city=parts[0], country=parts[-1])
        return Location()

    def _extract_summary(self, text: str) -> str:
        """Extract a summary/profile section when present."""

        section = self._extract_section(
            text,
            start_labels=["summary", "professional summary", "profile", "about", "objective"],
        )
        if section:
            return section[:800].strip()
        paragraphs = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        for paragraph in paragraphs[:3]:
            if len(paragraph.split()) >= 12:
                return paragraph[:800]
        return ""

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills from skills sections and common technology mentions."""

        section = self._extract_section(
            text,
            start_labels=["skills", "technical skills", "core competencies", "tech stack"],
        )
        detected: list[str] = []
        if section:
            detected.extend(self._split_skill_tokens(section))

        lowered = text.lower()
        for skill in COMMON_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", lowered):
                detected.append(skill)

        return self._dedupe_strings([self._normalize_skill_name(item) for item in detected if item.strip()])

    def _extract_section(self, text: str, start_labels: list[str]) -> str:
        """Return the text belonging to a named resume section."""

        lines = text.splitlines()
        capture = False
        collected: list[str] = []
        start_set = {label.lower() for label in start_labels}
        for line in lines:
            normalized = line.strip().lower().rstrip(":")
            if normalized in start_set:
                capture = True
                continue
            if capture and normalized in HEADING_PATTERNS:
                break
            if capture and line.strip():
                collected.append(line.strip())
        return "\n".join(collected).strip()

    def _split_skill_tokens(self, section: str) -> list[str]:
        """Split a skills section into candidate skill tokens."""

        flattened = section.replace("\n", ",").replace("|", ",").replace("•", ",")
        return [token.strip(" -:\t") for token in flattened.split(",") if token.strip()]

    def _normalize_skill_name(self, value: str) -> str:
        """Normalize a skill token into a display-friendly label."""

        lowered = value.strip().lower()
        special_cases = {
            "node": "Node.js",
            "node.js": "Node.js",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "aws": "AWS",
            "gcp": "GCP",
            "html": "HTML",
            "css": "CSS",
        }
        return special_cases.get(lowered, value.strip().title())

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        """Return strings with order preserved and duplicates removed."""

        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            key = value.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(value.strip())
        return output
