from __future__ import annotations

import os

import pytest

_TEST_ENV_DEFAULTS = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/ragdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "JWT_SECRET_KEY": "test-secret-key-change-in-production",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
    "MINIO_BUCKET": "rag-docs",
    "MINIO_SECURE": "false",
    "CHROMA_HOST": "localhost",
    "CHROMA_PORT": "8001",
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "OPENAI_API_KEY": "test-openai-key",
    "JINA_API_KEY": "test-jina-key",
    "ENVIRONMENT": "test",
}

for key, value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)

pytestmark = [pytest.mark.integration, pytest.mark.requires_infra]


def pytest_runtest_setup(item):
    if "requires_infra" in item.keywords and os.getenv("RUN_LIVE_INTEGRATION") != "1":
        pytest.skip("Set RUN_LIVE_INTEGRATION=1 to run live integration tests.")
