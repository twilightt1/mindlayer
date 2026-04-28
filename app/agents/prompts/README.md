# Prompt Management & A/B Testing — Quick Reference

## What this package adds

- **Versioned prompts** for `router`, `answer`, `evaluator`, `hallucination` agents
- **Deterministic A/B assignment** by `conversation_id` (no per-user skew)
- **Optional Redis persistence** for assignments (falls back to in-memory)
- **Outcome logging** to a JSONL file (one record per agent call)
- **Aggregation** of outcomes by agent + variant

## Built-in variants

| Agent          | Variants                              |
|----------------|---------------------------------------|
| router         | `router_v1` (default), `router_v2`    |
| answer         | `answer_v1` (default), `answer_v2`    |
| evaluator      | `evaluator_v1` (default), `evaluator_v2` |
| hallucination  | `hallucination_v1` (default), `hallucination_v2` |

## Quick start

```python
from app.agents.prompts import PromptRegistry, get_active_variant
from app.agents.prompts.integration import build_prompt, log_prompt_outcome

# Pick a variant for this conversation
variant = get_active_variant("router", conversation_id="abc-123")
# Or force a specific variant
PromptRegistry.assign("router", "abc-123", force="router_v2")

# Render the prompt
prompt = build_prompt("router", "abc-123", query="...", history="...")

# Run the LLM, then log the outcome for analysis
log_prompt_outcome("router", "abc-123", {"source_hit": 1.0, "latency_ms": 420})
```

## Inspect the registry

```python
from app.agents.prompts import PromptRegistry, list_variants
print(list_variants("router"))   # ['router_v1', 'router_v2']
print(PromptRegistry.diff("router", "router_v1", "router_v2"))
```

## Aggregate outcomes

```python
from app.agents.prompts.integration import aggregate_outcomes
print(aggregate_outcomes())
# {'router': {'router_v1': {'source_hit': 0.91, 'n': 18},
#             'router_v2': {'source_hit': 0.94, 'n': 17}}}
```

## Add a new variant

```python
from app.agents.prompts.registry import PromptRegistry, PromptVariant

PromptRegistry.register(PromptVariant(
    name="router_v3",
    agent="router",
    template="Your new router prompt here. {query}",
    description="A/B test candidate: tighter JSON schema",
    metadata={"experiment": "schema-v3"},
))
```

Or add it to `versions.py` and re-import.

## CLI

```bash
# Compare two variants in the offline evaluator
python scripts/eval_experiments.py --experiment router_test --variants router_v1,router_v2
```

## Migration strategy (agents still use hardcoded prompts)

The agents still have their original hardcoded prompts as the default. To migrate
a single agent to the registry:

1. In the agent, replace the hardcoded prompt with:
   ```python
   from app.agents.prompts.integration import build_prompt
   prompt = build_prompt("router", state.get("conversation_id", "default"),
                         query=query, history=history_str)
   ```
2. Run `python -m pytest tests/rag tests/eval` — the agent's existing tests
   should pass because `build_prompt` falls back gracefully if placeholders
   don't match.
3. Verify in production with `agent_trace` showing `prompt_variant: router_v1`.
4. Once stable, remove the hardcoded constant.
