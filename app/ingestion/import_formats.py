"""One-shot import format adapters (Open Memory Hub MVP item 3).

Turn provider data-export files into normalized ``ImportItem`` rows that
``app.services.import_service`` persists as ``Memory`` rows. Every format
claim here is verified against the PAM importer mappings (Feb 2026) —
provider export formats change without notice, so each adapter is defensive:
malformed entries are skipped, never fatal.

Verified format sources (also published in docs/API.md §Imports):
    - ChatGPT conversations.json — mapping DAG, unix-float create_time,
      message.author.role, content.parts[] with nulls:
      https://github.com/portable-ai-memory/portable-ai-memory/blob/master/importer-mappings.md
    - Claude conversations.json — chat_messages (not messages), sender
      "human"/"assistant", ISO 8601, message-level text: same document §2.
    - PAM memory-store.json — https://portable-ai-memory.org/spec/v1.0/
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

#: source_format values accepted by the API (exact strings).
SOURCE_FORMATS = ("auto", "chatgpt", "claude", "generic")

#: Memory.source_type written per format (exact strings — also in the
#: MemoryCreate and list_memories Literals; no migration needed because
#: memories.source_type is an unconstrained String(32)).
SOURCE_TYPE_FOR_FORMAT = {
    "chatgpt": "chatgpt_import",
    "claude": "claude_import",
    "generic": "generic_import",
}

#: Per-memory content cap. Matches the ChatRequest.query cap (10_000) so an
#: imported conversation stays the same order of magnitude as one chat.
MAX_CONTENT_CHARS = 10_000
TRUNCATION_MARKER = "\n\n[import truncated]"


class ImportFormatError(ValueError):
    """The uploaded file does not match the requested/detected format."""


class ImportItem(BaseModel):
    """One normalized item extracted from an export file.

    Adapters skip empty items instead of constructing them — ``content``
    stays min_length=1 as a belt-and-suspenders guard.
    """

    title:       str | None      = Field(default=None, max_length=500)
    content:     str             = Field(min_length=1)
    source_ref:  str | None      = Field(default=None, max_length=500)
    source_url:  str | None      = Field(default=None, max_length=1000)
    captured_at: datetime        = Field(default_factory=lambda: datetime.now(UTC))
    tags:        list[str]       = Field(default_factory=list, max_length=50)
    metadata:    dict[str, Any]  = Field(default_factory=dict)


def _clip(value: Any, limit: int) -> str | None:
    """Coerce to a stripped str clipped to ``limit``; None for empty."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def _to_utc_datetime(value: Any) -> datetime:
    """Epoch seconds (int/float) or ISO 8601 str → aware UTC datetime.

    Unusable values (None, 0, garbage) fall back to ``now(UTC)`` so a bad
    upstream timestamp never drops a memory. Handles the ChatGPT unix-float
    and Claude/generic ISO-8601 forms verified in the PAM mappings.
    """
    try:
        if isinstance(value, (int, float)):
            epoch = float(value)
            if epoch > 0:
                return datetime.fromtimestamp(epoch, tz=UTC)
        elif isinstance(value, str) and value.strip():
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (ValueError, OverflowError, OSError):
        pass
    return datetime.now(UTC)


def _chatgpt_transcript(conversation: dict) -> str:
    """Render a conversation's user/assistant text, ordered by create_time.

    ``mapping`` is a DAG keyed by node id (not a flat list); nodes may carry
    ``message: null`` and ``parts`` may contain nulls (verified upstream).
    system/tool roles are dropped — they carry model instructions, not
    user knowledge. Message create_time can be 0/null → falls back to 0
    so ordering degrades to insertion order, never crashes.
    """
    turns: list[tuple[float, str, str]] = []
    for node in (conversation.get("mapping") or {}).values():
        message = node.get("message") if isinstance(node, dict) else None
        if not isinstance(message, dict):
            continue
        role = (message.get("author") or {}).get("role")
        if role not in ("user", "assistant"):
            continue
        parts = (message.get("content") or {}).get("parts") or []
        text = "\n".join(p.strip() for p in parts if isinstance(p, str) and p.strip())
        if not text:
            continue
        try:
            create_time = float(message.get("create_time") or 0)
        except (TypeError, ValueError):
            create_time = 0.0
        turns.append((create_time, role, text))
    turns.sort(key=lambda turn: turn[0])
    return "\n\n".join(
        f"{'User' if role == 'user' else 'Assistant'}: {text}" for _ts, role, text in turns
    )


def parse_chatgpt(data: Any) -> list[ImportItem]:
    """ChatGPT conversations.json (JSON array) → one ImportItem per conversation."""
    if not isinstance(data, list):
        raise ImportFormatError(
            "ChatGPT export must be the conversations.json JSON array "
            "(Settings → Data controls → Export data)."
        )
    items: list[ImportItem] = []
    for conversation in data:
        if not isinstance(conversation, dict):
            continue
        content = _chatgpt_transcript(conversation)
        if not content:
            continue
        items.append(
            ImportItem(
                title=_clip(conversation.get("title"), 500) or "Untitled ChatGPT conversation",
                content=content,
                source_ref=_clip(conversation.get("id"), 500),
                captured_at=_to_utc_datetime(conversation.get("create_time")),
                tags=["chatgpt"],
                metadata={"import_format": "chatgpt"},
            )
        )
    return items
