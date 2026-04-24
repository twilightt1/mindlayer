import pytest

from app.agents import graph

pytestmark = pytest.mark.rag


@pytest.mark.asyncio
async def test_e2e_rag_query_flow(monkeypatch):
    calls: list[str] = []

    async def router(state):
        calls.append("router")
        state.setdefault("agent_trace", {})
        state["query_type"] = "rag"
        state["has_documents"] = True
        state["retry_count"] = 0
        return state

    async def memory_load(state):
        calls.append("memory")
        state["history"] = []
        return state

    async def retrieval(state):
        calls.append("retrieval")
        state["reranked_chunks"] = [
            {
                "content": "Server configuration requires a settings.json file.",
                "metadata": {"filename": "manual.md"},
                "score": 0.9,
                "source": "vector",
            }
        ]
        return state

    async def grade_docs(state):
        calls.append("grade_docs")
        state["context_relevant"] = True
        return state

    async def answer(state):
        calls.append("answer")
        state["response"] = "Server configuration requires a settings.json file [Source 1]."
        return state

    async def grade_gen(state):
        calls.append("grade_gen")
        state["is_hallucination"] = False
        state["answers_question"] = True
        return state

    async def save(state):
        calls.append("save")
        return state

    monkeypatch.setattr(graph, "router_agent", router)
    monkeypatch.setattr(graph, "memory_load_agent", memory_load)
    monkeypatch.setattr(graph, "retrieval_agent", retrieval)
    monkeypatch.setattr(graph, "evaluator_agent", grade_docs)
    monkeypatch.setattr(graph, "answer_agent", answer)
    monkeypatch.setattr(graph, "hallucination_agent", grade_gen)
    monkeypatch.setattr(graph, "memory_save_agent", save)

    test_graph = graph.build_graph()

    result = await test_graph.ainvoke(
        {
            "query": "How do I configure the server?",
            "conversation_id": "test_conv",
            "agent_trace": {},
        }
    )

    assert calls == ["router", "memory", "retrieval", "grade_docs", "answer", "grade_gen", "save"]
    assert result["query_type"] == "rag"
    assert result["reranked_chunks"][0]["metadata"]["filename"] == "manual.md"
    assert result["response"] == "Server configuration requires a settings.json file [Source 1]."


@pytest.mark.asyncio
async def test_e2e_chitchat_flow_skips_memory_and_retrieval(monkeypatch):
    calls: list[str] = []

    async def router(state):
        calls.append("router")
        state["query_type"] = "chitchat"
        state["retry_count"] = 0
        return state

    async def memory_load(state):
        calls.append("memory")
        return state

    async def retrieval(state):
        calls.append("retrieval")
        return state

    async def grade_docs(state):
        calls.append("grade_docs")
        return state

    async def answer(state):
        calls.append("answer")
        state["response"] = "Hi! How can I help you today?"
        return state

    async def grade_gen(state):
        calls.append("grade_gen")
        state["is_hallucination"] = False
        state["answers_question"] = True
        return state

    async def save(state):
        calls.append("save")
        return state

    monkeypatch.setattr(graph, "router_agent", router)
    monkeypatch.setattr(graph, "memory_load_agent", memory_load)
    monkeypatch.setattr(graph, "retrieval_agent", retrieval)
    monkeypatch.setattr(graph, "evaluator_agent", grade_docs)
    monkeypatch.setattr(graph, "answer_agent", answer)
    monkeypatch.setattr(graph, "hallucination_agent", grade_gen)
    monkeypatch.setattr(graph, "memory_save_agent", save)

    test_graph = graph.build_graph()

    result = await test_graph.ainvoke(
        {
            "query": "Hello there!",
            "conversation_id": "test_conv",
            "agent_trace": {},
        }
    )

    assert calls == ["router", "answer", "grade_gen", "save"]
    assert result["query_type"] == "chitchat"
    assert result["response"] == "Hi! How can I help you today?"


@pytest.mark.asyncio
async def test_rag_flow_retries_retrieval_when_context_is_irrelevant(monkeypatch):
    calls: list[str] = []
    grade_attempts = 0

    async def router(state):
        calls.append("router")
        state.setdefault("agent_trace", {})
        state["query_type"] = "rag"
        state["has_documents"] = True
        state["retry_count"] = 0
        return state

    async def memory_load(state):
        calls.append("memory")
        return state

    async def retrieval(state):
        calls.append("retrieval")
        state["reranked_chunks"] = [
            {
                "content": f"Retrieved context attempt {state.get('retry_count', 0)}",
                "metadata": {"filename": "manual.md"},
            }
        ]
        return state

    async def grade_docs(state):
        nonlocal grade_attempts
        calls.append("grade_docs")
        grade_attempts += 1
        state["context_relevant"] = grade_attempts > 1
        return state

    async def answer(state):
        calls.append("answer")
        state["response"] = "Answer after retrieval retry."
        return state

    async def grade_gen(state):
        calls.append("grade_gen")
        state["is_hallucination"] = False
        state["answers_question"] = True
        return state

    async def save(state):
        calls.append("save")
        return state

    monkeypatch.setattr(graph, "router_agent", router)
    monkeypatch.setattr(graph, "memory_load_agent", memory_load)
    monkeypatch.setattr(graph, "retrieval_agent", retrieval)
    monkeypatch.setattr(graph, "evaluator_agent", grade_docs)
    monkeypatch.setattr(graph, "answer_agent", answer)
    monkeypatch.setattr(graph, "hallucination_agent", grade_gen)
    monkeypatch.setattr(graph, "memory_save_agent", save)

    test_graph = graph.build_graph()

    result = await test_graph.ainvoke(
        {
            "query": "How do I configure the server?",
            "conversation_id": "test_conv",
            "agent_trace": {},
        }
    )

    assert calls == [
        "router",
        "memory",
        "retrieval",
        "grade_docs",
        "retrieval",
        "grade_docs",
        "answer",
        "grade_gen",
        "save",
    ]
    assert result["retry_count"] == 1
    assert result["response"] == "Answer after retrieval retry."
    assert result["agent_trace"]["correction"] == [
        {
            "reason": "irrelevant_context",
            "next_node": "retrieval",
            "retry_count": 1,
        }
    ]
