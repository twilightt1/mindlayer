"""
Cost & latency helpers for agents.

Tiny, dependency-free helpers that any agent can call to record
LLM usage against the central `CostTracker` (SQLite ledger) and the
per-request `AgentState`. Designed to be optional — agents that
don't call these helpers still work, they just don't record costs.
"""
from __future__ import annotations

import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.agents.state import AgentState


_DEFAULT_TRACKER: Any = None


def _get_tracker() -> Any:
    global _DEFAULT_TRACKER
    if _DEFAULT_TRACKER is None:
        from app.observability.cost import CostTracker

        _DEFAULT_TRACKER = CostTracker()
    return _DEFAULT_TRACKER


def record_cost(
    agent: str,
    state: "AgentState",
    model: str,
    tokens_in: int,
    tokens_out: int,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Record a cost event against both:
      - the global CostTracker (SQLite ledger) for cross-request analytics
      - the in-flight AgentState for per-request cost rollups

    Returns a dict with: agent, model, tokens_in, tokens_out, cost_usd.
    """
    from app.observability.cost import calculate_cost

    cost = calculate_cost(model, tokens_in, tokens_out)
    state.setdefault("cumulative_cost_usd", 0.0)
    state.setdefault("total_tokens_in", 0)
    state.setdefault("total_tokens_out", 0)
    state.setdefault("agent_costs", {})
    state["cumulative_cost_usd"] = round(state["cumulative_cost_usd"] + cost, 6)
    state["total_tokens_in"] += int(tokens_in)
    state["total_tokens_out"] += int(tokens_out)
    state["agent_costs"][agent] = round(state["agent_costs"].get(agent, 0.0) + cost, 6)

    if persist:
        try:
            _get_tracker().record(
                agent=agent,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                user_id=state.get("user_id"),
                conversation_id=state.get("conversation_id"),
            )
        except Exception:  # pragma: no cover - never let cost tracking break requests
            pass

    return {
        "agent": agent,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost,
    }


def record_latency(agent: str, state: "AgentState", latency_ms: float) -> None:
    """Record a per-agent latency measurement in the state."""
    state.setdefault("agent_latency_ms", {})
    state["agent_latency_ms"][agent] = round(
        state["agent_latency_ms"].get(agent, 0.0) + float(latency_ms),
        2,
    )


class Stopwatch:
    """Tiny stopwatch that records latency on exit."""

    def __init__(self, agent: str, state: "AgentState") -> None:
        self.agent = agent
        self.state = state
        self.start = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "Stopwatch":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.elapsed_ms = round((time.perf_counter() - self.start) * 1000, 2)
        record_latency(self.agent, self.state, self.elapsed_ms)


def get_total_cost(state: "AgentState") -> float:
    return float(state.get("cumulative_cost_usd", 0.0) or 0.0)


def get_total_tokens(state: "AgentState") -> tuple[int, int]:
    return (
        int(state.get("total_tokens_in", 0) or 0),
        int(state.get("total_tokens_out", 0) or 0),
    )


def cost_summary(state: "AgentState") -> dict[str, Any]:
    """Snapshot the per-request cost/latency summary."""
    tokens_in, tokens_out = get_total_tokens(state)
    return {
        "total_cost_usd": get_total_cost(state),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "agent_costs": dict(state.get("agent_costs", {}) or {}),
        "agent_latency_ms": dict(state.get("agent_latency_ms", {}) or {}),
    }


def merge_cost_summary(parts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Merge multiple `cost_summary` snapshots (e.g. across streamed tokens)."""
    total_cost = 0.0
    tokens_in = 0
    tokens_out = 0
    agent_costs: dict[str, float] = {}
    agent_latency: dict[str, float] = {}
    for p in parts:
        total_cost += float(p.get("total_cost_usd", 0.0) or 0.0)
        tokens_in += int(p.get("tokens_in", 0) or 0)
        tokens_out += int(p.get("tokens_out", 0) or 0)
        for k, v in (p.get("agent_costs") or {}).items():
            agent_costs[k] = round(agent_costs.get(k, 0.0) + float(v), 6)
        for k, v in (p.get("agent_latency_ms") or {}).items():
            agent_latency[k] = round(agent_latency.get(k, 0.0) + float(v), 2)
    return {
        "total_cost_usd": round(total_cost, 6),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "agent_costs": agent_costs,
        "agent_latency_ms": agent_latency,
    }
