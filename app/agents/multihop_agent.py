"""
Multi-hop Reasoning Agent for Orivory v2.0

Implements EfficientRAG pattern from EMNLP 2024:
- Detects multi-hop queries
- Decomposes into subqueries
- Recursive retrieval across hops
- Branch-solve-merge aggregation

Reference: EfficientRAG - EMNLP 2024
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from app.config import settings

if TYPE_CHECKING:
    from app.agents.state import AgentState

log = logging.getLogger(__name__)

# ─── LLM Client ───────────────────────────────────────────────────────────────

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
    return _client


# ─── Prompts ─────────────────────────────────────────────────────────────────

HOP_DETECTION_PROMPT = """You are a query analyzer for a research assistant.

Analyze the query to determine if it requires multi-hop reasoning.

A multi-hop query requires connecting information from multiple sources:
- "What is the relationship between X and Y?" (requires understanding X and Y separately)
- "Why did X happen based on Y?" (causal chain)
- "How does A affect B?" (dependency chain)
- "Compare X and Y" (parallel reasoning)
- "What caused X to change Y?" (cause-effect)

A single-hop query can be answered directly from one document:
- "What is X?"
- "When did Y happen?"
- "How many..."

Query: {query}

Respond with JSON:
{{
    "is_multihop": true/false,
    "hop_count": 1-3,
    "reasoning": "brief explanation",
    "key_entities": ["entity1", "entity2"],
    "relationship_type": "comparison|causal|dependency|other|none"
}}"""

SUBQUERY_GENERATION_PROMPT = """Given this multi-hop query, generate subqueries to retrieve information for each hop.

Original query: {query}

Context from previous hops:
{context}

Generate {hop_count} subquery(s). Each subquery should:
- Be specific enough to retrieve relevant documents
- Build on information from previous hops
- Use technical terms when possible

Respond with JSON:
{{
    "subqueries": [
        {{"hop": 1, "query": "subquery for hop 1", "purpose": "what to find"}},
        {{"hop": 2, "query": "subquery for hop 2", "purpose": "what to find"}}
    ]
}}"""

ANSWER_SYNTHESIS_PROMPT = """Synthesize an answer from multi-hop reasoning results.

Original query: {query}

Reasoning chain:
{reasoning_chain}

Synthesize a comprehensive answer that:
1. Addresses the original query
2. Shows the reasoning chain
3. Cites sources from retrieved documents
4. Notes any uncertainties or gaps

Provide the synthesized answer."""


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class HopResult:
    """Result from a single reasoning hop."""
    hop_number: int
    subquery: str
    retrieved_context: str
    answer_fragment: str
    confidence: float


@dataclass
class MultiHopResult:
    """Result from multi-hop reasoning."""
    is_multihop: bool
    hop_count: int
    hop_results: list[HopResult]
    synthesized_answer: str
    confidence: float
    reasoning_chain: str


# ─── Multi-hop Functions ──────────────────────────────────────────────────────

async def detect_multihop(query: str) -> dict:
    """
    Detect if query requires multi-hop reasoning.

    Args:
        query: The user's query

    Returns:
        Dict with is_multihop, hop_count, reasoning, etc.
    """
    import json

    client = _get_client()
    prompt = HOP_DETECTION_PROMPT.format(query=query)

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=300,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "is_multihop": result.get("is_multihop", False),
            "hop_count": min(result.get("hop_count", 1), settings.MULTIHOP_MAX_HOPS),
            "reasoning": result.get("reasoning", ""),
            "key_entities": result.get("key_entities", []),
            "relationship_type": result.get("relationship_type", "none"),
        }

    except Exception as e:
        log.warning(f"Multi-hop detection failed: {e}")
        return {
            "is_multihop": False,
            "hop_count": 1,
            "reasoning": f"Detection failed: {str(e)[:50]}",
            "key_entities": [],
            "relationship_type": "none",
        }


async def generate_subqueries(
    query: str,
    hop_count: int,
    context: str = "",
) -> list[dict]:
    """
    Generate subqueries for multi-hop reasoning.

    Args:
        query: Original query
        hop_count: Number of hops needed
        context: Context from previous hops

    Returns:
        List of subquery dicts with hop, query, purpose
    """
    import json

    client = _get_client()
    prompt = SUBQUERY_GENERATION_PROMPT.format(
        query=query,
        context=context or "No previous context",
        hop_count=hop_count,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        subqueries = result.get("subqueries", [])

        # Ensure we have the right number of subqueries
        while len(subqueries) < hop_count:
            subqueries.append({
                "hop": len(subqueries) + 1,
                "query": query,
                "purpose": "additional retrieval",
            })

        return subqueries[:hop_count]

    except Exception as e:
        log.warning(f"Subquery generation failed: {e}")
        # Fallback: use original query for all hops
        return [
            {"hop": i + 1, "query": query, "purpose": "retrieval"}
            for i in range(hop_count)
        ]


async def synthesize_answer(
    query: str,
    hop_results: list[HopResult],
) -> tuple[str, float]:
    """
    Synthesize final answer from multi-hop results.

    Args:
        query: Original query
        hop_results: Results from each hop

    Returns:
        Tuple of (synthesized_answer, confidence)
    """
    client = _get_client()

    # Build reasoning chain
    reasoning_chain = "\n\n".join([
        f"Hop {r.hop_number}: {r.subquery}\n"
        f"  Context: {r.retrieved_context[:200]}...\n"
        f"  Finding: {r.answer_fragment}"
        for r in hop_results
    ])

    prompt = ANSWER_SYNTHESIS_PROMPT.format(
        query=query,
        reasoning_chain=reasoning_chain,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content.strip()

        # Calculate confidence as average of hop confidences
        avg_confidence = sum(r.confidence for r in hop_results) / len(hop_results) if hop_results else 0.5

        return answer, avg_confidence

    except Exception as e:
        log.warning(f"Answer synthesis failed: {e}")
        return f"Could not synthesize multi-hop answer: {str(e)[:100]}", 0.3


# ─── Multi-hop Agent Node ─────────────────────────────────────────────────────

async def multihop_agent(state: AgentState) -> AgentState:
    """
    Multi-hop reasoning agent node for LangGraph workflow.

    This node:
    1. Detects if query requires multi-hop reasoning
    2. Generates subqueries for each hop
    3. Triggers recursive retrieval
    4. Synthesizes final answer

    Args:
        state: Current agent state

    Returns:
        Updated agent state with multi-hop results
    """
    state.setdefault("agent_trace", {})
    state.setdefault("multihop_trace", {})

    # Check if multi-hop is enabled
    if not settings.MULTIHOP_ENABLED:
        log.debug("Multi-hop disabled, skipping")
        state["multihop_trace"]["enabled"] = False
        state["multihop_result"] = None
        return state

    query = state.get("rewritten_query", state.get("query", ""))
    query_type = state.get("query_type", "")

    # Skip for non-RAG queries
    if query_type in ("chitchat", "save_note"):
        state["multihop_trace"]["skipped"] = True
        state["multihop_result"] = None
        return state

    # Step 1: Detect if multi-hop
    log.info(f"Multi-hop: Analyzing query: {query[:50]}...")

    detection = await detect_multihop(query)

    state["multihop_trace"]["detection"] = detection

    if not detection.get("is_multihop"):
        log.info("Multi-hop: Single-hop query detected")
        state["multihop_trace"]["mode"] = "single_hop"
        state["multihop_result"] = None
        return state

    hop_count = detection.get("hop_count", 1)
    log.info(f"Multi-hop: Detected {hop_count}-hop query")

    state["multihop_trace"]["mode"] = "multi_hop"
    state["multihop_trace"]["hop_count"] = hop_count

    # Step 2: Generate subqueries
    subqueries = await generate_subqueries(
        query=query,
        hop_count=hop_count,
        context="",  # Will be updated with each hop
    )

    state["multihop_trace"]["subqueries"] = [
        {"hop": sq["hop"], "query": sq["query"], "purpose": sq.get("purpose", "")}
        for sq in subqueries
    ]

    # Step 3: Execute hops (simplified - actual retrieval happens in retrieval_agent)
    # Store subqueries in state for retrieval agent to use
    state["multihop_subqueries"] = subqueries

    # Step 4: Flag for answer synthesis after retrieval
    state["multihop_pending"] = True
    state["multihop_hop_results"] = []

    return state


async def multihop_synthesis(state: AgentState) -> AgentState:
    """
    Synthesize answer after multi-hop retrieval.

    Called after retrieval completes to synthesize the final answer.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with synthesized answer
    """
    if not state.get("multihop_pending"):
        return state

    query = state.get("rewritten_query", state.get("query", ""))
    hop_results = state.get("multihop_hop_results", [])

    if not hop_results:
        log.warning("Multi-hop: No hop results to synthesize")
        state["multihop_result"] = None
        return state

    # Synthesize answer
    answer, confidence = await synthesize_answer(query, hop_results)

    state["multihop_result"] = {
        "answer": answer,
        "confidence": confidence,
        "hop_count": len(hop_results),
        "reasoning_chain": "\n".join([
            f"Hop {r.hop_number}: {r.answer_fragment}"
            for r in hop_results
        ]),
    }

    state["multihop_pending"] = False

    log.info(f"Multi-hop: Synthesized answer with confidence {confidence:.2f}")

    return state


# ─── Branch-Solve-Merge Helper ─────────────────────────────────────────────────

async def branch_solve_merge(
    query: str,
    branches: list[str],
    retrieved_contexts: list[str],
) -> str:
    """
    Process multiple branches and merge results.

    Used for parallel reasoning paths that need to be merged.

    Args:
        query: Original query
        branches: List of branch topics
        retrieved_contexts: Retrieved context for each branch

    Returns:
        Merged analysis
    """
    client = _get_client()

    branch_text = "\n\n".join([
        f"Branch {i+1} ({branches[i]}):\n{retrieved_contexts[i]}"
        for i in range(len(branches))
    ])

    prompt = f"""Analyze multiple reasoning branches and synthesize findings.

Query: {query}

Branches analyzed:
{branch_text}

Provide a synthesized analysis that:
1. Integrates findings from all branches
2. Resolves any conflicts between branches
3. Provides a coherent answer to the original query
"""

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        log.warning(f"Branch-solve-merge failed: {e}")
        return f"Branch merge failed: {str(e)[:100]}"
