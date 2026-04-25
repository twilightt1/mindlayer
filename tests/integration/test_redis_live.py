from __future__ import annotations

import pytest

from app.redis_client import get_redis

pytestmark = [pytest.mark.integration, pytest.mark.requires_infra]


@pytest.mark.asyncio
async def test_live_redis_ping_set_get_delete():
    redis = await get_redis()
    try:
        assert await redis.ping() is True
        await redis.set("supportmind:integration:redis", "ok", ex=30)
        assert await redis.get("supportmind:integration:redis") == "ok"
        assert await redis.delete("supportmind:integration:redis") == 1
    finally:
        await redis.aclose()
