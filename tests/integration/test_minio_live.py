from __future__ import annotations

import pytest

from app import storage

pytestmark = [pytest.mark.integration, pytest.mark.requires_infra]


@pytest.mark.asyncio
async def test_live_minio_bucket_put_get_remove():
    object_name = "integration/live-minio-check.txt"
    payload = b"supportmind live minio integration"

    await storage.ensure_bucket()
    assert await storage.bucket_exists()

    await storage.put_object(object_name, payload, "text/plain")
    try:
        assert await storage.get_object(object_name) == payload
    finally:
        await storage.remove_object(object_name)
