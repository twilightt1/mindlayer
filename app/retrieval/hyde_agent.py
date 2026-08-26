"""
HyDE (Hypothetical Document Embeddings) Agent for Orivory v2.0

Implements the HyDE pattern from Gao et al. (2023):
- Generate hypothetical relevant document from query
- Embed the hypothetical document
- Use embedding to retrieve real documents

Reference: https://arxiv.org/abs/2309.08830
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


# ─── Prompt Templates ─────────────────────────────────────────────────────────

HYDE_GENERATION_PROMPT = """You are a research assistant that generates hypothetical document passages.

Given the user's question, generate 2-3 hypothetical passages that would DIRECTLY answer the question.
These passages should:
- Be factual and informative
- Use appropriate technical terminology
- Be detailed enough to capture the essence of a real document
- Be written in the same style as academic/research documents

Question: {query}

Generate hypothetical passages that would contain the answer. Return as JSON:
{{
    "passages": [
        "Hypothetical passage 1 (2-3 sentences)...",
        "Hypothetical passage 2 (2-3 sentences)...",
        "Hypothetical passage 3 (2-3 sentences)..."
    ],
    "key_concepts": ["concept1", "concept2", "concept3"]
}}"""

HYDE_REFINEMENT_PROMPT = """Given this query and a hypothetical passage, refine and expand the passage to be more specific and detailed.

Query: {query}

Current passage: {passage}

Refine this passage to better match what a real document about this topic would contain.
Return only the refined passage (3-5 sentences)."""


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class HypotheticalDocument:
    """A hypothetical document generated from a query."""
    passages: list[str]
    key_concepts: list[str]
    combined_text: str


@dataclass
class HyDEResult:
    """Result from HyDE processing."""
    hypothetical_doc: HypotheticalDocument | None
    hyde_enabled: bool
    generation_latency_ms: float
    passage_count: int


# ─── HyDE Functions ──────────────────────────────────────────────────────────

async def generate_hypothetical_document(query: str) -> HypotheticalDocument | None:
    """
    Generate a hypothetical document from a query.
    
    This creates a "fake" document that would answer the query,
    which can then be embedded and used for retrieval.
    
    Args:
        query: The user's search query
    
    Returns:
        HypotheticalDocument with passages and key concepts
    """
    import time
    import json
    
    start_time = time.time()
    client = _get_client()
    
    prompt = HYDE_GENERATION_PROMPT.format(query=query)
    
    try:
        response = await client.chat.completions.create(
            model=settings.HYDE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,  # Some creativity for varied passages
            max_tokens=500,
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # Fallback: try to find JSON object
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    data = json.loads(content[start:end])
                else:
                    log.warning(f"HyDE: Could not parse response: {content[:100]}")
                    return None
        
        passages = data.get("passages", [])
        key_concepts = data.get("key_concepts", [])
        
        # Combine passages into single text
        combined = " ".join(passages)
        
        generation_time = (time.time() - start_time) * 1000
        log.info(f"HyDE: Generated {len(passages)} passages in {generation_time:.1f}ms")
        
        return HypotheticalDocument(
            passages=passages,
            key_concepts=key_concepts,
            combined_text=combined,
        )
        
    except Exception as e:
        log.warning(f"HyDE generation failed: {e}")
        return None


async def refine_passage(query: str, passage: str) -> str:
    """
    Refine a hypothetical passage to be more specific.
    
    Args:
        query: The original query
        passage: The passage to refine
    
    Returns:
        Refined passage text
    """
    client = _get_client()
    
    prompt = HYDE_REFINEMENT_PROMPT.format(query=query, passage=passage)
    
    try:
        response = await client.chat.completions.create(
            model=settings.HYDE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        log.warning(f"HyDE refinement failed: {e}")
        return passage  # Return original on error


# ─── HyDE Agent Node for LangGraph ───────────────────────────────────────────

async def hyde_agent(state: AgentState) -> AgentState:
    """
    HyDE agent node for LangGraph workflow.
    
    This node:
    1. Generates hypothetical document from query
    2. Stores it in state for downstream embedding
    3. Falls back gracefully if HyDE is disabled or fails
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state with HyDE results
    """
    import time
    
    state.setdefault("agent_trace", {})
    state.setdefault("hyde_trace", {})
    
    start_time = time.time()
    
    # Check if HyDE is enabled
    if not settings.HYDE_ENABLED:
        log.debug("HyDE disabled, skipping")
        state["hyde_trace"]["enabled"] = False
        state["hyde_result"] = None
        return state
    
    query = state.get("rewritten_query", state.get("query", ""))
    
    # Skip HyDE for certain query types
    query_type = state.get("query_type", "")
    if query_type in ("chitchat", "save_note"):
        log.debug(f"HyDE skipped for query_type={query_type}")
        state["hyde_trace"]["enabled"] = False
        state["hyde_trace"]["skipped_reason"] = f"query_type={query_type}"
        state["hyde_result"] = None
        return state
    
    # Generate hypothetical document
    log.info(f"HyDE: Generating hypothetical document for query: {query[:50]}...")
    
    hyde_doc = await generate_hypothetical_document(query)
    
    generation_time = (time.time() - start_time) * 1000
    
    if hyde_doc:
        state["hyde_result"] = {
            "passages": hyde_doc.passages,
            "key_concepts": hyde_doc.key_concepts,
            "combined_text": hyde_doc.combined_text,
        }
        state["hyde_trace"]["enabled"] = True
        state["hyde_trace"]["passage_count"] = len(hyde_doc.passages)
        state["hyde_trace"]["generation_latency_ms"] = generation_time
        state["hyde_trace"]["key_concepts"] = hyde_doc.key_concepts
        
        log.info(f"HyDE: Generated {len(hyde_doc.passages)} passages with concepts: {hyde_doc.key_concepts}")
    else:
        state["hyde_result"] = None
        state["hyde_trace"]["enabled"] = True
        state["hyde_trace"]["generation_failed"] = True
        state["hyde_trace"]["generation_latency_ms"] = generation_time
        
        log.warning("HyDE: Generation failed, continuing without HyDE")
    
    return state


# ─── HyDE Embedding Helper ────────────────────────────────────────────────────

async def get_hyde_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Get embeddings for HyDE hypothetical document passages.
    
    This can be used by the retrieval agent to enhance embedding-based search.
    
    Args:
        texts: List of text passages to embed
    
    Returns:
        List of embedding vectors
    """
    from app.retrieval.embedder import embed_texts
    
    try:
        embeddings = await embed_texts(texts)
        return embeddings
    except Exception as e:
        log.warning(f"HyDE embedding failed: {e}")
        return []
