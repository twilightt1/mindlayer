"""Fixture integrity: committed fixtures must parse and match the official schemas."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "eval" / "benchmarks" / "fixtures"


def test_longmemeval_fixture_matches_official_schema():
    records = json.loads((FIXTURES / "longmemeval_s_fixture.json").read_text())
    assert isinstance(records, list) and len(records) >= 2
    for rec in records:
        for field in ("question_id", "question_type", "question", "answer", "question_date",
                      "haystack_session_ids", "haystack_dates", "haystack_sessions", "answer_session_ids"):
            assert field in rec, f"missing {field}"
        assert len(rec["haystack_session_ids"]) == len(rec["haystack_sessions"]) == len(rec["haystack_dates"])
        for session in rec["haystack_sessions"]:
            for turn in session:
                assert turn["role"] in ("user", "assistant")
                assert isinstance(turn["content"], str) and turn["content"]
        assert set(rec["answer_session_ids"]).issubset(set(rec["haystack_session_ids"]))


def test_memoryagentbench_fixture_covers_all_four_competencies():
    records = json.loads((FIXTURES / "memoryagentbench_fixture.json").read_text())
    competencies = {rec["competency"] for rec in records}
    assert competencies == {"accurate_retrieval", "test_time_learning",
                            "long_range_understanding", "selective_forgetting"}
    for rec in records:
        assert rec["phase"] in ("ingest", "query")
        assert rec["question"] and rec["answer"]
