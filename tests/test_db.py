from e_block_bot.db import normalize_async_database_url


def test_normalize_postgres_urls_for_async_sqlalchemy() -> None:
    assert normalize_async_database_url("postgres://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    assert normalize_async_database_url("postgresql://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    assert normalize_async_database_url("sqlite+aiosqlite:///bot.db") == (
        "sqlite+aiosqlite:///bot.db"
    )
