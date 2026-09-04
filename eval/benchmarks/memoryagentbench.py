"""MemoryAgentBench adapter stub: scenario loader + selective-forgetting driver.

v0 harness covers the selective-forgetting scenario against the committed
fixture (one self-contained record per competency — see the README's pinned
grouping contract). Real MemoryAgentBench data is a pinned follow-up; until a
real run happens, no score from this adapter ships anywhere.
"""
from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from eval.benchmarks.longmemeval_s import (
    BenchmarkInstance,
    BenchmarkSession,
    BenchmarkTurn,
)

_COMPETENCIES = frozenset(
    {
        "accurate_retrieval",
        "test_time_learning",
        "long_range_understanding",
        "selective_forgetting",
    }
)
_PHASES = frozenset({"ingest", "query"})


@dataclass(frozen=True)
class ScenarioTurn(BenchmarkTurn):
    """BenchmarkTurn extended with MemoryAgentBench's ``forget`` flag."""

    forget: bool = False


@dataclass(frozen=True)
class Scenario:
    """One self-contained MemoryAgentBench scenario: its own ingest turns + its own question."""

    scenario_id: str
    competency: str
    history: tuple[BenchmarkTurn, ...]
    questions: tuple[BenchmarkInstance, ...]


def _require(obj: dict, field: str, ctx: str) -> object:
    if field not in obj:
        raise ValueError(f"{ctx}: missing field {field!r}")
    return obj[field]


def _require_str(obj: dict, field: str, ctx: str) -> str:
    value = _require(obj, field, ctx)
    if not isinstance(value, str):
        raise ValueError(f"{ctx}: field {field!r} must be a string, got {type(value).__name__}")
    return value


def _parse_sessions(raw_sessions: object, ctx: str) -> tuple[BenchmarkSession, ...]:
    if not isinstance(raw_sessions, list):
        raise ValueError(f"{ctx}: sessions must be a list of sessions")
    sessions: list[BenchmarkSession] = []
    for i, raw_turns in enumerate(raw_sessions):
        session_ctx = f"{ctx} session {i}"
        if not isinstance(raw_turns, list):
            raise ValueError(f"{session_ctx}: session must be a list of turns")
        turns: list[BenchmarkTurn] = []
        for j, turn in enumerate(raw_turns):
            turn_ctx = f"{session_ctx} turn {j}"
            if not isinstance(turn, dict):
                raise ValueError(f"{turn_ctx}: turn must be an object")
            role = _require_str(turn, "role", turn_ctx)
            if role not in ("user", "assistant"):
                raise ValueError(f"{turn_ctx}: role must be 'user' or 'assistant', got {role!r}")
            turns.append(
                ScenarioTurn(
                    role=role,
                    content=_require_str(turn, "content", turn_ctx),
                    has_answer=bool(turn.get("has_answer", False)),
                    forget=bool(turn.get("forget", False)),
                )
            )
        # MemoryAgentBench sessions are unnamed — synthetic ids s0, s1, ... parallel the list.
        sessions.append(BenchmarkSession(session_id=f"s{i}", date="", turns=tuple(turns)))
    return tuple(sessions)


def load_instances(path: Path) -> list[Scenario]:
    """Load a MemoryAgentBench fixture into one Scenario per record.

    Per the pinned grouping contract, each record is self-contained: its own
    sessions flatten (in order) into the scenario's history, and its
    question/answer pair becomes a single BenchmarkInstance bound to it. MAB
    records carry no question type or date, so the competency fills
    ``question_type`` and ``question_date`` stays empty. Raises ``ValueError``
    on any malformed record — never returns a half-loaded list.
    """
    records = json.loads(Path(path).read_text())
    if not isinstance(records, list):
        raise ValueError(f"{path}: top-level JSON must be an array of records, got {type(records).__name__}")

    scenarios: list[Scenario] = []
    for idx, record in enumerate(records):
        ctx = f"{path} record {idx}"
        if not isinstance(record, dict):
            raise ValueError(f"{ctx}: record must be an object")

        question_id = _require_str(record, "question_id", ctx)
        competency = _require_str(record, "competency", ctx)
        if competency not in _COMPETENCIES:
            raise ValueError(f"{ctx}: competency must be one of {sorted(_COMPETENCIES)}, got {competency!r}")
        phase = _require_str(record, "phase", ctx)
        if phase not in _PHASES:
            raise ValueError(f"{ctx}: phase must be one of {sorted(_PHASES)}, got {phase!r}")

        sessions = _parse_sessions(_require(record, "sessions", ctx), ctx)

        answer_session_ids = _require(record, "answer_session_ids", ctx)
        if not isinstance(answer_session_ids, list):
            raise ValueError(f"{ctx}: answer_session_ids must be a list")
        known = {session.session_id for session in sessions}
        unknown = set(answer_session_ids) - known
        if unknown:
            raise ValueError(f"{ctx}: answer_session_ids not in session ids {sorted(known)}: {sorted(unknown)}")

        history = tuple(turn for session in sessions for turn in session.turns)
        scenarios.append(
            Scenario(
                scenario_id=question_id,
                competency=competency,
                history=history,
                questions=(
                    BenchmarkInstance(
                        question_id=question_id,
                        question_type=competency,
                        question=_require_str(record, "question", ctx),
                        answer=_require_str(record, "answer", ctx),
                        question_date="",
                        sessions=sessions,
                        answer_session_ids=frozenset(answer_session_ids),
                    ),
                ),
            )
        )
    return scenarios


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _answer_recalled(answer: str, response: str) -> bool:
    """Case-insensitive, whitespace-normalized word-boundary match of the answer in the response."""
    gold = _normalize(answer)
    if not gold:
        return False
    return re.search(rf"(?<!\w){re.escape(gold)}(?!\w)", _normalize(response)) is not None


async def run_forgetting_scenario(
    scenario: Scenario,
    *,
    ingest_turn: Callable[[str], Awaitable[None]],
    forget: Callable[[str], Awaitable[None]],
    recall: Callable[[str], Awaitable[str]],
) -> dict:
    """Drive one scenario: ingest every history turn, forget the flagged fact(s), then recall.

    Every history turn is ingested in order; then ``forget`` is called exactly
    once per turn flagged ``forget: true`` (with the turn's content — Orivory's
    ``forget_memory`` path); then each question is asked via ``recall``.
    ``recalled_after_forget`` reports whether the question's expected answer
    still appears in the post-forget recall response (case-insensitive,
    whitespace-normalized word-boundary match). For the fixture's
    selective-forgetting record the expected answer is the surviving updated
    fact, so False means forgetting caused collateral damage; scenarios whose
    answer is the forgotten fact itself invert that reading — the runner
    interprets per competency.
    """
    for turn in scenario.history:
        await ingest_turn(turn.content)
    for turn in scenario.history:
        if isinstance(turn, ScenarioTurn) and turn.forget:
            await forget(turn.content)

    questions = []
    for instance in scenario.questions:
        response = await recall(instance.question)
        questions.append(
            {
                "question_id": instance.question_id,
                "recalled_after_forget": _answer_recalled(instance.answer, response),
            }
        )
    return {
        "scenario_id": scenario.scenario_id,
        "competency": scenario.competency,
        "questions": questions,
    }
