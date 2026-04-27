from redis.asyncio import ConnectionPool, Redis
from app.config import settings

_pool: ConnectionPool | None = None
_pool_loop: object | None = None


def get_pool() -> ConnectionPool:
    global _pool, _pool_loop
    try:
        import asyncio

        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _pool is None or (_pool_loop is not None and current_loop is not None and _pool_loop is not current_loop):
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_MAX,
            decode_responses=True,
        )
        _pool_loop = current_loop
    return _pool


async def get_redis() -> Redis:
    return Redis(connection_pool=get_pool())
