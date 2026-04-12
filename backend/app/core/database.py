"""Database engine and session helpers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

from alembic import command
from alembic.config import Config

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.db import Base

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True, pool_pre_ping=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session."""

    async with AsyncSessionFactory() as session:
        yield session


async def init_database() -> None:
    """Apply Alembic migrations, falling back to direct table creation when needed."""

    alembic_ini_path = settings.resolved_alembic_ini_path
    if alembic_ini_path.exists():
        try:
            await asyncio.to_thread(_run_migrations, alembic_ini_path)
            return
        except Exception:
            pass

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


def _run_migrations(alembic_ini_path: Path) -> None:
    """Run Alembic migrations up to head using the configured ini file."""

    config = Config(str(alembic_ini_path))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
