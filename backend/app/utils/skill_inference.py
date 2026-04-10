"""Rule-based skill inference helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class InferenceRule:
    """Single skill inference rule."""

    triggers: list[str]
    infers: str


class SkillInferenceEngine:
    """Apply YAML-driven skill inference rules to a canonical skill set."""

    def __init__(self, rules: list[InferenceRule]) -> None:
        """Store inference rules for later evaluation."""

        self.rules = rules

    @classmethod
    def from_yaml(cls, path: Path) -> "SkillInferenceEngine":
        """Load inference rules from a YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rules = [
            InferenceRule(triggers=item.get("triggers", []), infers=item.get("infers", ""))
            for item in payload.get("rules", [])
            if item.get("triggers") and item.get("infers")
        ]
        return cls(rules)

    def apply(self, skills: set[str]) -> set[str]:
        """Return inferred skills that match the candidate skill set."""

        inferred: set[str] = set()
        for rule in self.rules:
            if all(trigger in skills for trigger in rule.triggers):
                inferred.add(rule.infers)
        return inferred
