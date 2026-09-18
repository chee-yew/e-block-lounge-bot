"""Database engine and session management."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from e_block_bot.models import Base


def normalize_async_database_url(database_url: str) -> str:
    """Convert common PostgreSQL URLs to SQLAlchemy's async-driver form."""

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def create_engine(database_url: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine for the configured database."""

    return create_async_engine(normalize_async_database_url(database_url), pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create the application session factory."""

    return async_sessionmaker(engine, expire_on_commit=False)


async def init_database(engine: AsyncEngine) -> None:
    """Create tables for local development.

    Production deployments should run Alembic migrations instead.
    """

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database(engine: AsyncEngine) -> None:
    """Dispose all database connections."""

    await engine.dispose()


async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a session and roll it back if the caller fails."""

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
