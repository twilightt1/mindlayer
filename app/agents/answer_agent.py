import logging
import re
import time

from openai import AsyncOpenAI

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


SYSTEM_PROMPT = """You are a precise RAG assistant. Your ONLY job is to answer questions using the provided context.

STRICT RULES:
1. Every factual claim MUST be supported by a [Source N] citation from the context below.
2. If the context does not contain enough information, respond ONLY with: "Tôi không tìm thấy thông tin về vấn đề này trong tài liệu." but translate it to the language of the user's question. For example, if the question is in Vietnamese, respond with the Vietnamese sentence. If it's in English, respond with "I couldn't find information about this issue in the documents."
3. Do NOT use your general knowledge to fill gaps — if it's not in the context, it doesn't exist.
4. Do NOT speculate, extrapolate, or infer beyond what is explicitly stated.
5. Respond in the EXACT SAME LANGUAGE as the user's question.

Format example:
"Thời hạn bảo hành là 12 tháng [Source 1]. Điều kiện áp dụng bao gồm... [Source 2]."
"""

CITATION_RE = re.compile(r"\[source\s*\d+\]", re.IGNORECASE)
VIETNAMESE_HINTS = (
    "à", "á", "ạ", "ả", "ã", "â", "ầ", "ấ", "ậ", "ẩ", "ẫ", "ă", "ằ", "ắ", "ặ", "ẳ", "ẵ",
    "è", "é", "ẹ", "ẻ", "ẽ", "ê", "ề", "ế", "ệ", "ể", "ễ", "ì", "í", "ị", "ỉ", "ĩ",
    "ò", "ó", "ọ", "ỏ", "õ", "ô", "ồ", "ố", "ộ", "ổ", "ỗ", "ơ", "ờ", "ớ", "ợ", "ở", "ỡ",
    "ù", "ú", "ụ", "ủ", "ũ", "ư", "ừ", "ứ", "ự", "ử", "ữ", "ỳ", "ý", "ỵ", "ỷ", "ỹ", "đ",
)


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def _safe_generation_error(query: str) -> str:
    if any(char in query.casefold() for char in VIETNAMESE_HINTS):
        return "Xin lỗi, tôi chưa thể tạo câu trả lời lúc này. Vui lòng thử lại."
    return "Sorry, I couldn't generate an answer right now. Please try again."


def _source_label(chunk: dict) -> str:
    source_type = (chunk.get("metadata") or {}).get("source_type") or "document"
    labels = {
        "document": "document",
        "personal_memory": "personal memory",
        "knowledge_graph": "knowledge graph",
    }
    return labels.get(str(source_type), str(source_type).replace("_", " "))


def _record_citation_trace(state: AgentState) -> None:
    response = state.get("response", "")
    source_count = len(state.get("reranked_chunks", []))
    state.setdefault("agent_trace", {})["citation"] = {
        "has_citation": bool(CITATION_RE.search(response)),
        "source_count": source_count,
        "required": state.get("query_type") == "rag" and source_count > 0,
    }


async def answer_agent(state: AgentState) -> AgentState:
    state.setdefault("agent_trace", {})
    total_start = time.perf_counter()
    first_token_ms: float | None = None

    if state.get("query_type") == "summarize" and state.get("reranked_chunks"):
        context_parts = []
        for chunk in state["reranked_chunks"]:
            fname = chunk.get("metadata", {}).get("filename", "unknown")
            source_label = _source_label(chunk)
            context_parts.append(f"=== {source_label.upper()}: {fname} ===\n{chunk['content']}\n=== END OF {fname} ===")
        context = "\n\n".join(context_parts)
        system = f"You are an expert analyst. The user has provided the full text of one or more documents below. Please provide a comprehensive, well-structured summary of these documents. DO NOT complain about the text being disjointed, because it is the full document text reconstructed. Just summarize it.\nIMPORTANT: You MUST respond in the EXACT SAME LANGUAGE as the user's request.\n\n{context}"
    elif state.get("query_type") == "rag" and state.get("reranked_chunks"):
        context_parts = []
        for i, chunk in enumerate(state["reranked_chunks"], 1):
            fname = chunk.get("metadata", {}).get("filename", "unknown")
            source_label = _source_label(chunk)
            context_parts.append(f"[Source {i}] ({source_label} - {fname})\n{chunk['content']}")
        context = "\n\n---\n\n".join(context_parts)
        system = f"{SYSTEM_PROMPT}\n\nContext:\n{context}"
    else:
        system = SYSTEM_PROMPT

    messages = [{"role": "system", "content": system}]
    for h in state.get("history", []):
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": state["query"]})

    full_response = ""
    token_count = 0
    error: str | None = None

    try:
        stream = await _get_client().chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.ANSWER_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            stream=True,
            extra_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "RAG System",
            },
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta and first_token_ms is None:
                first_token_ms = _elapsed_ms(total_start)
            full_response += delta

            cb = state.get("_stream_callback")
            if cb:
                await cb(delta)

            if chunk.usage:
                token_count = chunk.usage.total_tokens

    except Exception as e:
        log.error("LLM error", extra={"error": str(e)})
        error = str(e)
        full_response = _safe_generation_error(state.get("query", ""))

    state["response"] = full_response
    state["token_count"] = token_count
    state["agent_trace"]["answer"] = {
        "model": settings.LLM_MODEL,
        "tokens": token_count,
        "context_chunks": len(state.get("reranked_chunks", [])),
        "retry_count": state.get("retry_count", 0),
        "latency_ms": _elapsed_ms(total_start),
        "first_token_ms": first_token_ms,
    }
    if error:
        state["agent_trace"]["answer"]["error"] = error
    _record_citation_trace(state)
    return state
