"""Tests for the prompt registry & integration helpers."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.prompts import PROMPT_VERSIONS, PromptRegistry, list_variants
from app.agents.prompts.integration import (
    aggregate_outcomes,
    build_prompt,
    log_prompt_outcome,
)
from app.agents.prompts.registry import PromptNotFoundError, PromptVariant, get_active_variant


# ---------------------------------------------------------------------------
# Variant basics
# ---------------------------------------------------------------------------


class TestPromptVariant:
    def test_render(self) -> None:
        v = PromptVariant(
            name="x", agent="router", template="hello {name}", description=""
        )
        assert v.render(name="world") == "hello world"

    def test_to_from_dict(self) -> None:
        v = PromptVariant(
            name="x", agent="router", template="a {b}", description="d",
            metadata={"k": 1}
        )
        d = v.to_dict()
        v2 = PromptVariant.from_dict(d)
        assert v2.name == v.name
        assert v2.template == v.template
        assert v2.metadata == v.metadata


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestPromptRegistry:
    def test_default_variants_registered(self) -> None:
        # Built-in versions should be registered on import
        for agent in ("router", "answer", "evaluator", "hallucination"):
            variants = PromptRegistry.list_variants(agent)
            assert len(variants) >= 1
            assert all(v.agent == agent for v in variants)

    def test_list_agents(self) -> None:
        agents = PromptRegistry.list_agents()
        assert {"router", "answer", "evaluator", "hallucination"} <= set(agents)

    def test_get_default(self) -> None:
        v = PromptRegistry.get("router")
        assert v.agent == "router"
        assert v.name

    def test_get_specific(self) -> None:
        v = PromptRegistry.get("router", "router_v1")
        assert v.name == "router_v1"

    def test_missing_agent_raises(self) -> None:
        with pytest.raises(PromptNotFoundError):
            PromptRegistry.get("nonexistent_agent")

    def test_missing_variant_raises(self) -> None:
        with pytest.raises(PromptNotFoundError):
            PromptRegistry.get("router", "router_v999")

    def test_register_custom(self) -> None:
        PromptRegistry.register(
            PromptVariant(
                name="custom_test", agent="router", template="custom {x}",
                description="test", metadata={"k": "v"},
            )
        )
        v = PromptRegistry.get("router", "custom_test")
        assert v.metadata == {"k": "v"}

    def test_register_from_file(self, tmp_path: Path) -> None:
        payload = [
            {"name": "x1", "agent": "router", "template": "Hi {q}"},
            {"name": "x2", "agent": "router", "template": "Hello {q}"},
        ]
        path = tmp_path / "prompts.json"
        path.write_text(json.dumps({"variants": payload}), encoding="utf-8")
        n = PromptRegistry.register_from_file(path)
        assert n == 2
        assert PromptRegistry.get("router", "x1").template == "Hi {q}"

    def test_diff(self) -> None:
        d = PromptRegistry.diff("router", "router_v1", "router_v2")
        assert d["agent"] == "router"
        assert d["variants"] == ["router_v1", "router_v2"]
        assert "length_delta_pct" in d


class TestVersions:
    def test_all_agents_have_v1(self) -> None:
        for agent, variants in PROMPT_VERSIONS.items():
            assert any(v.name.endswith("_v1") for v in variants), agent


# ---------------------------------------------------------------------------
# A/B assignment
# ---------------------------------------------------------------------------


class TestAssignment:
    def test_deterministic(self) -> None:
        a = PromptRegistry.assign("router", "conversation-X", variants=["a", "b", "c"])
        b = PromptRegistry.assign("router", "conversation-X", variants=["a", "b", "c"])
        assert a == b

    def test_distribution_reasonable(self) -> None:
        # 300 conversations across 3 variants — each variant should get some
        counts: dict[str, int] = {"a": 0, "b": 0, "c": 0}
        for i in range(300):
            v = PromptRegistry.assign("router", f"c-{i}", variants=list(counts.keys()))
            counts[v] += 1
        # Each should be between 60 and 140 (roughly 100 ± 40)
        for v, c in counts.items():
            assert 60 <= c <= 140, v

    def test_force(self) -> None:
        v = PromptRegistry.assign("router", "conv-Y", force="router_v2")
        assert v == "router_v2"
        assert PromptRegistry.get_assignment("router", "conv-Y") == "router_v2"

    def test_get_active_variant(self) -> None:
        v = get_active_variant("router", "some-conversation")
        assert v in list_variants("router")


# ---------------------------------------------------------------------------
# Integration helpers
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_with_known_placeholders(self) -> None:
        # router_v1 expects {query}
        rendered = build_prompt("router", "conv-1", query="hello", history="(empty)")
        assert "hello" in rendered

    def test_graceful_fallback(self) -> None:
        # Pass a kwarg the template doesn't reference; force the default router_v1
        rendered = build_prompt(
            "router", "conv-2", force_variant="router_v1", query="hi", extra_kwarg="x"
        )
        assert "hi" in rendered


class TestOutcomeLogging:
    def test_log_and_aggregate(self, tmp_path: Path) -> None:
        log = tmp_path / "outcomes.jsonl"
        log_prompt_outcome("router", "c-1", {"source_hit": 1.0, "latency_ms": 400}, log_path=log)
        log_prompt_outcome("router", "c-1", {"source_hit": 0.5, "latency_ms": 500}, log_path=log)
        log_prompt_outcome("router", "c-2", {"source_hit": 0.0, "latency_ms": 200}, log_path=log)
        agg = aggregate_outcomes(log_path=log)
        assert "router" in agg
        # All c-1/c-2 might be same variant; just check aggregates exist
        for variant_data in agg["router"].values():
            assert "n" in variant_data

    def test_empty_log(self, tmp_path: Path) -> None:
        assert aggregate_outcomes(log_path=tmp_path / "missing.jsonl") == {}
