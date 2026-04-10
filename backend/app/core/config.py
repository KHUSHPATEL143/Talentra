"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    app_name: str = "GARUDA Resume Intelligence API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    log_level: str = "INFO"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/garuda"
    redis_url: str = "redis://redis:6379/0"
    chromadb_host: str = "chromadb"
    chromadb_port: int = 8000
    chromadb_collection: str = "skills"
    default_match_mode: str = "precision"
    match_precision_threshold: float = 0.75
    match_recall_threshold: float = 0.55
    max_workers: int = 4
    max_file_size_mb: int = 10
    max_batch_files: int = 50
    redis_cache_ttl_seconds: int = 3600
    webhook_timeout_seconds: int = 10
    default_api_key_owner: str = "local-dev"
    frontend_origin: str = "http://localhost:3000"
    taxonomy_path: str = Field(default="backend/data/taxonomy/skills_taxonomy.json")
    inference_rules_path: str = Field(default="backend/data/taxonomy/inference_rules.yaml")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Return the maximum accepted upload size in bytes."""

        return self.max_file_size_mb * 1024 * 1024

    @property
    def resolved_taxonomy_path(self) -> Path:
        """Return the absolute path to the taxonomy seed file."""

        return Path(self.taxonomy_path).resolve()

    @property
    def resolved_inference_rules_path(self) -> Path:
        """Return the absolute path to the inference rules file."""

        return Path(self.inference_rules_path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings()
