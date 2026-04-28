import asyncio
import logging

from openai import AsyncOpenAI

from app.agents.llm_parsing import parse_llm_json_object
from app.agents.state import AgentState
from app.config import settings

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
    return _client


SYSTEM_PROMPT = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
It does not need to be a stringent test. The goal is to filter out erroneous retrievals.

Provide your output as a JSON object with a single key "score" and value "yes" or "no". No other text."""


def _fail_open() -> bool:
    return settings.EVALUATOR_FAILURE_MODE in {"warn_only", "fail_open"}


async def evaluator_agent(state: AgentState) -> AgentState:
    state.setdefault("agent_trace", {})
    state.setdefault("retry_count", 0)

    if state.get("query_type") != "rag":
        state["context_relevant"] = True
        state["agent_trace"]["grade_docs"] = "skipped"
        return state

    chunks = state.get("reranked_chunks", [])
    if not chunks:
        state["context_relevant"] = False
        state["agent_trace"]["grade_docs"] = "no_chunks"
        return state

    query = state["query"]
    client = _get_client()

    async def _grade_chunk(chunk: dict) -> tuple[dict, bool, str | None, str | None]:
        user_prompt = f"Question: {query}\n\nDocument:\n{chunk['content']}"
        try:
            resp = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": "RAG Evaluator",
                },
            )
            parsed = parse_llm_json_object(resp.choices[0].message.content)
            if not parsed.ok or parsed.data is None:
                raise ValueError(parsed.error or "invalid_grader_json")
            score = str(parsed.data.get("score", "no")).strip().casefold()
            return chunk, score == "yes", None, parsed.raw_preview
        except Exception as exc:
            log.warning("Document relevance grading failed", extra={"error": str(exc)})
            return chunk, _fail_open(), str(exc), None

    results = await asyncio.gather(*[_grade_chunk(c) for c in chunks])
    relevant_chunks = [c for c, is_relevant, _, _ in results if is_relevant]
    errors = [error for _, _, error, _ in results if error]

    if relevant_chunks:
        state["reranked_chunks"] = relevant_chunks
        state["context_relevant"] = True
    else:
        state["context_relevant"] = False

    state["agent_trace"]["grade_docs"] = {
        "total": len(chunks),
        "kept": len(relevant_chunks),
        "filtered": len(chunks) - len(relevant_chunks),
        "retry_count": state.get("retry_count", 0),
        "failure_mode": settings.EVALUATOR_FAILURE_MODE,
        "fallback_used": bool(errors),
        "error_count": len(errors),
    }
    if errors:
        state["agent_trace"]["grade_docs"]["errors"] = errors[:3]
    return state