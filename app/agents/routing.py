"""Pure routing helpers for the LangGraph chat workflow."""
from __future__ import annotations

from app.agents.state import AgentState

MAX_RETRIES = 3


def route_from_router(state: AgentState) -> str:
    return state.get("query_type") or "rag"


def has_grounding_context(state: AgentState) -> bool:
    return bool(
        state.get("grounding_context_chunks")
        or state.get("reranked_chunks")
        or state.get("personal_memory_chunks")
        or state.get("graph_context_chunks")
    )


def route_after_grade_docs(state: AgentState) -> str:
    if state.get("query_type") != "rag":
        return "answer"

    if not has_grounding_context(state):
        return "answer"

    if state.get("context_relevant", True):
        return "answer"

    # Retrying retrieval is only useful when uploaded document retrieval exists.
    if not state.get("has_documents", False):
        return "answer"

    if state.get("retry_count", 0) < MAX_RETRIES:
        return "retry_retrieval_for_irrelevant_context"

    return "record_irrelevant_context_retry_limit"


def route_after_grade_gen(state: AgentState) -> str:
    if state.get("query_type") != "rag":
        return "save"

    if not has_grounding_context(state):
        return "save"

    is_hallucination = state.get("is_hallucination", False)
    answers_question = state.get("answers_question", True)

    if not is_hallucination and answers_question:
        return "save"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "record_generation_retry_limit"

    if is_hallucination:
        return "retry_answer_for_hallucination"

    return "retry_retrieval_for_unanswered_question"
