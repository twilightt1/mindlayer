import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_conversations_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/chat/conversations")
    # Missing credentials should yield 401; some deployments surface 403 for
    # the same case. Accept either to remain tolerant of middleware config.
    assert resp.status_code in (401, 403)
