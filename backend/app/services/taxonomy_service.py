"""Taxonomy CRUD, seeding, and normalization helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chromadb_client import get_skill_collection
from app.core.config import get_settings
from app.models.db import PendingTaxonomyReview, SkillTaxonomy
from app.models.schemas import SkillFallbackResponse, TaxonomySearchResult
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


class TaxonomyService:
    """Service responsible for taxonomy loading, querying, and normalization support."""

    def __init__(self, embedding_service: EmbeddingService, llm_service: LLMService) -> None:
        """Store shared services and precompute in-memory indexes."""

        self.settings = get_settings()
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.taxonomy_entries = self._load_taxonomy_file(self.settings.resolved_taxonomy_path)
        self.alias_index = self._build_alias_index(self.taxonomy_entries)
        self.normalized_alias_index = self._build_normalized_alias_index(self.taxonomy_entries)
        self.fuzzy_choices = list(self.normalized_alias_index.keys())
        self.collection = get_skill_collection()
        self._llm_cache: dict[str, SkillFallbackResponse] = {}

    def _load_taxonomy_file(self, path: Path) -> list[dict[str, Any]]:
        """Load taxonomy JSON entries from disk."""

        return json.loads(path.read_text(encoding="utf-8"))

    def _build_alias_index(self, entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Build a fast lowercase alias lookup index."""

        index: dict[str, dict[str, Any]] = {}
        for entry in entries:
            values = [entry["canonical_name"], *entry.get("aliases", [])]
            for value in values:
                index[value.strip().lower()] = entry
        return index

    def _build_normalized_alias_index(self, entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Build a punctuation-tolerant alias lookup index."""

        index: dict[str, dict[str, Any]] = {}
        for entry in entries:
            values = [entry["canonical_name"], *entry.get("aliases", [])]
            for value in values:
                normalized = self._normalize_lookup_key(value)
                if normalized:
                    index[normalized] = entry
        return index

    def _normalize_lookup_key(self, value: str) -> str:
        """Normalize skill text so common punctuation and spacing variants resolve locally."""

        lowered = value.strip().lower().replace("&", " and ")
        lowered = lowered.replace(".js", " js").replace(".net", " net")
        lowered = re.sub(r"[^a-z0-9+#]+", " ", lowered)
        return re.sub(r"\s+", " ", lowered).strip()

    async def seed_taxonomy(self, session: AsyncSession) -> None:
        """Seed PostgreSQL and ChromaDB with taxonomy data when empty."""

        count = await session.scalar(select(func.count()).select_from(SkillTaxonomy))
        if count and count > 0:
            return

        records = [
            SkillTaxonomy(
                canonical_name=entry["canonical_name"],
                category=entry["category"],
                subcategory=entry["subcategory"],
                parent_id=entry.get("parent_id"),
                aliases=entry.get("aliases", []),
            )
            for entry in self.taxonomy_entries
        ]
        session.add_all(records)
        await session.commit()

        names = [entry["canonical_name"] for entry in self.taxonomy_entries]
        embeddings = await self.embedding_service.embed_batch(names)
        metadatas = [
            {"category": entry["category"], "subcategory": entry["subcategory"]}
            for entry in self.taxonomy_entries
        ]
        self.collection.upsert(ids=names, embeddings=embeddings, metadatas=metadatas, documents=names)

    def exact_match(self, raw_skill: str) -> dict[str, Any] | None:
        """Return an exact taxonomy match for a skill alias."""

        stripped = raw_skill.strip().lower()
        if stripped in self.alias_index:
            return self.alias_index[stripped]
        normalized = self._normalize_lookup_key(raw_skill)
        if normalized:
            return self.normalized_alias_index.get(normalized)
        return None

    def fuzzy_match(self, raw_skill: str, threshold: int = 85) -> tuple[dict[str, Any] | None, float]:
        """Return the best fuzzy match above threshold."""

        normalized = self._normalize_lookup_key(raw_skill)
        if not normalized:
            return None, 0.0
        result = process.extractOne(normalized, self.fuzzy_choices, scorer=fuzz.token_sort_ratio)
        if not result:
            return None, 0.0
        choice, score, _ = result
        if score < threshold:
            return None, float(score) / 100.0
        return self.normalized_alias_index[choice], float(score) / 100.0

    async def embedding_match(self, raw_skill: str, threshold: float = 0.82) -> tuple[dict[str, Any] | None, float]:
        """Return the best embedding-based taxonomy match."""

        query_embedding = await self.embedding_service.embed_text(raw_skill)
        result = self.collection.query(query_embeddings=[query_embedding], n_results=1)
        if not result["ids"] or not result["ids"][0]:
            return None, 0.0
        skill_name = result["ids"][0][0]
        distance = result["distances"][0][0] if result.get("distances") else 1.0
        similarity = max(0.0, 1.0 - float(distance))
        if similarity < threshold:
            return None, similarity
        return self.alias_index[skill_name.lower()], similarity

    async def llm_match(self, raw_skill: str) -> SkillFallbackResponse:
        """Use the LLM to map a skill to the taxonomy."""

        cache_key = self._normalize_lookup_key(raw_skill) or raw_skill.strip().lower()
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        context = self._build_llm_context(raw_skill)
        result = await self.llm_service.fallback_normalize_skill(raw_skill, context)
        self._llm_cache[cache_key] = result
        return result

    def _build_llm_context(self, raw_skill: str, limit: int = 25) -> list[str]:
        """Return a narrowed taxonomy context for LLM fallback prompts."""

        normalized = self._normalize_lookup_key(raw_skill)
        if normalized:
            candidates = process.extract(normalized, self.fuzzy_choices, scorer=fuzz.token_sort_ratio, limit=limit)
            context = [self.normalized_alias_index[choice]["canonical_name"] for choice, _, _ in candidates]
            deduped = list(dict.fromkeys(context))
            if deduped:
                return deduped
        return [entry["canonical_name"] for entry in self.taxonomy_entries[:limit]]

    async def mark_pending_review(
        self,
        session: AsyncSession,
        raw_skill: str,
        suggested_canonical: str | None,
        confidence: float,
    ) -> PendingTaxonomyReview:
        """Persist a low-confidence emerging skill for review."""

        pending = PendingTaxonomyReview(
            raw_skill=raw_skill,
            suggested_canonical=suggested_canonical,
            confidence=confidence,
            status="pending",
        )
        session.add(pending)
        await session.commit()
        await session.refresh(pending)
        return pending

    async def list_entries(
        self,
        session: AsyncSession,
        category: str | None,
        parent_id: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[SkillTaxonomy], int]:
        """Return paginated taxonomy entries."""

        filters = []
        if category:
            filters.append(SkillTaxonomy.category == category)
        if parent_id is not None:
            filters.append(SkillTaxonomy.parent_id == parent_id)

        total_query = select(func.count()).select_from(SkillTaxonomy)
        items_query = select(SkillTaxonomy).order_by(SkillTaxonomy.category, SkillTaxonomy.subcategory, SkillTaxonomy.canonical_name)
        for clause in filters:
            total_query = total_query.where(clause)
            items_query = items_query.where(clause)

        total = int(await session.scalar(total_query) or 0)
        result = await session.execute(items_query.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def search(self, query: str, limit: int = 10) -> list[TaxonomySearchResult]:
        """Run semantic search against the ChromaDB skill collection."""

        query_embedding = await self.embedding_service.embed_text(query)
        result = self.collection.query(query_embeddings=[query_embedding], n_results=limit)
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        output: list[TaxonomySearchResult] = []
        for skill_name, distance, metadata in zip(ids, distances, metadatas, strict=False):
            output.append(
                TaxonomySearchResult(
                    canonical_name=skill_name,
                    category=metadata.get("category", ""),
                    subcategory=metadata.get("subcategory", ""),
                    similarity=max(0.0, 1.0 - float(distance)),
                )
            )
        return output
