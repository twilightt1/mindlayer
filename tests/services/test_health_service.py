import pytest

from app.services import health_service

pytestmark = pytest.mark.service


@pytest.mark.asyncio
async def test_check_readiness_ok(monkeypatch):
    async def ok():
        return None

    monkeypatch.setattr(health_service, "_check_postgres", ok)
    monkeypatch.setattr(health_service, "_check_redis", ok)
    monkeypatch.setattr(health_service, "_check_minio", ok)
    monkeypatch.setattr(health_service, "_check_chroma", ok)

    result = await health_service.check_readiness()

    assert result["status"] == "ok"
    assert set(result["checks"]) == {"postgres", "redis", "minio", "chroma"}
    assert all(check["status"] == "ok" for check in result["checks"].values())


@pytest.mark.asyncio
async def test_check_readiness_degraded_when_dependency_fails(monkeypatch):
    async def ok():
        return None

    async def failed():
        raise RuntimeError("connection refused to test dependency")

    monkeypatch.setattr(health_service, "_check_postgres", ok)
    monkeypatch.setattr(health_service, "_check_redis", ok)
    monkeypatch.setattr(health_service, "_check_minio", ok)
    monkeypatch.setattr(health_service, "_check_chroma", failed)

    result = await health_service.check_readiness()

    assert result["status"] == "degraded"
    assert result["checks"]["chroma"]["status"] == "failed"
    assert "connection refused" in result["checks"]["chroma"]["error"]
    assert result["checks"]["postgres"]["status"] == "ok"


def test_sanitize_error_limits_length_and_removes_newlines():
    error = RuntimeError("line one\n" + "x" * 500)

    message = health_service._sanitize_error(error)

    assert "\n" not in message
    assert len(message) == 300
