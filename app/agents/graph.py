from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph

from app.agents.answer_agent import answer_agent
from app.agents.context_merge_agent import context_merge_agent
from app.agents.evaluator_agent import evaluator_agent
from app.agents.graph_context_agent import graph_context_agent
from app.agents.hallucination_agent import hallucination_agent
from app.agents.memory_agent import memory_load_agent, memory_save_agent
from app.agents.personal_context_agent import personal_context_agent
from app.agents.retrieval_agent import retrieval_agent
from app.agents.router_agent import router_agent
from app.agents.routing import (
    route_after_grade_docs as _route_after_grade_docs,
    route_after_grade_gen as _route_after_grade_gen,
    route_from_router as _route,
)
from app.agents.state import AgentState


def _record_correction(state: AgentState, reason: str, next_node: str) -> None:
    state.setdefault("agent_trace", {})
    corrections = state["agent_trace"].setdefault("correction", [])
    corrections.append(
        {
            "reason": reason,
            "next_node": next_node,
            "retry_count": state.get("retry_count", 0),
        }
    )


def _increment_retry(state: AgentState, reason: str, next_node: str) -> AgentState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    _record_correction(state, reason, next_node)
    return state


def _retry_retrieval_for_irrelevant_context(state: AgentState) -> AgentState:
    return _increment_retry(state, "irrelevant_context", "retrieval")


def _retry_answer_for_hallucination(state: AgentState) -> AgentState:
    return _increment_retry(state, "hallucination_detected", "answer")


def _retry_retrieval_for_unanswered_question(state: AgentState) -> AgentState:
    return _increment_retry(state, "answer_did_not_resolve_question", "retrieval")


def _record_irrelevant_context_retry_limit(state: AgentState) -> AgentState:
    _record_correction(state, "irrelevant_context_retry_limit", "answer")
    return state


def _record_generation_retry_limit(state: AgentState) -> AgentState:
    _record_correction(state, "generation_retry_limit", "save")
    return state


# Route helpers are pure functions in app.agents.routing so they can be tested
# without importing retrieval/vector dependencies required by the full graph.


def build_graph() -> CompiledStateGraph:
    g = StateGraph(AgentState)

    g.add_node("router", router_agent)
    g.add_node("memory", memory_load_agent)
    g.add_node("personal_context", personal_context_agent)
    g.add_node("graph_context", graph_context_agent)
    g.add_node("retrieval", retrieval_agent)
    g.add_node("merge_context", context_merge_agent)
    g.add_node("grade_docs", evaluator_agent)
    g.add_node("retry_retrieval_for_irrelevant_context", _retry_retrieval_for_irrelevant_context)
    g.add_node("retry_answer_for_hallucination", _retry_answer_for_hallucination)
    g.add_node("retry_retrieval_for_unanswered_question", _retry_retrieval_for_unanswered_question)
    g.add_node("record_irrelevant_context_retry_limit", _record_irrelevant_context_retry_limit)
    g.add_node("record_generation_retry_limit", _record_generation_retry_limit)
    g.add_node("answer", answer_agent)
    g.add_node("grade_gen", hallucination_agent)
    g.add_node("save", memory_save_agent)

    g.add_edge(START, "router")

    g.add_conditional_edges(
        "router",
        _route,
        {
            "rag": "memory",
            "summarize": "memory",
            "chitchat": "answer",
        },
    )

    g.add_edge("memory", "personal_context")
    g.add_edge("personal_context", "graph_context")
    g.add_edge("graph_context", "retrieval")
    g.add_edge("retrieval", "merge_context")
    g.add_edge("merge_context", "grade_docs")
    g.add_conditional_edges(
        "grade_docs",
        _route_after_grade_docs,
        {
            "retry_retrieval_for_irrelevant_context": "retry_retrieval_for_irrelevant_context",
            "record_irrelevant_context_retry_limit": "record_irrelevant_context_retry_limit",
            "answer": "answer",
        },
    )
    g.add_edge("retry_retrieval_for_irrelevant_context", "retrieval")
    g.add_edge("record_irrelevant_context_retry_limit", "answer")

    g.add_edge("answer", "grade_gen")
    g.add_conditional_edges(
        "grade_gen",
        _route_after_grade_gen,
        {
            "retry_answer_for_hallucination": "retry_answer_for_hallucination",
            "retry_retrieval_for_unanswered_question": "retry_retrieval_for_unanswered_question",
            "record_generation_retry_limit": "record_generation_retry_limit",
            "save": "save",
        },
    )
    g.add_edge("retry_answer_for_hallucination", "answer")
    g.add_edge("retry_retrieval_for_unanswered_question", "retrieval")
    g.add_edge("record_generation_retry_limit", "save")
    g.add_edge("save", END)

    return g.compile()


rag_graph = build_graph()
