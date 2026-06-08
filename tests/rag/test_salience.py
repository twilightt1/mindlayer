"""P2.1 tests: salience feedback loop (bump + decay)."""
from __future__ import annotations

import pytest

from app.agents.memory_agent import _used_memory_ids
from app.retrieval.memory.salience import DEFAULT_BUMP_STEP, SALIENCE_MAX, next_salience

pytestmark = pytest.mark.rag


class TestNextSalience:
    def test_increments_toward_one(self):
        assert next_salience(0.5) == 0.55
        assert next_salience(0.0) == round(DEFAULT_BUMP_STEP, 6)

    def test_asymptotic_never_exceeds_max(self):
        s = 0.5
        for _ in range(1000):
            s = next_salience(s)
        assert s <= SALIENCE_MAX
        assert s > 0.99  # converges near 1.0

    def test_clamps_out_of_range_input(self):
        assert next_salience(1.5) == SALIENCE_MAX  # clamped down first
        assert next_salience(-1.0) == round(DEFAULT_BUMP_STEP, 6)

    def test_diminishing_returns(self):
        # The increment shrinks as salience rises.
        low_gain = next_salience(0.1) - 0.1
        high_gain = next_salience(0.9) - 0.9
        assert low_gain > high_gain


class TestUsedMemoryIds:
    def test_extracts_unique_memory_ids_from_grounding(self):
        state = {
            "grounding_context_chunks": [
                {"metadata": {"memory_id": "m1"}},
                {"metadata": {"memory_id": "m2"}},
                {"metadata": {"memory_id": "m1"}},  # dup
                {"metadata": {"document_id": "d1"}},  # no memory_id
                {"content": "no metadata"},
            ]
        }
        assert _used_memory_ids(state) == ["m1", "m2"]

    def test_empty_when_no_grounding(self):
        assert _used_memory_ids({}) == []
        assert _used_memory_ids({"grounding_context_chunks": []}) == []
