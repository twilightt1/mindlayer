"""Unit tests for hub models: shape, defaults, active logic."""
from __future__ import annotations

import uuid

from app.models.agent_client import AgentClient
from app.models.memory_access_log import MemoryAccessLog


def test_agent_client_defaults():
    client = AgentClient(user_id=uuid.uuid4(), name="Claude Desktop", token_hash="a" * 64)
    assert client.is_active is True
    assert client.scopes == ["memory:read"]
    assert client.status == "active"


def test_agent_client_revoked_is_inactive():
    client = AgentClient(user_id=uuid.uuid4(), name="Old Agent", token_hash="b" * 64, status="revoked")
    assert client.is_active is False


def test_access_log_defaults():
    entry = MemoryAccessLog(user_id=uuid.uuid4(), action="mcp_search")
    assert entry.detail == {}
    assert entry.memory_id is None
    assert entry.agent_client_id is None
