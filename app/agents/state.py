from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_id: str
    conversation_id: str
    query: str
    rewritten_query: str

    query_type: str
    router_confidence: float
    router_reasoning: str
    search_variants: list[str]

    history: list[dict[str, Any]]

    bm25_results: list[dict[str, Any]]
    vector_results: list[dict[str, Any]]
    fused_chunks: list[dict[str, Any]]

    reranked_chunks: list[dict[str, Any]]

    response: str
    token_count: int
    agent_trace: dict[str, Any]

    error: str | None
    should_stream: bool
    has_documents: bool
    document_count: int

    context_relevant: bool
    is_hallucination: bool
    answers_question: bool
    retry_count: int

    # AI/ML observability (cost & latency tracking)
    cumulative_cost_usd: float
    total_tokens_in: int
    total_tokens_out: int
    agent_costs: dict[str, float]
    agent_latency_ms: dict[str, float]
