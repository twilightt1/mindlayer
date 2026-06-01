from app.agents.graph import (
    MAX_RETRIES,
    _record_generation_retry_limit,
    _record_irrelevant_context_retry_limit,
    _retry_answer_for_hallucination,
    _retry_retrieval_for_irrelevant_context,
    _retry_retrieval_for_unanswered_question,
    _route_after_grade_docs,
    _route_after_grade_gen,
)

import pytest

pytestmark = pytest.mark.rag


def test_grade_docs_routes_relevant_context_to_answer():
    state = {
        "query_type": "rag",
        "has_documents": True,
        "context_relevant": True,
        "retry_count": 0,
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_docs(state) == "answer"


def test_grade_docs_routes_irrelevant_context_to_retrieval_retry_node():
    state = {
        "query_type": "rag",
        "has_documents": True,
        "context_relevant": False,
        "retry_count": 0,
        "agent_trace": {},
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_docs(state) == "retry_retrieval_for_irrelevant_context"

    updated = _retry_retrieval_for_irrelevant_context(state)

    assert updated["retry_count"] == 1
    assert updated["agent_trace"]["correction"] == [
        {
            "reason": "irrelevant_context",
            "next_node": "retrieval",
            "retry_count": 1,
        }
    ]


def test_grade_docs_records_retry_limit_before_answering():
    state = {
        "query_type": "rag",
        "has_documents": True,
        "context_relevant": False,
        "retry_count": MAX_RETRIES,
        "agent_trace": {},
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_docs(state) == "record_irrelevant_context_retry_limit"

    updated = _record_irrelevant_context_retry_limit(state)

    assert updated["agent_trace"]["correction"] == [
        {
            "reason": "irrelevant_context_retry_limit",
            "next_node": "answer",
            "retry_count": MAX_RETRIES,
        }
    ]


def test_grade_gen_routes_valid_generation_to_save():
    state = {
        "query_type": "rag",
        "is_hallucination": False,
        "answers_question": True,
        "retry_count": 0,
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_gen(state) == "save"


def test_grade_gen_retries_answer_for_hallucination():
    state = {
        "query_type": "rag",
        "is_hallucination": True,
        "answers_question": True,
        "retry_count": 0,
        "agent_trace": {},
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_gen(state) == "retry_answer_for_hallucination"

    updated = _retry_answer_for_hallucination(state)

    assert updated["retry_count"] == 1
    assert updated["agent_trace"]["correction"] == [
        {
            "reason": "hallucination_detected",
            "next_node": "answer",
            "retry_count": 1,
        }
    ]


def test_grade_gen_retries_retrieval_when_answer_does_not_resolve_question():
    state = {
        "query_type": "rag",
        "is_hallucination": False,
        "answers_question": False,
        "retry_count": 0,
        "agent_trace": {},
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_gen(state) == "retry_retrieval_for_unanswered_question"

    updated = _retry_retrieval_for_unanswered_question(state)

    assert updated["retry_count"] == 1
    assert updated["agent_trace"]["correction"] == [
        {
            "reason": "answer_did_not_resolve_question",
            "next_node": "retrieval",
            "retry_count": 1,
        }
    ]


def test_grade_gen_records_generation_retry_limit_before_save():
    state = {
        "query_type": "rag",
        "is_hallucination": True,
        "answers_question": False,
        "retry_count": MAX_RETRIES,
        "agent_trace": {},
        "grounding_context_chunks": [{"id": "x", "content": "ctx"}],
    }

    assert _route_after_grade_gen(state) == "record_generation_retry_limit"

    updated = _record_generation_retry_limit(state)

    assert updated["agent_trace"]["correction"] == [
        {
            "reason": "generation_retry_limit",
            "next_node": "save",
            "retry_count": MAX_RETRIES,
        }
    ]


def test_chitchat_generation_skips_self_correction():
    state = {
        "query_type": "chitchat",
        "is_hallucination": True,
        "answers_question": False,
        "retry_count": 0,
    }

    assert _route_after_grade_docs(state) == "answer"
    assert _route_after_grade_gen(state) == "save"
