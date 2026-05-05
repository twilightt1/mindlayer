"""
Per-query cost estimation for SupportMind.

The agent graph typically makes 3-5 LLM calls per request:
  - router, evaluator, hallucination, answer
  - possibly more on retries

This module estimates total cost given a model and call count.
"""
from __future__ import annotations

from collections.abc import Iterable

from app.observability.cost import calculate_cost, PRICING


# Average token counts observed in production (per call type).
# These are starting points — replace with measured values from your own logs.
DEFAULT_TOKENS_PER_CALL: dict[str, tuple[int, int]] = {
    "router":        (350, 80),
    "retrieval":     (0, 0),   # No LLM
    "evaluator":     (450, 30),
    "answer":        (1200, 400),
    "hallucination": (500, 30),
}


def estimate_query_cost(
    model: str,
    call_breakdown: dict[str, int] | None = None,
    avg_tokens_per_call: dict[str, tuple[int, int]] | None = None,
) -> dict[str, dict[str, float]]:
    """
    Return per-agent cost breakdown + total for a single query.

    Args:
        model: LLM model identifier (must be in PRICING for non-zero cost).
        call_breakdown: optional dict of {agent_name: num_calls}. Defaults to
            one call per agent.
        avg_tokens_per_call: override the default per-agent token counts.

    Returns:
        Dict with 'per_agent' and 'total' keys.
    """
    breakdown = call_breakdown or {name: 1 for name in DEFAULT_TOKENS_PER_CALL}
    tokens_table = avg_tokens_per_call or DEFAULT_TOKENS_PER_CALL
    per_agent: dict[str, dict[str, float]] = {}
    total = 0.0
    for agent, n_calls in breakdown.items():
        tok_in, tok_out = tokens_table.get(agent, (0, 0))
        per_call_cost = calculate_cost(model, tok_in, tok_out)
        agent_total = round(per_call_cost * n_calls, 6)
        per_agent[agent] = {
            "calls": n_calls,
            "tokens_in_per_call": tok_in,
            "tokens_out_per_call": tok_out,
            "cost_per_call_usd": round(per_call_cost, 6),
            "total_cost_usd": agent_total,
        }
        total += agent_total
    return {"per_agent": per_agent, "total_cost_usd": round(total, 6)}


def rank_models_by_cost(
    models: Iterable[str],
    query_calls: dict[str, int] | None = None,
) -> list[tuple[str, float]]:
    """Return models sorted by estimated cost per query, ascending."""
    out: list[tuple[str, float]] = []
    for m in models:
        est = estimate_query_cost(m, call_breakdown=query_calls)
        out.append((m, est["total_cost_usd"]))
    return sorted(out, key=lambda x: x[1])


def list_known_models() -> list[str]:
    return sorted(PRICING.keys())
