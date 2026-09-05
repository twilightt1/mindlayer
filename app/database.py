from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


def _make_engine():
    """Create the async engine for the configured DATABASE_URL.

    Full-stack deployments use Postgres (pool sizing applies). Lite mode
    uses SQLite (`sqlite+aiosqlite`) with no pool sizing args — SQLite has
    no pool to size and SQLAlchemy would reject pool_size there.
    """
    if IS_SQLITE:
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.ENVIRONMENT == "development",
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.ENVIRONMENT == "development",
    )


engine = _make_engine()

if IS_SQLITE:
    # SQLite does not enforce foreign keys unless asked, and the memory
    # hub relies on ON DELETE CASCADE everywhere.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def bootstrap_sqlite() -> None:
    """Create all tables for the lite-mode SQLite deployment.

    Full-stack (Postgres) deployments use Alembic migrations instead —
    `docker compose up migrate` / `alembic upgrade head`. SQLite deployments
    are created fresh from the model metadata (no evolution history yet).
    """
    if not IS_SQLITE:
        raise RuntimeError("bootstrap_sqlite() is only for SQLite deployments")
    from app import models  # noqa: F401 — register every model on Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
