"""Unit tests for MCP principal resolution. DB access is faked."""
from __future__ import annotations

import uuid

import pytest

from app.mcp_hub.identity import AgentPrincipal, extract_token
from app.services.agent_token_service import hash_token


def test_extract_token_bearer():
    assert extract_token({"Authorization": "Bearer oa_abc123"}) == "oa_abc123"
    assert extract_token({"authorization": "bearer oa_abc123"}) == "oa_abc123"


def test_extract_token_custom_header():
    assert extract_token({"X-Orivory-Agent-Token": "oa_xyz"}) == "oa_xyz"


def test_extract_token_missing():
    assert extract_token({}) is None
    assert extract_token({"Authorization": "Basic zzz"}) is None


def test_principal_scopes():
    p = AgentPrincipal(
        user_id=uuid.uuid4(),
        agent_client_id=uuid.uuid4(),
        name="Claude",
        scopes=frozenset({"memory:read"}),
    )
    assert p.can_read() and not p.can_write()


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalars(self):
        return self

    def first(self):
        return self._row


class _FakeDB:
    def __init__(self, row):
        self._row = row
        self.committed = False

    async def execute(self, _stmt):
        return _FakeResult(self._row)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_resolve_principal_found_and_updates_last_used():
    from app.mcp_hub.identity import resolve_principal
    from app.models.agent_client import AgentClient

    client = AgentClient(user_id=uuid.uuid4(), name="OpenClaw", token_hash=hash_token("oa_ok"), scopes=["memory:read", "memory:write"])
    db = _FakeDB(client)
    principal = await resolve_principal(db, "oa_ok")
    assert principal is not None
    assert principal.can_write()
    assert db.committed
    assert client.last_used_at is not None and client.last_used_at.tzinfo is not None


@pytest.mark.asyncio
async def test_resolve_principal_rejects_inactive_or_bad_token():
    from app.mcp_hub.identity import resolve_principal
    from app.models.agent_client import AgentClient

    revoked = AgentClient(user_id=uuid.uuid4(), name="Old", token_hash=hash_token("oa_rev"), status="revoked")
    assert await resolve_principal(_FakeDB(revoked), "oa_rev") is None
    assert await resolve_principal(_FakeDB(None), "oa_missing") is None
    assert await resolve_principal(_FakeDB(None), None) is None
