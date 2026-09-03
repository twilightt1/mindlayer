"""Unit tests for agent token generation and validation."""
from __future__ import annotations

import hashlib

import pytest

from app.services.agent_token_service import (
    generate_token,
    hash_token,
    token_hash_prefix,
    validate_scopes,
)


def test_generate_token_format():
    token = generate_token()
    assert token.startswith("oa_")
    assert len(token) == 3 + 32
    int(token[3:], 16)  # hex-parseable


def test_generate_token_unique():
    assert len({generate_token() for _ in range(100)}) == 100


def test_hash_token_is_sha256():
    assert hash_token("oa_abc") == hashlib.sha256(b"oa_abc").hexdigest()


def test_token_hash_prefix_is_safe():
    assert token_hash_prefix("oa_abc") == hash_token("oa_abc")[:8]
    assert len(token_hash_prefix("oa_abc")) == 8


def test_validate_scopes_ok():
    assert validate_scopes(["memory:read", "memory:write"]) == ["memory:read", "memory:write"]
    assert validate_scopes([]) == ["memory:read"]


def test_validate_scopes_rejects_unknown():
    with pytest.raises(ValueError, match="unknown scope"):
        validate_scopes(["admin:all"])
