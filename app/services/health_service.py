from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from sqlalchemy import text

from app.config import settings

CheckPayload = dict[str, Any]
CheckFn = Callable[[], Awaitable[None]]


async def _check_postgres() -> None:
    from app.database import engine

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis() -> None:
    from app.redis_client import get_redis

    redis = await get_redis()
    try:
        await redis.ping()
    finally:
        await redis.aclose()


async def _check_minio() -> None:
    from app.storage import bucket_exists

    exists = await bucket_exists(settings.MINIO_BUCKET)
    if not exists:
        raise RuntimeError(f"MinIO bucket '{settings.MINIO_BUCKET}' does not exist")


async def _check_chroma() -> None:
    url = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/heartbeat"
    async with httpx.AsyncClient(timeout=2.0) as client:
        response = await client.get(url)
        response.raise_for_status()


def _sanitize_error(error: Exception) -> str:
    message = str(error).replace("\n", " ").strip()
    if not message:
        message = error.__class__.__name__
    return message[:300]


async def _measure(name: str, checker: CheckFn) -> tuple[str, CheckPayload]:
    started = time.perf_counter()
    try:
        await checker()
        return name, {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except Exception as exc:
        return name, {
            "status": "failed",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": _sanitize_error(exc),
        }


def _default_readiness_checkers() -> dict[str, CheckFn]:
    return {
        "postgres": _check_postgres,
        "redis": _check_redis,
        "minio": _check_minio,
        "chroma": _check_chroma,
    }


async def run_readiness_checks(
    extra_checkers: dict[str, CheckFn] | None = None,
) -> dict[str, CheckPayload]:
    checkers = _default_readiness_checkers()
    if extra_checkers:
        checkers.update(extra_checkers)
    results = await asyncio.gather(
        *[_measure(name, checker) for name, checker in checkers.items()]
    )
    return dict(results)


async def check_readiness() -> CheckPayload:
    checks = await run_readiness_checks()
    status = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
    return {
        "status": status,
        "version": "1.0.0",
        "checks": checks,
    }
