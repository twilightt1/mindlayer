from __future__ import annotations

import httpx
import pytest

from app.config import settings

pytestmark = [pytest.mark.integration, pytest.mark.requires_infra]


@pytest.mark.asyncio
async def test_live_chroma_heartbeat():
    url = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/heartbeat"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)

    assert response.status_code == 200
    assert response.json()
