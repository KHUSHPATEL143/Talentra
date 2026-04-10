"""Sentence-transformer embedding helpers."""

from __future__ import annotations

import asyncio
from functools import cached_property

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generate semantic embeddings for skills and job descriptions."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Store the transformer model name for lazy loading."""

        self.model_name = model_name

    @cached_property
    def model(self) -> SentenceTransformer:
        """Load and cache the embedding model."""

        return SentenceTransformer(self.model_name)

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""

        return await asyncio.to_thread(self._embed_single, text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings."""

        return await asyncio.to_thread(self._embed_many, texts)

    def _embed_single(self, text: str) -> list[float]:
        """Synchronous single-text embedding implementation."""

        vector = self.model.encode(text or "", normalize_embeddings=True)
        return vector.tolist()

    def _embed_many(self, texts: list[str]) -> list[list[float]]:
        """Synchronous batch embedding implementation."""

        if not texts:
            return []
        matrix = self.model.encode(texts, normalize_embeddings=True)
        return [row.tolist() for row in matrix]

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        """Return cosine similarity between two embedding vectors."""

        if not left or not right:
            return 0.0
        left_vector = np.array(left)
        right_vector = np.array(right)
        denominator = np.linalg.norm(left_vector) * np.linalg.norm(right_vector)
        if denominator == 0:
            return 0.0
        return float(np.dot(left_vector, right_vector) / denominator)

    def weighted_average(self, vectors: list[list[float]], weights: list[float]) -> list[float]:
        """Return a weighted average embedding."""

        if not vectors:
            return []
        matrix = np.array(vectors)
        weight_array = np.array(weights or [1.0] * len(vectors))
        total_weight = weight_array.sum()
        if total_weight == 0:
            weight_array = np.ones(len(vectors))
            total_weight = float(len(vectors))
        averaged = np.average(matrix, axis=0, weights=weight_array)
        normalized = averaged / max(np.linalg.norm(averaged), 1e-12)
        return normalized.tolist()
