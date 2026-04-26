"""API test environment defaults."""

import os

_API_TEST_ENV_DEFAULTS = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/ragdb_test",
    "REDIS_URL": "redis://localhost:6379/0",
    "JWT_SECRET_KEY": "test-secret-key-change-in-production",
    "ENVIRONMENT": "test",
}

for key, value in _API_TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)
