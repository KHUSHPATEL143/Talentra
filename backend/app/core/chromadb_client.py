"""ChromaDB client helpers and collection initialization."""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings

settings = get_settings()
chroma_client = chromadb.HttpClient(host=settings.chromadb_host, port=settings.chromadb_port)


def get_skill_collection() -> Collection:
    """Return the ChromaDB collection used for skill embeddings."""

    return chroma_client.get_or_create_collection(name=settings.chromadb_collection, metadata={"hnsw:space": "cosine"})
