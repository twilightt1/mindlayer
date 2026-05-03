"""
Integration helpers for the prompt registry.

The agent modules (router_agent.py, answer_agent.py, ...) keep their hardcoded
prompts as the safe default. This module lets you switch to the registry-driven
prompts when the registry has a registered variant for the relevant agent.

Usage from an agent:

    from app.agents.prompts.integration import build_prompt, log_prompt_outcome

    prompt = build_prompt("router", state.get("conversation_id", "default"),
                          query=query, history=history_str)
    # ... call LLM with `prompt` ...
    log_prompt_outcome("router", state.get("conversation_id", "default"),
                       outcome={"source_hit": 1.0, "latency_ms": 420})
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.prompts.registry import PromptRegistry, get_active_variant

# Optional Redis-backed outcome log
_OUTCOME_LOG_PATH = Path(
    os.environ.get("PROMPT_OUTCOME_LOG", "eval/prompt_outcomes.jsonl")
)


def build_prompt(
    agent: str,
    conversation_id: str,
    *,
    force_variant: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Return the rendered prompt for `agent` using the registry.

    Falls back gracefully if the registry has no variant with the required
    placeholders: returns the default variant's template rendered (or, on
    KeyError, returns a stub string). This keeps callers safe even if the
    registry's templates differ from the agent's existing prompts.
    """
    variant = force_variant or get_active_variant(agent, conversation_id)
    pv = PromptRegistry.get(agent, variant)
    try:
        return pv.render(**kwargs)
    except KeyError as missing:
        # Template references a placeholder we don't have. Fall back to a
        # best-effort render that preserves the agent's kwargs the template
        # does reference, and appends the missing fields at the end.
        rendered = pv.template
        for k, v in kwargs.items():
            rendered = rendered.replace("{" + k + "}", str(v))
        rendered += "\n\n# (auto-appended placeholders: " + ", ".join(missing.args) + ")\n"
        return rendered


def log_prompt_outcome(
    agent: str,
    conversation_id: str,
    outcome: Mapping[str, Any],
    log_path: str | Path = _OUTCOME_LOG_PATH,
) -> None:
    """Append a JSON line recording which variant was used + the outcome."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    variant = PromptRegistry.get_assignment(agent, conversation_id) or "default"
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "conversation_id": conversation_id,
        "variant": variant,
        "outcome": dict(outcome),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def aggregate_outcomes(
    log_path: str | Path = _OUTCOME_LOG_PATH,
) -> dict[str, dict[str, dict[str, float]]]:
    """
    Read the outcome log and aggregate by agent -> variant -> metric averages.

    Returns a nested dict like:
        {agent: {variant: {"source_hit": 0.92, "latency_ms": 410, "n": 18}}}
    """
    log_path = Path(log_path)
    if not log_path.exists():
        return {}
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            outcome = rec.get("outcome", {})
            if not isinstance(outcome, dict):
                continue
            by_key.setdefault((rec.get("agent", "?"), rec.get("variant", "?")), []).append(outcome)
    aggregated: dict[str, dict[str, dict[str, float]]] = {}
    for (agent, variant), items in by_key.items():
        aggregated.setdefault(agent, {})[variant] = _avg_dict(items)
    return aggregated


def _avg_dict(items: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for item in items:
        for k, v in item.items():
            try:
                num = float(v)
            except (TypeError, ValueError):
                continue
            sums[k] = sums.get(k, 0.0) + num
            counts[k] = counts.get(k, 0) + 1
    out: dict[str, float] = {}
    for k, total in sums.items():
        out[k] = round(total / counts[k], 4)
    out["n"] = len(list(items)) if isinstance(items, list) else sum(counts.values())  # type: ignore[arg-type]
    return out
