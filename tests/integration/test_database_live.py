from __future__ import annotations

import pytest
from sqlalchemy import text

from app.database import engine

pytestmark = [pytest.mark.integration, pytest.mark.requires_infra]


@pytest.mark.asyncio
async def test_live_postgres_select_one():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
