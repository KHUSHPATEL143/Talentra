"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central application configuration."""

    app_name: str = "Talentra - Talent Intelligence Platform"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    environment: str = "development"
    log_level: str = "INFO"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    llm_provider: str = "openai"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/garuda"
    mongodb_url: str = "mongodb://localhost:27017/talentra"
    redis_url: str = "redis://localhost:6379/0"
    redis_url: str = "redis://redis:6379/0"
    chromadb_host: str = "localhost"
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
    default_api_key: str = ""
    frontend_origin: str = "http://localhost:3000"
    taxonomy_path: str = Field(default="data/taxonomy/skills_taxonomy.json")
    inference_rules_path: str = Field(default="data/taxonomy/inference_rules.yaml")

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

        path = Path(self.taxonomy_path)
        return path if path.is_absolute() else (BASE_DIR / path).resolve()

    @property
    def resolved_inference_rules_path(self) -> Path:
        """Return the absolute path to the inference rules file."""

        path = Path(self.inference_rules_path)
        return path if path.is_absolute() else (BASE_DIR / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings()
