"""LongMemEval-S adapter: typed loader, injected ingest/recall, exact-match judge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.benchmarks.longmemeval_s import (
    BenchmarkInstance,
    BenchmarkSession,
    BenchmarkTurn,
    ingest_history,
    is_abstention,
    judge_answer,
    load_instances,
    run_query,
)

FIXTURE = Path(__file__).resolve().parents[2] / "eval" / "benchmarks" / "fixtures" / "longmemeval_s_fixture.json"

pytestmark = pytest.mark.eval


def test_load_fixture_returns_two_typed_instances():
    instances = load_instances(FIXTURE)
    assert len(instances) == 2
    first = instances[0]
    assert isinstance(first, BenchmarkInstance)
    assert first.question_id == "fixture_0001"
    assert first.question_type == "temporal-reasoning"
    assert first.answer == "Runkeeper"
    assert first.question_date == "2026-08-20"
    assert isinstance(first.sessions, tuple) and len(first.sessions) == 3
    assert first.answer_session_ids == frozenset({"s_2026_06_14"})


def test_sessions_and_turns_are_frozen_dataclasses():
    instances = load_instances(FIXTURE)
    first = instances[0]
    assert isinstance(first.sessions, tuple)
    session = first.sessions[1]
    assert isinstance(session, BenchmarkSession)
    assert session.session_id == "s_2026_06_14"
    assert session.date == "2026-06-14"
    assert isinstance(session.turns, tuple) and len(session.turns) == 4
    evidence_turn = session.turns[2]
    assert isinstance(evidence_turn, BenchmarkTurn)
    assert evidence_turn.role == "user"
    assert evidence_turn.content.startswith("About 5k every other day.")
    assert evidence_turn.has_answer is True
    assert session.turns[0].has_answer is False
    assert isinstance(first.answer_session_ids, frozenset)


def test_is_abstention_marks_only_abs_suffix_ids():
    instances = load_instances(FIXTURE)
    assert is_abstention(instances[0]) is False
    assert is_abstention(instances[1]) is True


def test_load_instances_raises_value_error_on_broken_parallel_arrays(tmp_path):
    records = json.loads(FIXTURE.read_text())
    del records[0]["haystack_dates"]
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="haystack_dates"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_unequal_array_lengths(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["haystack_dates"].pop()
    broken = tmp_path / "unequal.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="parallel haystack arrays"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_missing_field(tmp_path):
    records = json.loads(FIXTURE.read_text())
    del records[0]["question"]
    broken = tmp_path / "missing_field.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="missing field 'question'"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_bad_role(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["haystack_sessions"][0][0]["role"] = "system"
    broken = tmp_path / "bad_role.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="role must be 'user' or 'assistant'"):
        load_instances(broken)


async def test_ingest_history_calls_create_memory_once_per_turn_with_prefix_and_date():
    instances = load_instances(FIXTURE)
    session = instances[0].sessions[0]

    calls: list[tuple[str, str]] = []

    async def collector(content: str, source: str) -> None:
        calls.append((content, source))

    await ingest_history(session, create_memory=collector)

    assert len(calls) == len(session.turns)
    first_content, first_source = calls[0]
    assert first_content == (
        "[user] 2026-05-02\nI finally set up my apartment in Oakland. The moving boxes are finally gone."
    )
    assert first_source == "s_2026_05_02"
    assert calls[1][0].startswith("[assistant] 2026-05-02\n")
    assert calls[2][0].startswith("[user] 2026-05-02\n")
    assert calls[3][0].startswith("[assistant] 2026-05-02\n")


async def test_ingest_history_caps_turn_content_at_10k_chars():
    instances = load_instances(FIXTURE)
    session = instances[0].sessions[0]
    long_turn = BenchmarkTurn(role="user", content="x" * 25_000, has_answer=False)
    long_session = BenchmarkSession(
        session_id=session.session_id, date=session.date, turns=(long_turn,)
    )

    calls: list[str] = []

    async def collector(content: str, source: str) -> None:
        calls.append(content)

    await ingest_history(long_session, create_memory=collector)

    assert len(calls) == 1
    assert len(calls[0]) == len("[user] 2026-05-02\n") + 10_000
    assert calls[0].startswith("[user] 2026-05-02\n")
    assert calls[0].endswith("x" * 10_000)


async def test_run_query_returns_recall_answer_for_the_question():
    instances = load_instances(FIXTURE)
    instance = instances[0]

    async def recall(question: str) -> str:
        assert question == "Which app did I use to track my runs before I switched to Strava?"
        return "runkeeper"

    assert await run_query(instance, recall=recall) == "runkeeper"


def test_judge_answer_exact_match_on_short_numeric_gold():
    assert judge_answer(
        "How many runs did I log last week?",
        "3",
        "You logged 3 runs last week.",
    ) is True
    assert judge_answer("How old is my bike?", "26", "26") is True


def test_judge_answer_false_on_wrong_answer_or_nonnumeric_gold():
    assert judge_answer(
        "How many runs did I log last week?",
        "3",
        "You logged 5 runs last week.",
    ) is False
    # Prose gold answers are outside the non-LLM subset — must not pass the guard.
    assert judge_answer(
        "Which app did I use to track my runs before I switched to Strava?",
        "Runkeeper",
        "Runkeeper",
    ) is False


def test_judge_answer_normalizes_case_and_whitespace():
    assert judge_answer("How many?", "Yes", "  YES  ") is True
    assert judge_answer("How many?", "yes", "well, Yes indeed") is True
    assert judge_answer("How many?", "No", "yes") is False
