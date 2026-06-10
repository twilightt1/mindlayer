import json
import logging
import re
from datetime import datetime
from uuid import UUID

from app.agents.state import AgentState
from app.redis_client import get_redis

log = logging.getLogger(__name__)

# Lead-in phrases that mark an explicit "save this" imperative. Stripped from
# the stored note so the memory holds the content, not the command.
_SAVE_TRIGGER_RE = re.compile(
    r"^\s*(please\s+)?(remember that|remember to|remember|note that|save (?:this|a) note|"
    r"make a note|take a note|jot down|note|ghi nhớ rằng|ghi nhớ|ghi chú lại|ghi chú|"
    r"lưu lại rằng|lưu lại|lưu|lưu ý rằng|lưu ý|nhớ giùm|nhớ là|nhớ)\b"
    r"\s*[:\-,]?\s*",
    re.IGNORECASE,
)

_VIETNAMESE_HINTS = (
    "à", "á", "ạ", "ả", "ã", "â", "ầ", "ấ", "ậ", "ẩ", "ẫ", "ă", "ằ", "ắ", "ặ", "ẳ", "ẵ",
    "è", "é", "ẹ", "ẻ", "ẽ", "ê", "ề", "ế", "ệ", "ể", "ễ", "ì", "í", "ị", "ỉ", "ĩ",
    "ò", "ó", "ọ", "ỏ", "õ", "ô", "ồ", "ố", "ộ", "ổ", "ỗ", "ơ", "ờ", "ớ", "ợ", "ở", "ỡ",
    "ù", "ú", "ụ", "ủ", "ũ", "ư", "ừ", "ứ", "ự", "ử", "ữ", "ỳ", "ý", "ỵ", "ỷ", "ỹ", "đ",
)


def _is_vietnamese(text: str) -> bool:
    return any(ch in text.casefold() for ch in _VIETNAMESE_HINTS)


def _strip_save_trigger(query: str) -> str:
    """Remove a leading save imperative, leaving just the note content."""
    return _SAVE_TRIGGER_RE.sub("", query, count=1).strip()


def _note_title(content: str) -> str:
    """Derive a short title from the first line/sentence of the note."""
    first_line = content.strip().splitlines()[0] if content.strip() else ""
    title = first_line.strip()
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    return title or "Note"

async def memory_load_agent(state: AgentState) -> AgentState:
    cid = state["conversation_id"]
    redis = await get_redis()
    cached = await redis.get(f"conv_history:{cid}")
    if cached:
        state["history"] = json.loads(cached)
        return state
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.message import Message
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Message).where(Message.conversation_id == cid)
                .order_by(Message.created_at.desc()).limit(10)
            )
            msgs = result.scalars().all()
        history = [{"role": m.role, "content": m.content} for m in reversed(msgs)]
        state["history"] = history
        await redis.setex(f"conv_history:{cid}", 300, json.dumps(history))
    except Exception as e:
        log.warning("History load failed", extra={"error": str(e)})
        state["history"] = []
    return state

def _used_memory_ids(state: AgentState) -> list[str]:
    """Memory ids that survived into the grounding context for this answer."""
    seen: list[str] = []
    for chunk in state.get("grounding_context_chunks", []) or []:
        mid = (chunk.get("metadata") or {}).get("memory_id")
        if mid and mid not in seen:
            seen.append(str(mid))
    return seen


async def _bump_used_memory_salience(state: AgentState) -> int:
    """Reward memories that were actually used in the answer (P2.1).

    Best-effort and isolated in its own session so a failure here never
    affects message persistence or the chat turn.
    """
    memory_ids = _used_memory_ids(state)
    if not memory_ids:
        return 0
    try:
        from app.database import AsyncSessionLocal
        from app.retrieval.memory.salience import bump_salience

        async with AsyncSessionLocal() as db:
            count = await bump_salience(db, UUID(state["user_id"]), memory_ids)
        state.setdefault("agent_trace", {})["salience_bump"] = {"memories_bumped": count}
        return count
    except Exception as e:  # noqa: BLE001
        log.warning("Salience bump failed", extra={"error": str(e)})
        state.setdefault("agent_trace", {})["salience_bump"] = {"error": str(e)}
        return 0


def _record_grounding_confidence(state: AgentState) -> None:
    """Compute + store grounding confidence once the full trace is assembled.

    Runs in the save node (after grade_gen) so the hallucination verdict is
    available. Stored in agent_trace.grounding so it is persisted with the
    message and surfaced in the SSE done event.
    """
    try:
        from app.agents.grounding import compute_grounding_confidence

        state.setdefault("agent_trace", {})["grounding"] = compute_grounding_confidence(state)
    except Exception as e:  # noqa: BLE001
        log.warning("Grounding confidence failed", extra={"error": str(e)})


async def memory_save_agent(state: AgentState) -> AgentState:
    cid = state["conversation_id"]

    # P3: finalize the grounding-confidence signal BEFORE persisting the trace,
    # so it is stored on the assistant message and queryable by the trend job.
    _record_grounding_confidence(state)

    try:
        from app.database import AsyncSessionLocal
        from app.models.message import Message
        async with AsyncSessionLocal() as db:
            db.add(Message(conversation_id=cid, role="user", content=state["query"]))
            db.add(Message(conversation_id=cid, role="assistant", content=state["response"],
                           agent_trace=state.get("agent_trace", {})))
            await db.commit()
        redis = await get_redis()
        await redis.delete(f"conv_history:{cid}")
    except Exception as e:
        log.error("Save messages failed", extra={"error": str(e)})

    # P2.1: reward memories used in this answer (after persistence, best-effort).
    await _bump_used_memory_salience(state)
    return state


async def memory_save_note_agent(state: AgentState) -> AgentState:
    """Persist the user's message as a personal memory (save_note intent).

    Strips the "remember that…" lead-in, stores the remaining text as a
    Memory (source_type=conversation_excerpt), embeds + enqueues graph
    extraction via the shared write-back pipeline, and sets a confirmation
    response. The node then flows into ``save`` (message persistence + the
    terminal SSE emit), so no SSE changes are needed.
    """
    state.setdefault("agent_trace", {})
    query = state.get("query", "")
    vietnamese = _is_vietnamese(query)
    content = _strip_save_trigger(query)

    async def _stream(text: str) -> None:
        cb = state.get("_stream_callback")
        if cb:
            await cb(text)

    # Nothing left after stripping the trigger → ask for the note content.
    if not content:
        msg = (
            "Bạn muốn tôi ghi nhớ điều gì? Hãy cho tôi biết nội dung cần lưu."
            if vietnamese
            else "What would you like me to remember? Please tell me the note content."
        )
        state["response"] = msg
        await _stream(msg)
        state["agent_trace"]["save_note"] = {"saved": False, "reason": "empty_content"}
        return state

    memory_id: str | None = None
    try:
        from app.database import AsyncSessionLocal
        from app.models.memory import Memory
        from app.retrieval.memory.write_back import index_new_memory

        async with AsyncSessionLocal() as db:
            memory = Memory(
                user_id=UUID(state["user_id"]),
                source_type="conversation_excerpt",
                source_ref=f"conversation:{state['conversation_id']}",
                title=_note_title(content),
                content=content,
                tags=["chat_note"],
                captured_at=datetime.utcnow(),
                extra_metadata={
                    "kind": "chat_note",
                    "conversation_id": state["conversation_id"],
                },
            )
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            memory_id = str(memory.id)
            # Best-effort embed + graph (Postgres row is source of truth).
            await index_new_memory(memory)

        msg = (
            f"Đã lưu vào bộ nhớ của bạn: \"{_note_title(content)}\""
            if vietnamese
            else f"Saved to your memory: \"{_note_title(content)}\""
        )
        state["response"] = msg
        await _stream(msg)
        state["agent_trace"]["save_note"] = {"saved": True, "memory_id": memory_id}
    except Exception as e:
        log.error("save_note failed", extra={"error": str(e)})
        msg = (
            "Xin lỗi, tôi chưa thể lưu ghi chú này. Vui lòng thử lại."
            if vietnamese
            else "Sorry, I couldn't save that note right now. Please try again."
        )
        state["response"] = msg
        await _stream(msg)
        state["agent_trace"]["save_note"] = {"saved": False, "error": str(e)}

    return state
