"""Tests for agent cost/latency helpers."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.agents.cost_helpers import (
    Stopwatch,
    cost_summary,
    get_total_cost,
    get_total_tokens,
    merge_cost_summary,
    record_cost,
    record_latency,
)
from app.agents.state import AgentState


def _state() -> AgentState:
    return AgentState(
        user_id="u1",
        conversation_id="c1",
        query="hi",
    )


class TestRecordCost:
    def test_records_into_state(self) -> None:
        state = _state()
        record_cost("router", state, "openai/gpt-4o-mini", 1000, 500, persist=False)
        record_cost("answer", state, "openai/gpt-4o-mini", 2000, 1000, persist=False)
        assert get_total_cost(state) > 0
        in_t, out_t = get_total_tokens(state)
        assert in_t == 3000
        assert out_t == 1500
        # Per-agent cost present
        assert "router" in state["agent_costs"]
        assert "answer" in state["agent_costs"]

    def test_unknown_model_zero_cost(self) -> None:
        state = _state()
        record_cost("router", state, "unknown/model", 1000, 500, persist=False)
        assert get_total_cost(state) == 0.0
        # Tokens are still counted
        in_t, _ = get_total_tokens(state)
        assert in_t == 1000


class TestRecordLatency:
    def test_accumulates(self) -> None:
        state = _state()
        record_latency("router", state, 120.5)
        record_latency("router", state, 80.3)
        assert state["agent_latency_ms"]["router"] == 200.8


class TestStopwatch:
    def test_measures(self) -> None:
        state = _state()
        with Stopwatch("router", state) as sw:
            sum(range(1000))
        assert sw.elapsed_ms >= 0
        assert state["agent_latency_ms"]["router"] == sw.elapsed_ms


class TestCostSummary:
    def test_returns_full_summary(self) -> None:
        state = _state()
        record_cost("router", state, "openai/gpt-4o-mini", 1000, 500, persist=False)
        record_latency("router", state, 120.0)
        summary = cost_summary(state)
        assert summary["tokens_in"] == 1000
        assert summary["tokens_out"] == 500
        assert "router" in summary["agent_costs"]
        assert "router" in summary["agent_latency_ms"]


class TestMergeCostSummary:
    def test_merges(self) -> None:
        a = {"total_cost_usd": 0.1, "tokens_in": 100, "tokens_out": 50,
             "agent_costs": {"router": 0.1}, "agent_latency_ms": {"router": 100}}
        b = {"total_cost_usd": 0.2, "tokens_in": 200, "tokens_out": 100,
             "agent_costs": {"answer": 0.2}, "agent_latency_ms": {"answer": 200}}
        merged = merge_cost_summary([a, b])
        assert merged["total_cost_usd"] == pytest.approx(0.3)
        assert merged["tokens_in"] == 300
        assert merged["tokens_out"] == 150
        assert "router" in merged["agent_costs"]
        assert "answer" in merged["agent_costs"]


import pytest  # noqa: E402
