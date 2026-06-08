"""Shared synchronous SQLAlchemy engine for Celery tasks.

Celery tasks run in synchronous worker processes and cannot use the async
engine from ``app.database``. Previously each task called
``create_engine(...)`` on every invocation, which created a brand-new
connection pool per task run and exhausted PostgreSQL connections under
load. This module exposes a single process-level engine + sessionmaker so
all tasks in a worker share one pool.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


@lru_cache(maxsize=1)
def get_sync_engine() -> Engine:
    """Return the process-wide synchronous engine, creating it on first use."""
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    return create_engine(
        sync_url,
        pool_pre_ping=True,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def _get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_sync_engine(), expire_on_commit=False, autoflush=False)


@contextmanager
def sync_session() -> Iterator[Session]:
    """Yield a synchronous session bound to the shared engine."""
    session = _get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
