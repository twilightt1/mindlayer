import logging
import re

from openai import AsyncOpenAI

from app.agents.llm_parsing import coerce_float, coerce_string_list, parse_llm_json_object
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


CHITCHAT_PATTERN = re.compile(
    r"^(hello|hi|hey|xin chào|chào|alo|chào bạn|bạn khỏe|cảm ơn|thanks|thank you|ok|okay|bye|tạm biệt)[\s!?.]*$",
    re.IGNORECASE,
)

ROUTER_SYSTEM = """You are an intent classifier and query optimizer for a Vietnamese RAG chatbot.
Given the user's query and conversation history, you must:
1. Classify the intent
2. Rewrite the query to be fully self-contained (resolving pronouns based on history)
3. Generate 3 search variants (if intent is 'rag') for better retrieval coverage.

## Intent definitions:
**chitchat** — Casual conversation that requires no document lookup.
**summarize** — A request to summarize or synthesize content from documents or the conversation.
**rag** — A specific factual question that requires retrieving information from the knowledge base.

---

## Query to classify:
"{query}"

## Conversation history (last 3 turns):
{history}

---

## Output format:
Return ONLY valid JSON. No markdown, no explanation outside the JSON.

{{
  "intent": "<chitchat | summarize | rag>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one short sentence explaining the classification>",
  "rewritten_query": "<the self-contained version of the query>",
  "search_variants": ["<variant 1>", "<variant 2>", "<variant 3>"]
}}

## Example Output:
{{"intent": "rag", "confidence": 0.95, "reasoning": "User asks about product specs", "rewritten_query": "What are the specifications of product X?", "search_variants": ["Product X technical details", "Features of product X", "Product X datasheet"]}}
## Output:"""


def _router_fallback(state: AgentState, query: str, error: str, raw_preview: str | None = None) -> None:
    has_grounding_source = bool(state.get("has_documents") or state.get("personal_memory_enabled", False))
    fallback_intent = "rag" if has_grounding_source else "chitchat"
    state["query_type"] = fallback_intent
    state["rewritten_query"] = query
    state["search_variants"] = [query] if fallback_intent == "rag" else []
    state["router_confidence"] = 0.0
    state["router_reasoning"] = f"Error fallback: {error}"
    state["agent_trace"]["router"] = {
        "mode": "fallback",
        "intent": fallback_intent,
        "fallback_used": True,
        "error": error,
        "raw_response_preview": raw_preview,
    }


async def router_agent(state: AgentState) -> AgentState:
    state.setdefault("agent_trace", {})
    state.setdefault("retry_count", 0)
    state.setdefault("context_relevant", True)
    state.setdefault("is_hallucination", False)
    state.setdefault("answers_question", True)
    query = state.get("query", "").strip()
    q_lower = query.lower()

    if CHITCHAT_PATTERN.match(q_lower):
        state["query_type"] = "chitchat"
        state["rewritten_query"] = query
        state["search_variants"] = []
        state["router_confidence"] = 1.0
        state["router_reasoning"] = "Matched chitchat regex fast-path"
        state["agent_trace"]["router"] = {
            "mode": "regex",
            "intent": "chitchat",
            "confidence": 1.0,
            "fallback_used": False,
        }
        return state

    history = state.get("history", [])
    recent_history = history[-3:] if history else []
    history_str = ""
    for h in recent_history:
        role = h.get("role", "unknown")
        content = h.get("content", "")
        history_str += f"{role.capitalize()}: {content}\n"
    if not history_str:
        history_str = "(empty)"

    try:
        client = _get_client()
        prompt = ROUTER_SYSTEM.format(query=query, history=history_str.strip())

        resp = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            extra_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "RAG Router",
            },
        )
        result_text = resp.choices[0].message.content
        parsed = parse_llm_json_object(result_text)
        if not parsed.ok or parsed.data is None:
            _router_fallback(state, query, parsed.error or "invalid_router_json", parsed.raw_preview)
            log.warning("Router JSON parsing failed", extra={"error": parsed.error})
            return state

        result_json = parsed.data
        intent = str(result_json.get("intent", "rag")).lower()
        if intent not in ["rag", "chitchat", "summarize"]:
            intent = "rag"

        rewritten_query = result_json.get("rewritten_query")
        if not isinstance(rewritten_query, str) or not rewritten_query.strip():
            rewritten_query = query

        state["query_type"] = intent
        state["router_confidence"] = coerce_float(result_json.get("confidence"), 0.0, minimum=0.0, maximum=1.0)
        state["router_reasoning"] = str(result_json.get("reasoning") or "No reasoning provided")
        state["rewritten_query"] = rewritten_query.strip()
        state["search_variants"] = coerce_string_list(result_json.get("search_variants"), limit=3)
        state["agent_trace"]["router"] = {
            "mode": "llm",
            "intent": intent,
            "confidence": state["router_confidence"],
            "fallback_used": False,
        }

    except Exception as e:
        log.error("Router LLM error", extra={"error": str(e)})
        _router_fallback(state, query, str(e))

    return state
