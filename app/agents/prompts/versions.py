"""
Versioned prompt definitions for SupportMind agents.

Each prompt variant is registered as a `PromptVariant` (see registry.py).
Variants are grouped by agent (`router`, `answer`, `evaluator`, `hallucination`).

The `v1` variants are the production prompts used by the agents today.
`v2` variants are alternative phrasings that can be enabled via A/B testing
through the registry.
"""
from __future__ import annotations

from app.agents.prompts.variant import PromptVariant


# ---------------------------------------------------------------------------
# Router agent prompts
# ---------------------------------------------------------------------------

ROUTER_V1 = PromptVariant(
    name="router_v1",
    agent="router",
    description="Default router: classify as chitchat/summarize/rag; rewrite the query.",
    template=(
        "You are SupportMind's intent router.\n"
        "Classify the user message into exactly one of: chitchat, summarize, rag.\n"
        "If unsure, default to 'rag'.\n"
        "Then rewrite the user message to be self-contained (replace pronouns, "
        "add missing context). Respond as JSON: "
        '{"query_type": "...", "rewritten_query": "...", "rationale": "..."}\n\n'
        "User: {query}"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.1.0"},
)

ROUTER_V2 = PromptVariant(
    name="router_v2",
    agent="router",
    description="Slightly stricter: forces JSON keys, requires confident rationale.",
    template=(
        "You are the SupportMind intent router. Choose the most appropriate "
        "intent for the user's message.\n"
        "Allowed intents: chitchat, summarize, rag.\n"
        "Pick 'rag' if the question is about a product, document, or account.\n"
        "Respond STRICTLY as JSON with keys: query_type, rewritten_query, "
        "rationale. The rationale must mention one concrete reason for the choice.\n"
        "User: {query}\n"
        "JSON:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.4.0", "experiment": "stricter-json"},
)


# ---------------------------------------------------------------------------
# Answer agent prompts
# ---------------------------------------------------------------------------

ANSWER_V1 = PromptVariant(
    name="answer_v1",
    agent="answer",
    description="Default answer: cite [Source N] markers, follow citation rules.",
    template=(
        "You are SupportMind's support assistant.\n"
        "Answer the user's question using ONLY the context below.\n"
        "If the answer is not in the context, reply: "
        "\"I don't know based on the available SupportMind documentation.\"\n"
        "Cite sources inline as [Source 1], [Source 2], etc. "
        "Match numbers to the order the sources appear below.\n\n"
        "Question: {query}\n\n"
        "Context:\n{context}\n\n"
        "Answer:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.1.0"},
)

ANSWER_V2 = PromptVariant(
    name="answer_v2",
    agent="answer",
    description="Adds chain-of-thought: extract facts first, then answer.",
    template=(
        "You are SupportMind's support assistant. Be precise and cite sources.\n"
        "Step 1: From the context, list 2-5 bullet points of facts relevant to the question.\n"
        "Step 2: Compose a concise final answer using only those facts. "
        "Cite each fact as [Source N] matching the order below.\n"
        "If no relevant facts exist, reply: "
        "\"I don't know based on the available SupportMind documentation.\"\n\n"
        "Question: {query}\n\n"
        "Context:\n{context}\n\n"
        "Facts:\n"
        "- \n\n"
        "Answer:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.4.0", "experiment": "cot-extract"},
)


# ---------------------------------------------------------------------------
# Evaluator agent prompts (document relevance grading)
# ---------------------------------------------------------------------------

EVALUATOR_V1 = PromptVariant(
    name="evaluator_v1",
    agent="evaluator",
    description="Default per-chunk relevance grader.",
    template=(
        "You are grading a single retrieved document chunk for relevance to the user's "
        "question. Respond as JSON: {\"relevant\": true|false, \"reason\": \"...\"}.\n"
        "A chunk is 'relevant' iff it contains an answer (or partial answer) to the "
        "question.\n\n"
        "Question: {query}\n\n"
        "Chunk:\n{chunk}\n\n"
        "JSON:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.1.0"},
)

EVALUATOR_V2 = PromptVariant(
    name="evaluator_v2",
    agent="evaluator",
    description="Stricter: requires 'partial'/'full'/'none' relevance levels.",
    template=(
        "Grade the chunk's relevance to the question.\n"
        "Respond as JSON: {\"relevance\": \"full\"|\"partial\"|\"none\", \"reason\": \"...\"}.\n"
        "- 'full':   the chunk completely answers the question\n"
        "- 'partial': the chunk contains some useful information\n"
        "- 'none':   the chunk is unrelated\n\n"
        "Question: {query}\n\n"
        "Chunk:\n{chunk}\n\n"
        "JSON:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.4.0", "experiment": "graded-relevance"},
)


# ---------------------------------------------------------------------------
# Hallucination agent prompts
# ---------------------------------------------------------------------------

HALLUCINATION_V1 = PromptVariant(
    name="hallucination_v1",
    agent="hallucination",
    description="Default: judge if answer is grounded in context and answers the question.",
    template=(
        "You are verifying whether an answer is faithful to the given context.\n"
        "Respond as JSON: {\"grounded\": true|false, \"answers_question\": true|false, "
        "\"reason\": \"...\"}.\n\n"
        "Context:\n{context}\n\n"
        "Answer: {answer}\n\n"
        "Question: {query}\n\n"
        "JSON:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.1.0"},
)

HALLUCINATION_V2 = PromptVariant(
    name="hallucination_v2",
    agent="hallucination",
    description="Adds explicit citation-presence check.",
    template=(
        "You are an LLM-as-judge verifying answer faithfulness.\n"
        "Respond as JSON with keys: grounded, answers_question, has_citation, reason.\n"
        "- grounded: the answer's claims are supported by the context\n"
        "- answers_question: the answer addresses the question\n"
        "- has_citation: the answer contains [Source N] markers\n\n"
        "Context:\n{context}\n\n"
        "Answer: {answer}\n\n"
        "Question: {query}\n\n"
        "JSON:"
    ),
    metadata={"author": "supportmind", "introduced_in": "0.4.0", "experiment": "citation-check"},
)


# ---------------------------------------------------------------------------
# All registered versions
# ---------------------------------------------------------------------------

PROMPT_VERSIONS: dict[str, list[PromptVariant]] = {
    "router": [ROUTER_V1, ROUTER_V2],
    "answer": [ANSWER_V1, ANSWER_V2],
    "evaluator": [EVALUATOR_V1, EVALUATOR_V2],
    "hallucination": [HALLUCINATION_V1, HALLUCINATION_V2],
}


def get_default_variants() -> dict[str, str]:
    """Return the default variant name per agent (e.g. {'router': 'router_v1'})."""
    return {
        agent: variants[0].name for agent, variants in PROMPT_VERSIONS.items() if variants
    }
