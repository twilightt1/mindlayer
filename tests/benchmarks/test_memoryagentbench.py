"""MemoryAgentBench adapter: scenario grouping, forgetting driver, recall check."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.benchmarks.longmemeval_s import BenchmarkInstance, BenchmarkTurn
from eval.benchmarks.memoryagentbench import Scenario, load_instances, run_forgetting_scenario

FIXTURE = Path(__file__).resolve().parents[2] / "eval" / "benchmarks" / "fixtures" / "memoryagentbench_fixture.json"

pytestmark = pytest.mark.eval


def test_load_fixture_returns_one_scenario_per_competency():
    scenarios = load_instances(FIXTURE)
    assert len(scenarios) == 4
    assert all(isinstance(s, Scenario) for s in scenarios)
    assert {s.competency for s in scenarios} == {
        "accurate_retrieval",
        "test_time_learning",
        "long_range_understanding",
        "selective_forgetting",
    }


def test_scenario_history_flattens_sessions_in_order():
    scenarios = load_instances(FIXTURE)
    by_competency = {s.competency: s for s in scenarios}

    # Multi-session record: history = sessions flattened to turns, in order.
    lru = by_competency["long_range_understanding"]
    assert len(lru.history) == 8  # 2 sessions × 4 turns
    assert all(isinstance(t, BenchmarkTurn) for t in lru.history)
    assert lru.history[0].content.startswith("We finally started the kitchen renovation.")
    assert lru.history[4].content.startswith("The cabinets are in!")
    # Synthetic session ids s0, s1... parallel to the record's sessions.
    assert [s.session_id for s in lru.questions[0].sessions] == ["s0", "s1"]

    # Single-session record keeps its turn order too.
    sf = by_competency["selective_forgetting"]
    assert len(sf.history) == 4
    assert sf.history[1].role == "assistant"


def test_scenario_binds_one_benchmark_instance_with_question_fields():
    scenarios = load_instances(FIXTURE)
    by_competency = {s.competency: s for s in scenarios}

    sf = by_competency["selective_forgetting"]
    assert len(sf.questions) == 1
    question = sf.questions[0]
    assert isinstance(question, BenchmarkInstance)
    assert question.question_id == "fixture_sf_0001"
    assert question.question == "What time does my flight to Tokyo depart and from which gate?"
    assert question.answer == "10:45 AM from gate C3"
    # MAB records carry no question type/date: competency fills the type, date stays empty.
    assert question.question_type == "selective_forgetting"
    assert question.question_date == ""
    assert question.answer_session_ids == frozenset({"s0"})

    # Competency passthrough + scenario_id from the record's question_id.
    assert sf.scenario_id == "fixture_sf_0001"
    assert sf.competency == "selective_forgetting"

    ttl = by_competency["test_time_learning"]
    assert ttl.questions[0].question_id == "fixture_ttl_0003"


def test_selective_forgetting_scenario_marks_forget_flagged_turn():
    scenarios = load_instances(FIXTURE)
    by_competency = {s.competency: s for s in scenarios}

    sf = by_competency["selective_forgetting"]
    flagged = [t for t in sf.history if t.forget]
    assert len(flagged) == 1
    assert flagged[0].content == (
        "Just booked my trip! My flight to Tokyo departs at 7:30 AM from gate B12."
    )

    # No other scenario carries a forget-flagged turn.
    for competency, scenario in by_competency.items():
        if competency != "selective_forgetting":
            assert not any(t.forget for t in scenario.history)


def test_load_instances_raises_value_error_on_missing_field(tmp_path):
    records = json.loads(FIXTURE.read_text())
    del records[0]["question"]
    broken = tmp_path / "missing_field.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="missing field 'question'"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_bad_competency(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["competency"] = "not_a_competency"
    broken = tmp_path / "bad_competency.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="competency"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_bad_phase(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["phase"] = "chatty"
    broken = tmp_path / "bad_phase.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="phase"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_bad_role(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["sessions"][0][0]["role"] = "system"
    broken = tmp_path / "bad_role.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="role must be 'user' or 'assistant'"):
        load_instances(broken)


def test_load_instances_raises_value_error_on_unknown_answer_session_id(tmp_path):
    records = json.loads(FIXTURE.read_text())
    records[0]["answer_session_ids"] = ["s9"]
    broken = tmp_path / "unknown_answer_session.json"
    broken.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="answer_session_ids not in session ids"):
        load_instances(broken)


async def test_run_forgetting_scenario_drives_ingest_forget_recall():
    scenarios = load_instances(FIXTURE)
    sf = next(s for s in scenarios if s.competency == "selective_forgetting")

    ingested: list[str] = []
    forgotten: list[str] = []
    recalled: list[str] = []

    async def ingest_turn(content: str) -> None:
        ingested.append(content)

    async def forget(content: str) -> None:
        forgotten.append(content)

    async def recall(question: str) -> str:
        recalled.append(question)
        # Good hygiene: the old 7:30 AM / gate B12 fact is gone; the updated fact survives.
        return "Your flight now departs at 10:45 AM from gate C3."

    result = await run_forgetting_scenario(sf, ingest_turn=ingest_turn, forget=forget, recall=recall)

    # Ingest: every history turn, in order, exactly once.
    assert len(ingested) == len(sf.history)
    assert ingested == [t.content for t in sf.history]

    # Forget: exactly once, with the flagged turn's content.
    assert len(forgotten) == 1
    assert forgotten[0] == (
        "Just booked my trip! My flight to Tokyo departs at 7:30 AM from gate B12."
    )

    # Recall: once per question, passing the question text.
    assert recalled == ["What time does my flight to Tokyo depart and from which gate?"]

    # Returned dict shape; the expected (surviving, updated) answer was still recalled.
    assert result == {
        "scenario_id": "fixture_sf_0001",
        "competency": "selective_forgetting",
        "questions": [{"question_id": "fixture_sf_0001", "recalled_after_forget": True}],
    }


async def test_run_forgetting_scenario_false_when_stale_fact_replaces_the_answer():
    scenarios = load_instances(FIXTURE)
    sf = next(s for s in scenarios if s.competency == "selective_forgetting")

    async def ingest_turn(content: str) -> None:
        return None

    async def forget(content: str) -> None:
        return None

    async def recall(question: str) -> str:
        # Bad hygiene: the "forgotten" old fact dominates the response instead of the answer.
        return "Your flight departs at 7:30 AM from gate B12."

    result = await run_forgetting_scenario(sf, ingest_turn=ingest_turn, forget=forget, recall=recall)

    # The expected (updated) answer text does not appear in the response.
    assert result["questions"][0]["recalled_after_forget"] is False


async def test_run_forgetting_scenario_recall_match_is_case_and_whitespace_insensitive():
    scenarios = load_instances(FIXTURE)
    sf = next(s for s in scenarios if s.competency == "selective_forgetting")

    async def ingest_turn(content: str) -> None:
        return None

    async def forget(content: str) -> None:
        return None

    async def recall(question: str) -> str:
        return "  it   departs 10:45 am  from gate c3, nice and late. "

    result = await run_forgetting_scenario(sf, ingest_turn=ingest_turn, forget=forget, recall=recall)

    assert result["questions"][0]["recalled_after_forget"] is True


async def test_run_forgetting_scenario_without_forget_flag_never_calls_forget():
    scenarios = load_instances(FIXTURE)
    ar = next(s for s in scenarios if s.competency == "accurate_retrieval")

    forgotten: list[str] = []

    async def ingest_turn(content: str) -> None:
        return None

    async def forget(content: str) -> None:
        forgotten.append(content)

    async def recall(question: str) -> str:
        return "It's in the black notebook on my desk."

    result = await run_forgetting_scenario(ar, ingest_turn=ingest_turn, forget=forget, recall=recall)

    assert forgotten == []
    assert result == {
        "scenario_id": "fixture_ar_0002",
        "competency": "accurate_retrieval",
        "questions": [{"question_id": "fixture_ar_0002", "recalled_after_forget": True}],
    }
