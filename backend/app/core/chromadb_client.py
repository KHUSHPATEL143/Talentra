"""ChromaDB client helpers and collection initialization."""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings

settings = get_settings()
chroma_client = None


def get_chroma_client() -> chromadb.HttpClient:
    """Return the shared ChromaDB HTTP client."""

    global chroma_client
    if chroma_client is None:
        chroma_client = chromadb.HttpClient(host=settings.chromadb_host, port=settings.chromadb_port)
    return chroma_client


def get_collection(name: str) -> Collection:
    """Return a ChromaDB collection configured for cosine similarity."""

    return get_chroma_client().get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def get_skill_collection() -> Collection:
    """Return the ChromaDB collection used for taxonomy skill embeddings."""

    return get_collection(settings.skill_embeddings_collection)


def get_candidate_collection() -> Collection:
    """Return the ChromaDB collection used for candidate embeddings."""

    return get_collection(settings.candidate_embeddings_collection)


def get_job_collection() -> Collection:
    """Return the ChromaDB collection used for job description embeddings."""

    return get_collection(settings.job_embeddings_collection)
