"""P4 hardening tests: email normalization, context budget, query limits."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.rag


class TestEmailNormalization:
    def test_register_lowercases_full_address(self):
        from app.schemas.auth import RegisterRequest

        r = RegisterRequest(email="User.Name@Example.COM", password="secret12")
        assert r.email == "user.name@example.com"

    def test_login_strips_and_lowercases(self):
        from app.schemas.auth import LoginRequest

        r = LoginRequest(email="  MiXeD@Case.io  ", password="x")
        assert r.email == "mixed@case.io"

    def test_forgot_password_normalizes(self):
        from app.schemas.auth import ForgotPasswordRequest

        r = ForgotPasswordRequest(email="HELP@Domain.ORG")
        assert r.email == "help@domain.org"

    def test_otp_verify_normalizes(self):
        from app.schemas.auth import OTPVerifyRequest

        r = OTPVerifyRequest(email="A@B.Com", otp_code="123456")
        assert r.email == "a@b.com"


class TestChatRequestLimits:
    def test_query_max_length_enforced(self):
        from pydantic import ValidationError

        from app.schemas.conversation import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(query="x" * 10_001)

    def test_query_within_limit_ok(self):
        from app.schemas.conversation import ChatRequest

        req = ChatRequest(query="x" * 10_000)
        assert len(req.query) == 10_000


class TestContextBudget:
    def _chunk(self, mid: str, n: int):
        return {"content": "x" * n, "metadata": {"memory_id": mid}}

    def test_first_chunk_always_kept_even_if_over_budget(self):
        from app.agents.context_merge_agent import merge_context_chunks

        state = {"reranked_chunks": [self._chunk("m1", 1000)]}
        merged, dropped = merge_context_chunks(state, char_budget=10)
        assert len(merged) == 1  # never send empty context
        assert dropped == 0

    def test_chunks_beyond_budget_dropped(self):
        from app.agents.context_merge_agent import merge_context_chunks

        state = {
            "reranked_chunks": [
                self._chunk("m1", 100),
                self._chunk("m2", 100),
                self._chunk("m3", 100),
            ]
        }
        merged, dropped = merge_context_chunks(state, char_budget=150)
        assert len(merged) == 1  # 100 fits, +100 would exceed 150
        assert dropped == 2

    def test_priority_order_preserved_under_budget(self):
        from app.agents.context_merge_agent import merge_context_chunks

        state = {
            "reranked_chunks": [self._chunk("doc1", 100)],
            "personal_memory_chunks": [self._chunk("mem1", 100)],
        }
        # Budget fits only the first (document) group chunk.
        merged, dropped = merge_context_chunks(state, char_budget=150)
        assert [c["metadata"]["memory_id"] for c in merged] == ["doc1"]
        assert dropped == 1

    def test_count_cap_still_applies(self):
        from app.agents.context_merge_agent import merge_context_chunks

        state = {"reranked_chunks": [self._chunk(f"m{i}", 1) for i in range(20)]}
        merged, dropped = merge_context_chunks(state, max_chunks=5, char_budget=10_000)
        assert len(merged) == 5
