# Import Paths v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users pull existing AI-memory exports into Orivory: a one-shot import service + `POST /api/v1/imports` endpoint that parses ChatGPT / Claude / generic(+PAM) JSON exports into `Memory` rows, dedups by `(user_id, source_type, source_ref)`, indexes best-effort, and returns an honest summary `{created, skipped_duplicates, failed}`.

**Architecture:** Reuse the existing stack — no new tables, no migration: imports write plain `Memory` rows with three new `source_type` values (`chatgpt_import`, `claude_import`, `generic_import`; the column is an unconstrained `String(32)`). A pure parsing module (`app/ingestion/import_formats.py`) turns each verified export shape into normalized `ImportItem`s; a service (`app/services/import_service.py`) does dedup (one batched `source_ref IN (...)` query, like `SourceSyncService`), batched row creation, one commit, and best-effort `index_new_memory`. The router (`app/api/v1/imports.py`) is synchronous with a 20 MiB cap — Celery for large files is a follow-up. One memory per conversation (transcript rendering, 10 000-char cap) because conversations can be huge.

**Tech Stack:** FastAPI + `python-multipart` (already a dependency — `chat.py` uses `UploadFile` today), SQLAlchemy 2.0 async (existing), Pydantic v2 (existing), stdlib `json` only. **No new dependencies.**

**Spec:** `docs/ideas/open-memory-hub.md` (MVP item 3: "Import paths — Rewind/Limitless/OpenRecall exports; ChatGPT/Claude/Gemini memory exports (PAM mappings)").

### Verified export formats (primary sources for every format claim below)

- **ChatGPT** — export path: Settings → Data controls → Export data, ZIP by email (https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data). File/shape: `conversations.json` is a JSON **array**; conversation has `id`, `title`, `create_time`/`update_time` (**unix epoch float seconds**); messages live in `mapping` as a **DAG keyed by node id** (not a flat list) with `message: null` nodes, `message.author.role`, `message.content.parts[]` (may contain strings, dicts, **nulls**), per-message `create_time` that can be `0`/`null`. ChatGPT's "Memory" feature contents are **NOT** in the export. Source: https://github.com/portable-ai-memory/portable-ai-memory/blob/master/importer-mappings.md §1.
- **Claude** — Settings → Privacy → Export data; `conversations.json` is a JSON **array**; conversation has `uuid`, `name`, `summary`, `created_at`/`updated_at` (**ISO 8601**), and messages in **`chat_messages`** (NOT `messages`) as a flat linear array with `sender` = **`"human"`/`"assistant"`** (NOT `user`), message-level `text` (plain-text duplicate of the `content[]` text parts), `content[]` blocks of types `text|thinking|tool_use|tool_result|token_budget`. Companion files `memories.json` (`conversations_memory` + `project_memories`), `projects.json`, `users.json`. Source: same importer-mappings.md §2 (verified against a real Feb 2026 export).
- **PAM** — spec v1.0 (`schema: "portable-ai-memory"`, `memories[]` with `id`, `type`, `content`, `temporal.created_at`, `provenance.platform`): https://github.com/portable-ai-memory/portable-ai-memory/blob/master/spec.md (§20 provider matrix, §25 normalized conversations) + https://portable-ai-memory.org/ (minimal example file). Detection heuristics for provider formats: importer-mappings.md §9.
- **Rewind / Limitless — NOT verifiable, no adapter in v0 (honest flag).** Rewind stopped recording 2025-12-19 after the Meta acquisition (https://rewind.ai/what-happened-to-rewind/). History lives in a **SQLCipher-encrypted local SQLite** db (`~/Library/Application Support/com.memoryvault.MemoryVault/db-enc.sqlite3`, https://github.com/pedramamini/RewindMCP/blob/main/README-SCHEMA.md) with **no official export format**; community tools decrypt locally (https://github.com/anaclumos/rewind-export-all-data). v0 ships only the generic JSON path + docs note. Dedicated adapter = follow-up, blocked on format verification.
- **OpenRecall — storage verified; v0 via generic dump recipe, native adapter = follow-up.** Local **unencrypted SQLite**, table `entries(id INTEGER PK, app TEXT, title TEXT, text TEXT, timestamp INTEGER UNIQUE, embedding BLOB)` (unix seconds). Source: https://github.com/openrecall/openrecall/blob/main/openrecall/database.py. v0 documents a `sqlite3 → json_group_array` one-liner into the generic format (Task 5 docs); a native `.db` upload adapter is a follow-up.
- **Gemini / Copilot — deferred.** Formats verified in importer-mappings.md (§3 Takeout `MyActivity.json` two variants; §4 Privacy Dashboard CSV, two column layouts) but not in v0's JSON scope; CSV support and these adapters are follow-ups.

## Global Constraints

- Python 3.12+, ruff line-length 120, target py313 (`pyproject.toml`); zero NEW ruff findings in touched files.
- All routes under `/api/v1`; routers use `Annotated[User, Depends(get_current_verified_user)]` and `Annotated[AsyncSession, Depends(get_db)]` (copy the pattern from `app/api/v1/erasure.py:33-41`).
- Postgres is source of truth; Chroma/graph indexing stays best-effort via `app/retrieval/memory/write_back.py` (`index_new_memory` never raises).
- **Migration: NONE.** Imports reuse the `memories` table; `memories.source_type` is an unconstrained `String(32)` (created in `alembic/versions/a1b2c3d4e5f6_mindlayer_core.py:34`, no CHECK constraint anywhere) — new `source_type` values need no schema change.
- New `Memory.source_type` strings, exact: `chatgpt_import`, `claude_import`, `generic_import`. They must match **identically** in `app/schemas/Orivory.py` (`MemoryCreate` Literal), `app/api/v1/memories.py` (`list_memories` filter Literal), and `app/ingestion/import_formats.py::SOURCE_TYPE_FOR_FORMAT` (locked by a Task 1 test).
- `source_format` values, exact: `auto`, `chatgpt`, `claude`, `generic` (API field + `SOURCE_FORMATS` tuple).
- Caps: upload ≤ 20 MiB (`MAX_IMPORT_UPLOAD_BYTES = 20 * 1024 * 1024`, router answers 413); per-memory content ≤ 10 000 chars (`MAX_CONTENT_CHARS = 10_000`, matches `ChatRequest.query` cap in `app/schemas/conversation.py:60`); titles clipped at 500, refs at 500, URLs at 1000.
- CI-safe tests only: no live Postgres/Redis/Chroma; fake-DB pattern from `tests/services/test_erasure_service.py` (compiled-SQL dispatch fakes), inline JSON fixtures mirroring the verified shapes. Register the new router in `tests/api/test_router_wiring.py:ROUTERS_TO_CHECK`.
- `datetime.now(UTC)` aware everywhere (never naive, never `utcnow()`); **never log imported file contents** (privacy — log only ids/counts/format).
- Every task ends with `ruff check app tests` green + the touched pytest subset green + a Conventional Commit.

---

### Task 1: Import formats module — `ImportItem`, helpers, ChatGPT adapter

**Files:**
- Create: `app/ingestion/import_formats.py`
- Create: `tests/ingestion/__init__.py` (empty)
- Test: `tests/ingestion/test_import_formats.py`

**Interfaces:**
- Produces (used by Tasks 2–4):
  - `ImportItem` (Pydantic): `title: str | None` (≤500), `content: str` (`min_length=1`), `source_ref: str | None` (≤500), `source_url: str | None` (≤1000), `captured_at: datetime` (default `datetime.now(UTC)`), `tags: list[str]` (≤50), `metadata: dict[str, Any]`.
  - `ImportFormatError(ValueError)` — the only error type the router maps to 422.
  - Constants: `SOURCE_FORMATS = ("auto", "chatgpt", "claude", "generic")`; `SOURCE_TYPE_FOR_FORMAT = {"chatgpt": "chatgpt_import", "claude": "claude_import", "generic": "generic_import"}`; `MAX_CONTENT_CHARS = 10_000`; `TRUNCATION_MARKER = "\n\n[import truncated]"`.
  - `parse_chatgpt(data: Any) -> list[ImportItem]` — one item per conversation, transcript `User: … / Assistant: …` ordered by `create_time`, `source_ref = conversation.id`, `captured_at` from conversation `create_time`.
  - Helpers `_clip(value, limit) -> str | None`, `_to_utc_datetime(value: Any) -> datetime` (epoch float or ISO 8601 → aware UTC; `None`/`0`/garbage → `datetime.now(UTC)`).

- [ ] **Step 1: Write the failing test** — `tests/ingestion/test_import_formats.py`:

```python
"""Unit tests for import format adapters.

Inline fixtures mirror the VERIFIED export shapes (sources listed in
docs/superpowers/plans/2026-09-02-import-paths.md and docs/API.md §Imports):
ChatGPT mapping-DAG conversations.json, Claude chat_messages export.
CI-safe: pure parsing, no DB, no Chroma.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.ingestion.import_formats import (
    SOURCE_TYPE_FOR_FORMAT,
    ImportFormatError,
    ImportItem,
    _to_utc_datetime,
    parse_chatgpt,
)

# Real ChatGPT conversations.json shape: array of conversations; mapping is a
# DAG keyed by node id; entries may carry message: null; parts may contain
# nulls; create_time is a unix float (conversation-level) — verified against
# PAM importer-mappings.md §1.
CHATGPT_SAMPLE = [
    {
        "id": "6ef2b3a1-2c4d-4e2f-9a1b-000000000001",
        "title": "Postgres indexing advice",
        "create_time": 1738454400.0,
        "update_time": 1738454500.0,
        "mapping": {
            "root": {"id": "root", "message": None, "parent": None, "children": ["u", "a"]},
            "u": {
                "id": "u",
                "parent": "root",
                "children": ["a"],
                "message": {
                    "id": "u",
                    "author": {"role": "user"},
                    "create_time": 1738454400.5,
                    "content": {"content_type": "text", "parts": ["How should I index a jsonb column?"]},
                },
            },
            "a": {
                "id": "a",
                "parent": "u",
                "children": [],
                "message": {
                    "id": "a",
                    "author": {"role": "assistant"},
                    "create_time": 1738454410.9,
                    "content": {"content_type": "text", "parts": ["Use a GIN index on the jsonb path expression.", None]},
                    "metadata": {"model_slug": "gpt-4o"},
                },
            },
        },
    },
    {
        # system-role message only → no user knowledge → skipped
        "id": "skipped-empty",
        "title": "No user/assistant text",
        "create_time": 1738454600.0,
        "mapping": {
            "s": {
                "id": "s",
                "message": {
                    "author": {"role": "system"},
                    "create_time": 1.0,
                    "content": {"parts": ["You are ChatGPT."]},
                },
            }
        },
    },
]


def test_source_type_mapping_locked():
    """Cross-task contract: these exact strings appear in the MemoryCreate /
    list_memories Literals (Task 4) and the service's Memory rows (Task 3)."""
    assert SOURCE_TYPE_FOR_FORMAT == {
        "chatgpt": "chatgpt_import",
        "claude": "claude_import",
        "generic": "generic_import",
    }


def test_parse_chatgpt_one_memory_per_conversation():
    items = parse_chatgpt(CHATGPT_SAMPLE)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Postgres indexing advice"
    assert item.source_ref == "6ef2b3a1-2c4d-4e2f-9a1b-000000000001"
    assert item.captured_at == datetime.fromtimestamp(1738454400.0, tz=UTC)
    assert "User: How should I index a jsonb column?" in item.content
    assert "Assistant: Use a GIN index on the jsonb path expression." in item.content
    # ordered by message create_time (user turn first)
    assert item.content.index("User:") < item.content.index("Assistant:")
    assert item.tags == ["chatgpt"]
    assert item.metadata == {"import_format": "chatgpt"}


def test_parse_chatgpt_skips_conversations_without_user_text():
    items = parse_chatgpt(CHATGPT_SAMPLE)
    assert [i.source_ref for i in items] == ["6ef2b3a1-2c4d-4e2f-9a1b-000000000001"]


def test_parse_chatgpt_requires_array():
    with pytest.raises(ImportFormatError, match="conversations.json JSON array"):
        parse_chatgpt({"mapping": {}})


def test_to_utc_datetime_variants():
    epoch = _to_utc_datetime(1738454400.5)
    assert epoch == datetime.fromtimestamp(1738454400.5, tz=UTC)
    assert _to_utc_datetime(1738454400).tzinfo is not None  # int epochs too
    assert _to_utc_datetime(0).tzinfo is not None           # unix 0 → now(UTC) fallback
    assert _to_utc_datetime(None).tzinfo is not None       # missing → now(UTC)
    iso = _to_utc_datetime("2026-01-20T09:15:00Z")
    assert iso == datetime(2026, 1, 20, 9, 15, tzinfo=UTC)  # Z suffix handled
    naive = _to_utc_datetime("2026-01-20T09:15:00")
    assert naive.tzinfo is not None                         # naive → assumed UTC
    garbage = _to_utc_datetime("not-a-date")
    assert garbage.tzinfo is not None                       # garbage → now(UTC)


def test_import_item_rejects_empty_content():
    from pydantic import ValidationError

    # ValidationError subclasses ValueError; adapters skip empties before
    # constructing items, so this is a belt-and-suspenders guard.
    with pytest.raises(ValidationError):
        ImportItem(content="")
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/ingestion/test_import_formats.py -v` → FAIL (ModuleNotFoundError / ImportError on `app.ingestion.import_formats`).
- [ ] **Step 3: Implement** — `app/ingestion/import_formats.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/ingestion/test_import_formats.py -v` → PASS (all Task 1 tests green).
- [ ] **Step 5: Lint + commit** — `ruff check app tests && pytest tests/ingestion -q` → green; `git commit -m "feat: import format module (ImportItem + ChatGPT adapter)"`.

---

### Task 2: Claude, generic + PAM adapters, `detect_format`, `parse_import`

**Files:**
- Modify: `app/ingestion/import_formats.py` (append Task 2 functions + `__all__`)
- Test: `tests/ingestion/test_import_formats.py` (append)

**Interfaces:**
- Consumes: `ImportItem`, `ImportFormatError`, `MAX_CONTENT_CHARS`, `TRUNCATION_MARKER`, `_clip`, `_to_utc_datetime` (Task 1).
- Produces (used by Tasks 3–4):
  - `parse_claude(data: Any) -> list[ImportItem]` — one item per conversation from `chat_messages` (`sender` `"human"`/`"assistant"`, message-level `text`), `source_ref = uuid`, `captured_at` from conversation `created_at` (ISO 8601).
  - `parse_generic(data: Any) -> list[ImportItem]` — accepts EITHER a PAM `memory-store.json` (dict with `schema == "portable-ai-memory"`, handled by `_parse_pam`) OR a JSON array of `{title?, content, created_at?, url?, ref?, tags?}`.
  - `detect_format(data: Any) -> str` — `"chatgpt" | "claude" | "generic" | "unknown"` (PAM spec §9 heuristics).
  - `parse_import(source_format: str, data: Any) -> list[ImportItem]` — dispatches to the concrete parser (NOT `"auto"` — the service resolves auto first), caps every item's content to exactly `MAX_CONTENT_CHARS` when over.

- [ ] **Step 1: Write the failing tests** — append to `tests/ingestion/test_import_formats.py` (extend the import block at the top with the new names):

```python
# — top-of-file imports gain: —
#     detect_format, parse_claude, parse_generic, parse_import, MAX_CONTENT_CHARS

# Real Claude conversations.json shape: array; chat_messages (NOT messages);
# sender "human"/"assistant"; message-level text is the plain-text duplicate
# of content[] text parts; created_at ISO 8601 — verified against PAM
# importer-mappings.md §2.
CLAUDE_SAMPLE = [
    {
        "uuid": "9f1c2ab3-1111-4222-8333-444444444444",
        "name": "Vector db selection",
        "summary": "Choosing a vector database",
        "created_at": "2026-01-20T09:15:00Z",
        "updated_at": "2026-01-20T09:20:00Z",
        "chat_messages": [
            {
                "uuid": "m1",
                "sender": "human",
                "text": "pgvector or Qdrant for 10M vectors?",
                "created_at": "2026-01-20T09:15:00Z",
                "content": [],
            },
            {
                "uuid": "m2",
                "sender": "assistant",
                "text": "pgvector keeps data in Postgres; Qdrant separates storage.",
                "created_at": "2026-01-20T09:16:00Z",
                "content": [{"type": "text", "text": "pgvector keeps data in Postgres; Qdrant separates storage."}],
            },
        ],
    },
    {"uuid": "empty-conv", "name": "No text", "chat_messages": []},
]

# Real PAM memory-store.json shape (minimal example from portable-ai-memory.org).
PAM_SAMPLE = {
    "schema": "portable-ai-memory",
    "schema_version": "1.0",
    "owner": {"id": "user-123"},
    "memories": [
        {
            "id": "mem-001",
            "type": "skill",
            "content": "User is a cloud infrastructure engineer",
            "temporal": {"created_at": "2025-01-15T00:00:00Z"},
            "provenance": {"platform": "chatgpt"},
        },
        {
            "id": "mem-002",
            "type": "preference",
            "content": "Prefers concise answers",
            "temporal": {"created_at": "2025-02-01T00:00:00Z"},
            "provenance": {"platform": "claude"},
        },
    ],
}

GENERIC_SAMPLE = [
    {
        "title": "Rewind daily digest",
        "content": "Worked on the import path today.",
        "created_at": "2026-09-01T10:00:00Z",
        "url": "https://example.com/d",
        "tags": ["rewind"],
        "ref": "rewind-2026-09-01",
    },
    {"content": "untitled note"},
    {"title": "no content — skipped"},
]


def test_parse_claude_one_memory_per_conversation():
    items = parse_claude(CLAUDE_SAMPLE)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Vector db selection"
    assert item.source_ref == "9f1c2ab3-1111-4222-8333-444444444444"
    assert item.captured_at == datetime(2026, 1, 20, 9, 15, tzinfo=UTC)
    assert item.content.startswith("User: pgvector or Qdrant")
    assert "Assistant: pgvector keeps data in Postgres" in item.content
    assert item.tags == ["claude"]
    assert item.metadata == {"import_format": "claude"}


def test_parse_claude_requires_array():
    with pytest.raises(ImportFormatError, match="conversations.json JSON array"):
        parse_claude({"chat_messages": []})


def test_parse_generic_array():
    items = parse_generic(GENERIC_SAMPLE)
    assert len(items) == 2  # third entry has no content → skipped
    assert items[0].source_ref == "rewind-2026-09-01"
    assert items[0].source_url == "https://example.com/d"
    assert items[0].tags == ["rewind"]
    assert items[0].captured_at == datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    assert items[1].title is None  # untitled note


def test_parse_generic_pam_bundle():
    items = parse_generic(PAM_SAMPLE)
    assert len(items) == 2
    first = items[0]
    assert first.title == "[skill] User is a cloud infrastructure engineer"
    assert first.source_ref == "mem-001"
    assert first.tags == ["skill"]
    assert first.metadata["pam"] is True
    assert first.metadata["platform"] == "chatgpt"
    assert first.captured_at == datetime(2025, 1, 15, tzinfo=UTC)


def test_detect_format():
    assert detect_format(CHATGPT_SAMPLE) == "chatgpt"
    assert detect_format(CLAUDE_SAMPLE) == "claude"
    assert detect_format(GENERIC_SAMPLE) == "generic"
    assert detect_format(PAM_SAMPLE) == "generic"  # PAM rides the generic path
    assert detect_format([]) == "unknown"
    assert detect_format({"stray": 1}) == "unknown"


def test_parse_import_truncates_long_content():
    payload = [{"content": "x" * (MAX_CONTENT_CHARS + 500)}]
    items = parse_import("generic", payload)
    assert len(items) == 1
    assert len(items[0].content) == MAX_CONTENT_CHARS  # exactly at the cap
    assert items[0].content.endswith(TRUNCATION_MARKER)


def test_parse_import_unknown_format_rejected():
    with pytest.raises(ImportFormatError, match="unknown source_format"):
        parse_import("rewind", [{"content": "x"}])
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/ingestion/test_import_formats.py -v` → FAIL (ImportError: cannot import name `parse_claude` …).
- [ ] **Step 3: Implement** — append to `app/ingestion/import_formats.py`:

```python
def parse_claude(data: Any) -> list[ImportItem]:
    """Claude conversations.json (JSON array) → one ImportItem per conversation.

    Verified shape (PAM importer-mappings §2): messages live in
    ``chat_messages`` (NOT ``messages``) as a flat linear array; senders are
    ``"human"``/``"assistant"``; the message-level ``text`` is the plain-text
    duplicate of the content[] text parts. thinking/tool_use/tool_result
    blocks are model plumbing, not user knowledge — dropped in v0.
    """
    if not isinstance(data, list):
        raise ImportFormatError(
            "Claude export must be the conversations.json JSON array "
            "(claude.ai Settings → Privacy → Export data)."
        )
    items: list[ImportItem] = []
    for conversation in data:
        if not isinstance(conversation, dict):
            continue
        lines: list[str] = []
        for message in conversation.get("chat_messages") or []:
            if not isinstance(message, dict):
                continue
            sender = message.get("sender")
            text = str(message.get("text") or "").strip()
            if not text or sender not in ("human", "assistant"):
                continue
            lines.append(f"{'User' if sender == 'human' else 'Assistant'}: {text}")
        if not lines:
            continue
        items.append(
            ImportItem(
                title=_clip(conversation.get("name"), 500) or "Untitled Claude conversation",
                content="\n\n".join(lines),
                source_ref=_clip(conversation.get("uuid"), 500),
                captured_at=_to_utc_datetime(conversation.get("created_at")),
                tags=["claude"],
                metadata={"import_format": "claude"},
            )
        )
    return items


def _parse_pam(data: dict) -> list[ImportItem]:
    """PAM memory-store.json → one ImportItem per memory (generic path).

    PAM memories carry no title (content is the payload), so synthesize
    ``[<type>] <content preview>``. Relations/conversations companions are
    out of scope for v0.
    """
    items: list[ImportItem] = []
    for memory in data.get("memories") or []:
        if not isinstance(memory, dict):
            continue
        content = str(memory.get("content") or "").strip()
        if not content:
            continue
        mem_type = str(memory.get("type") or "memory")
        provenance = memory.get("provenance") or {}
        items.append(
            ImportItem(
                title=_clip(f"[{mem_type}] {content[:120]}", 500),
                content=content,
                source_ref=_clip(memory.get("id"), 500),
                captured_at=_to_utc_datetime((memory.get("temporal") or {}).get("created_at")),
                tags=[mem_type],
                metadata={
                    "import_format": "generic",
                    "pam": True,
                    "platform": provenance.get("platform"),
                },
            )
        )
    return items


def parse_generic(data: Any) -> list[ImportItem]:
    """Generic JSON → ImportItems.

    Accepts either a PAM ``memory-store.json`` (dict with
    ``schema == "portable-ai-memory"``) or a JSON array of
    ``{title?, content, created_at?, url?, ref?, tags?}`` items — the shape
    any provider (or an OpenRecall sqlite dump, see docs) can be reduced to.
    """
    if isinstance(data, dict) and data.get("schema") == "portable-ai-memory":
        return _parse_pam(data)
    if not isinstance(data, list):
        raise ImportFormatError(
            "Generic import must be a JSON array of "
            "{title?, content, created_at?, url?, ref?, tags?} items "
            "or a PAM memory-store.json object."
        )
    items: list[ImportItem] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        content = str(entry.get("content") or "").strip()
        if not content:
            continue
        items.append(
            ImportItem(
                title=_clip(entry.get("title"), 500),
                content=content,
                source_ref=_clip(entry.get("ref"), 500),
                source_url=_clip(entry.get("url"), 1000),
                captured_at=_to_utc_datetime(entry.get("created_at")),
                tags=[str(t) for t in (entry.get("tags") or []) if str(t).strip()][:50],
                metadata={"import_format": "generic"},
            )
        )
    return items


def detect_format(data: Any) -> str:
    """Best-effort provider detection (PAM spec §9 heuristics, verified).

    Keys off the first array element: ``mapping`` → chatgpt,
    ``chat_messages`` → claude, ``content`` → generic; a dict with the PAM
    ``schema`` marker → generic.
    """
    if isinstance(data, list):
        sample = data[0] if data else {}
        if isinstance(sample, dict):
            if "mapping" in sample:
                return "chatgpt"
            if "chat_messages" in sample:
                return "claude"
            if "content" in sample:
                return "generic"
    if isinstance(data, dict) and data.get("schema") == "portable-ai-memory":
        return "generic"
    return "unknown"


_PARSERS: dict[str, Any] = {
    "chatgpt": parse_chatgpt,
    "claude": parse_claude,
    "generic": parse_generic,
}


def parse_import(source_format: str, data: Any) -> list[ImportItem]:
    """Parse per a CONCRETE ``source_format`` (the service resolves ``auto``
    first) and cap every item's content to exactly ``MAX_CONTENT_CHARS``.
    """
    try:
        parser = _PARSERS[source_format]
    except KeyError:
        raise ImportFormatError(
            f"unknown source_format: {source_format!r} (supported: {SOURCE_FORMATS})"
        ) from None
    items = parser(data)
    for item in items:
        if len(item.content) > MAX_CONTENT_CHARS:
            keep = MAX_CONTENT_CHARS - len(TRUNCATION_MARKER)
            item.content = item.content[:keep] + TRUNCATION_MARKER
    return items


__all__ = [
    "MAX_CONTENT_CHARS",
    "SOURCE_FORMATS",
    "SOURCE_TYPE_FOR_FORMAT",
    "TRUNCATION_MARKER",
    "ImportFormatError",
    "ImportItem",
    "detect_format",
    "parse_chatgpt",
    "parse_claude",
    "parse_generic",
    "parse_import",
]
```

- [ ] **Step 4: Run to verify it passes** — `pytest tests/ingestion/test_import_formats.py -v` → PASS (all Task 1 + Task 2 tests green).
- [ ] **Step 5: Lint + commit** — `ruff check app tests && pytest tests/ingestion -q` → green; `git commit -m "feat: claude/generic/PAM import adapters + format detection"`.

---

### Task 3: Import service — dedup, batched `Memory` creation, best-effort indexing

**Files:**
- Create: `app/services/import_service.py`
- Modify: `app/schemas/Orivory.py` (add `ImportSummary` after `MemoryUpdate`, before `MemoryEntityLink` — follow the file's field-alignment style)
- Test: `tests/services/test_import_service.py`

**Interfaces:**
- Consumes: `parse_import`, `detect_format`, `SOURCE_TYPE_FOR_FORMAT`, `ImportFormatError` (Tasks 1–2); `Memory` model; `index_new_memory` (`app/retrieval/memory/write_back.py`).
- Produces:
  - `ImportSummary` (Pydantic, in `app/schemas/Orivory.py`): `source_format: str`, `detected_format: str`, `filename: str`, `total_items: int`, `created: int`, `skipped_duplicates: int`, `failed: int`, `errors: list[str] = []`.
  - `async run_import(db: AsyncSession, user_id: uuid.UUID, source_format: str, filename: str, data: bytes) -> ImportSummary` — raises `ImportFormatError` for non-JSON input or an undetectable format; per-item problems are isolated into `failed`/`errors` (house pattern: `SourceSyncService`). Dedups against existing rows (one `Memory.source_ref.in_(refs)` query scoped to `user_id` + `source_type`) and within the file; single commit; `refresh` each created row (server defaults must load before indexing); then `await index_new_memory(memory)` per created row (never raises).

- [ ] **Step 1: Write the failing test** — `tests/services/test_import_service.py`:

```python
"""Unit tests for the import service — fake DB, monkeypatched indexing.

CI-safe: the single dedup select is answered by a fake returning refs
(pattern: tests/services/test_erasure_service.py); index_new_memory is
patched with a recorder (no Chroma).
"""
from __future__ import annotations

import json
import uuid

import pytest

from app.ingestion.import_formats import ImportFormatError
from app.services import import_service
from app.services.import_service import run_import

CHATGPT_PAYLOAD = [
    {
        "id": "c1",
        "title": "First",
        "create_time": 1738454400.0,
        "mapping": {
            "u": {"message": {"author": {"role": "user"}, "create_time": 1.0,
                              "content": {"parts": ["hello"]}}},
            "a": {"message": {"author": {"role": "assistant"}, "create_time": 2.0,
                              "content": {"parts": ["hi there"]}}},
        },
    },
    {
        "id": "c2",
        "title": "Second",
        "create_time": 1738454500.0,
        "mapping": {
            "u": {"message": {"author": {"role": "user"}, "create_time": 1.0,
                              "content": {"parts": ["second conv"]}}},
        },
    },
]


class _FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    """Answers the single dedup select run_import issues."""

    def __init__(self, existing_refs=()):
        self._existing_refs = list(existing_refs)
        self.added = []
        self.committed = 0
        self.refreshed = []

    async def execute(self, _stmt):
        return _FakeRows(self._existing_refs)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1

    async def refresh(self, obj):
        self.refreshed.append(obj)


@pytest.fixture()
def indexed(monkeypatch):
    calls: list = []

    async def _fake_index(memory):
        calls.append(memory)

    monkeypatch.setattr(import_service, "index_new_memory", _fake_index)
    return calls


def _payload_bytes(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


async def test_run_import_creates_and_indexes(indexed):
    db = _FakeDB()
    summary = await run_import(db, uuid.uuid4(), "chatgpt", "conversations.json", _payload_bytes(CHATGPT_PAYLOAD))
    assert summary.created == 2
    assert summary.detected_format == "chatgpt"
    assert summary.source_format == "chatgpt"
    assert summary.total_items == 2
    assert summary.skipped_duplicates == 0
    assert summary.failed == 0
    assert len(db.added) == 2
    memory = db.added[0]
    assert memory.source_type == "chatgpt_import"
    assert memory.source_ref == "c1"
    assert memory.title == "First"
    assert memory.tags == ["chatgpt"]
    assert memory.captured_at.tzinfo is not None
    assert memory.extra_metadata["import"] == {"file": "conversations.json"}
    assert db.committed == 1
    assert len(db.refreshed) == 2
    assert indexed == db.added  # every created row indexed exactly once, in order


async def test_run_import_dedups_against_db_and_within_file(indexed):
    db = _FakeDB(existing_refs=["c1"])
    summary = await run_import(db, uuid.uuid4(), "chatgpt", "f.json", _payload_bytes(CHATGPT_PAYLOAD))
    assert summary.created == 1          # only c2
    assert summary.skipped_duplicates == 1  # c1 already in db
    assert [m.source_ref for m in db.added] == ["c2"]


async def test_run_import_auto_detects_claude(indexed):
    claude_payload = [{
        "uuid": "k1",
        "name": "Conv",
        "created_at": "2026-01-20T09:15:00Z",
        "chat_messages": [{"uuid": "m1", "sender": "human", "text": "hi"}],
    }]
    db = _FakeDB()
    summary = await run_import(db, uuid.uuid4(), "auto", "conversations.json", _payload_bytes(claude_payload))
    assert summary.source_format == "auto"
    assert summary.detected_format == "claude"
    assert db.added[0].source_type == "claude_import"


async def test_run_import_rejects_non_json():
    with pytest.raises(ImportFormatError, match="not valid UTF-8 JSON"):
        await run_import(_FakeDB(), uuid.uuid4(), "generic", "bad.json", b"{not json")


async def test_run_import_rejects_undetectable_format():
    with pytest.raises(ImportFormatError, match="could not detect"):
        await run_import(_FakeDB(), uuid.uuid4(), "auto", "x.json", _payload_bytes({"stray": 1}))


async def test_run_import_isolates_failed_items(indexed, monkeypatch):
    class _BoomMemory:
        def __init__(self, **kwargs):
            if kwargs.get("source_ref") == "c2":
                raise ValueError("simulated row failure")
            for key, value in kwargs.items():
                setattr(self, key, value)

    monkeypatch.setattr(import_service, "Memory", _BoomMemory)
    db = _FakeDB()
    summary = await run_import(db, uuid.uuid4(), "chatgpt", "f.json", _payload_bytes(CHATGPT_PAYLOAD))
    assert summary.created == 1
    assert summary.failed == 1
    assert summary.errors == ["simulated row failure"]
    assert db.committed == 1  # the good row still commits
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/services/test_import_service.py -v` → FAIL (ImportError on `app.services.import_service`).
- [ ] **Step 3: Add `ImportSummary` to `app/schemas/Orivory.py`** (follow the file's alignment style; place after `MemoryUpdate`):

```python
class ImportSummary(BaseModel):
    """Result of one import run (POST /api/v1/imports)."""
    source_format:       str
    detected_format:     str
    filename:            str
    total_items:         int
    created:             int
    skipped_duplicates:  int
    failed:              int
    errors:              list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement** — `app/services/import_service.py`:

```python
"""One-shot memory import service (Open Memory Hub MVP item 3).

Turns an uploaded provider export file into Memory rows: parse (adapters)
→ resolve/detect format → dedup on (user_id, source_type, source_ref) →
create rows → single commit → best-effort indexing (embed + graph enqueue
via write_back — Postgres is the source of truth, indexing never raises).

v0 is synchronous and bounded by the router's 20 MiB upload cap; large
imports move to a Celery task later (docs/API.md §Imports, follow-ups).
"""
from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.import_formats import (
    SOURCE_TYPE_FOR_FORMAT,
    ImportFormatError,
    detect_format,
    parse_import,
)
from app.models.memory import Memory
from app.retrieval.memory.write_back import index_new_memory
from app.schemas.Orivory import ImportSummary

log = logging.getLogger(__name__)

MAX_ERRORS_KEPT = 50


async def run_import(
    db: AsyncSession,
    user_id: uuid.UUID,
    source_format: str,
    filename: str,
    data: bytes,
) -> ImportSummary:
    """Import one export file for one user.

    Raises ``ImportFormatError`` for undecodable JSON or an undetectable
    format; per-item problems are isolated into failed/errors instead of
    failing the whole run (house pattern: SourceSyncService).
    """
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportFormatError(f"file {filename!r} is not valid UTF-8 JSON: {exc}") from exc

    detected = source_format if source_format != "auto" else detect_format(parsed)
    if detected not in SOURCE_TYPE_FOR_FORMAT:
        raise ImportFormatError(
            "could not detect the export format — pass source_format "
            "explicitly (chatgpt | claude | generic)"
        )

    items = parse_import(detected, parsed)
    source_type = SOURCE_TYPE_FOR_FORMAT[detected]

    # Dedup part 1: refs this user already imported from this format.
    # Query-based (like SourceSyncService) — memories has no unique index.
    refs = [item.source_ref for item in items if item.source_ref]
    existing_refs: set[str] = set()
    if refs:
        rows = (
            await db.execute(
                select(Memory.source_ref).where(
                    Memory.user_id == user_id,
                    Memory.source_type == source_type,
                    Memory.source_ref.in_(refs),
                )
            )
        ).scalars().all()
        existing_refs = {row for row in rows if row}

    created_rows: list[Memory] = []
    seen_refs: set[str] = set()
    skipped_duplicates = 0
    failed = 0
    errors: list[str] = []

    # Dedup part 2: within the same file.
    for item in items:
        try:
            if item.source_ref and (item.source_ref in existing_refs or item.source_ref in seen_refs):
                skipped_duplicates += 1
                continue
            memory = Memory(
                user_id=user_id,
                title=item.title,
                content=item.content,  # already capped by parse_import
                source_type=source_type,
                source_ref=item.source_ref,
                source_url=item.source_url,
                tags=item.tags,
                captured_at=item.captured_at,
                extra_metadata={**item.metadata, "import": {"file": filename}},
            )
            db.add(memory)
            created_rows.append(memory)
            if item.source_ref:
                seen_refs.add(item.source_ref)
        except Exception as exc:  # per-item isolation; the run continues
            failed += 1
            if len(errors) < MAX_ERRORS_KEPT:
                errors.append(str(exc))
            log.warning(
                "Import item failed",
                extra={"user_id": str(user_id), "file": filename, "error": str(exc)},
            )

    if created_rows:
        await db.commit()
        # Server-side defaults (id, timestamps) must load before indexing.
        for memory in created_rows:
            await db.refresh(memory)
        # Best-effort embed + graph enqueue — index_new_memory never raises.
        for memory in created_rows:
            await index_new_memory(memory)

    return ImportSummary(
        source_format=source_format,
        detected_format=detected,
        filename=filename,
        total_items=len(items),
        created=len(created_rows),
        skipped_duplicates=skipped_duplicates,
        failed=failed,
        errors=errors[:MAX_ERRORS_KEPT],
    )


__all__ = ["MAX_ERRORS_KEPT", "run_import"]
```

- [ ] **Step 5: Run to verify it passes** — `pytest tests/services/test_import_service.py -v` → PASS (6 tests).
- [ ] **Step 6: Lint + commit** — `ruff check app tests && pytest tests/services tests/ingestion -q` → green; `git commit -m "feat: one-shot import service (dedup + batched create + best-effort indexing)"`.

---

### Task 4: `POST /api/v1/imports` router + source_type Literals + wiring

**Files:**
- Create: `app/api/v1/imports.py`
- Modify: `app/api/v1/router.py` (import `imports`, include its router)
- Modify: `app/schemas/Orivory.py:15-17` (`MemoryCreate.source_type` Literal gains the three import values)
- Modify: `app/api/v1/memories.py:115-116` (`list_memories` `source_type` filter Literal gains the same three values)
- Modify: `tests/api/test_router_wiring.py` (append `"app.api.v1.imports"` to `ROUTERS_TO_CHECK`)
- Test: `tests/api/test_imports_router.py`

**Interfaces:**
- Consumes: `run_import`, `ImportSummary`, `ImportFormatError` (Tasks 1–3); `get_current_verified_user`, `get_db`.
- Produces REST API:
  - `POST /api/v1/imports` — multipart `file` (JSON export) + form `source_format` (`auto` default) → 201 `ImportSummary`. 422 on empty file / non-JSON / unknown+undetectable format; 413 over `MAX_IMPORT_UPLOAD_BYTES = 20 * 1024 * 1024`. Multipart is already supported (`python-multipart` in `pyproject.toml`; `chat.py` uses `UploadFile` today).
  - `Memory.source_type` values `chatgpt_import` / `claude_import` / `generic_import` become legal in `POST /api/v1/memories` and in the `GET /api/v1/memories` filter.

- [ ] **Step 1: Write the failing test** — `tests/api/test_imports_router.py`:

```python
"""Wiring tests for the imports router — CI-safe, no live DB."""
from __future__ import annotations

import typing

from fastapi.routing import APIRoute

from app.api.v1.imports import MAX_IMPORT_UPLOAD_BYTES, router


def test_imports_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/imports" in paths


def test_import_upload_cap_is_20mib():
    assert MAX_IMPORT_UPLOAD_BYTES == 20 * 1024 * 1024


def test_import_summary_response_shape():
    from app.schemas.Orivory import ImportSummary

    fields = set(ImportSummary.model_fields)
    assert {
        "source_format", "detected_format", "filename", "total_items",
        "created", "skipped_duplicates", "failed", "errors",
    } <= fields


def test_memory_create_source_types_include_imports():
    from app.schemas.Orivory import MemoryCreate

    annotation = MemoryCreate.model_fields["source_type"].annotation
    values = typing.get_args(annotation)
    for source_type in ("chatgpt_import", "claude_import", "generic_import"):
        assert source_type in values


def _literal_values(annotation) -> tuple:
    """Unwrap Optional[Literal[...]] → the Literal's values."""
    for arg in typing.get_args(annotation):
        if typing.get_origin(arg) is typing.Literal:
            return typing.get_args(arg)
    return ()


def test_memories_list_filter_includes_import_types():
    from app.api.v1.memories import list_memories

    hints = typing.get_type_hints(list_memories)
    values = _literal_values(hints["source_type"])
    for source_type in ("chatgpt_import", "claude_import", "generic_import"):
        assert source_type in values
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/api/test_imports_router.py -v` → FAIL (ImportError on `app.api.v1.imports`).
- [ ] **Step 3: Extend the Literals** — in `app/schemas/Orivory.py` change `MemoryCreate.source_type` (lines 15-17) from:

```python
    source_type:   Literal["manual_note", "file_upload", "google_drive", "notion",
                            "gmail", "web_clipper", "rss", "conversation_excerpt", "other"] = "manual_note"
```

to:

```python
    source_type:   Literal["manual_note", "file_upload", "google_drive", "notion",
                            "gmail", "web_clipper", "rss", "conversation_excerpt",
                            "chatgpt_import", "claude_import", "generic_import", "other"] = "manual_note"
```

and in `app/api/v1/memories.py` change the `list_memories` `source_type` parameter (lines 115-116) from:

```python
    source_type: Literal["manual_note", "file_upload", "google_drive", "notion",
                          "gmail", "web_clipper", "rss", "conversation_excerpt", "other"] | None = None,
```

to:

```python
    source_type: Literal["manual_note", "file_upload", "google_drive", "notion",
                          "gmail", "web_clipper", "rss", "conversation_excerpt",
                          "chatgpt_import", "claude_import", "generic_import", "other"] | None = None,
```

Both must list the same three values as `SOURCE_TYPE_FOR_FORMAT` (locked by `test_source_type_mapping_locked` in Task 1).

- [ ] **Step 4: Implement the router** — `app/api/v1/imports.py`:

```python
"""Imports API — one-shot provider export imports (Open Memory Hub MVP 3).

Endpoint:
    POST /api/v1/imports    upload an export file (JSON) + source_format
                            → ImportSummary {created, skipped_duplicates, failed}

v0 is synchronous and capped at 20 MiB per upload; larger imports move to a
Celery task in a later plan (docs/API.md §Imports). Format claims and
export paths are verified against the PAM importer mappings — see
docs/API.md §Imports for the source list.
"""
from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ingestion.import_formats import ImportFormatError
from app.models.user import User
from app.schemas.Orivory import ImportSummary
from app.services.import_service import run_import
from app.utils.dependencies import get_current_verified_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_IMPORT_UPLOAD_BYTES = 20 * 1024 * 1024  # keeps the v0 path synchronous


@router.post("", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile = File(..., description="Export file (JSON): ChatGPT/Claude conversations.json, "
                                              "PAM memory-store.json, or a generic items array"),
    source_format: Annotated[Literal["auto", "chatgpt", "claude", "generic"], Form()] = "auto",
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportSummary:
    """Import one export file as memories.

    Auto-detects the format when ``source_format=auto``. Idempotent per
    (user, format, ref): re-uploading a file skips already-imported items
    instead of duplicating them.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file is empty.")
    if len(data) > MAX_IMPORT_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Import file exceeds the {MAX_IMPORT_UPLOAD_BYTES // (1024 * 1024)} MiB synchronous cap.",
        )
    filename = file.filename or "upload"
    try:
        summary = await run_import(db, current_user.id, source_format, filename, data)
    except ImportFormatError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    log.info(
        "Import finished",
        extra={
            "user_id": str(current_user.id),
            "file": filename,
            "format": summary.detected_format,
            "created": summary.created,
            "duplicates": summary.skipped_duplicates,
        },
    )
    return summary
```

(The dependency parameters above follow the bare-`Depends` house style from `app/api/v1/erasure.py:37-38` — no `= None` defaults. `Depends(...)` in defaults would be allowed by the repo's ruff `B008` ignore, but the house pattern passes them bare.)

- [ ] **Step 5: Wire the router** — in `app/api/v1/router.py` add `imports` to the `from app.api.v1 import (...)` list (alphabetical, after `insights`) and `api_router.include_router(imports.router)` after the `sources.router` line. Append `"app.api.v1.imports"` to `ROUTERS_TO_CHECK` in `tests/api/test_router_wiring.py`.
- [ ] **Step 6: Run to verify it passes** — `pytest tests/api/test_imports_router.py tests/api/test_router_wiring.py -v` → PASS.
- [ ] **Step 7: Smoke the endpoint signature resolves** — `python -c "from app.main import app; print([r.path for r in app.routes if 'import' in getattr(r, 'path', '')])"` → prints `['/api/v1/imports']` (plus any `/imports`-prefixed paths).
- [ ] **Step 8: Lint + commit** — `ruff check app tests && pytest tests/api tests/ingestion tests/services -q` → green; `git commit -m "feat: POST /api/v1/imports (one-shot export upload → memories)"`.

---

### Task 5: Docs — API section, README feature row, one-pager status

**Files:**
- Modify: `docs/API.md` (new `## 15. Imports` section after `## 14. Erasure Receipts`, before `## Appendix A`)
- Modify: `README.md` (Key Features table row, after `Multi-Source Ingestion`)
- Modify: `docs/ideas/open-memory-hub.md` (MVP item 3 status)

- [ ] **Step 1: Add the API.md section** — insert this content as `## 15. Imports` (update the doc's Table of Contents to list it):

```markdown
## 15. Imports (One-Shot Memory Imports)

Import a provider data export into your memory store in one request. v0
covers JSON exports; each import is idempotent per item — re-uploading the
same file skips what it already imported.

### POST /api/v1/imports

`multipart/form-data`:

| Field | Type | Notes |
|-------|------|-------|
| `file` | file | The export file (JSON, ≤ 20 MiB) |
| `source_format` | string | `auto` (default) \| `chatgpt` \| `claude` \| `generic` |

Response `201`:

```json
{
  "source_format": "auto",
  "detected_format": "chatgpt",
  "filename": "conversations.json",
  "total_items": 128,
  "created": 120,
  "skipped_duplicates": 8,
  "failed": 0,
  "errors": []
}
```

Example:

```bash
curl -X POST http://localhost:8000/api/v1/imports \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@conversations.json" \
  -F "source_format=chatgpt"
```

### Supported formats

| source_format | File | How to get it | Verified shape |
|---------------|------|---------------|----------------|
| `chatgpt` | `conversations.json` | ChatGPT Settings → Data controls → Export data (ZIP arrives by email) | JSON array; `title`, `create_time` (unix float), `mapping` DAG of messages (`author.role`, `content.parts[]` with nulls) |
| `claude` | `conversations.json` | claude.ai Settings → Privacy → Export data | JSON array; `name`, `created_at` (ISO 8601), `chat_messages[]` with `sender` `human`/`assistant` and message-level `text` |
| `generic` | any items array, or a PAM `memory-store.json` | your own export/dump | `[{title?, content, created_at?, url?, ref?, tags?}]` or PAM v1.0 (`schema: "portable-ai-memory"`) |

Semantics:

- `auto` detection keys off the first array element (`mapping` → chatgpt,
  `chat_messages` → claude, `content` → generic) and the PAM `schema` marker.
- Each conversation becomes **one** memory (transcript `User: … / Assistant: …`),
  content capped at 10 000 chars (`[import truncated]` marker); system,
  thinking and tool blocks are dropped.
- Import `source_type` values on the created memories: `chatgpt_import`,
  `claude_import`, `generic_import` — filter them with
  `GET /api/v1/memories?source_type=chatgpt_import`.
- Dedup key: `(user, source_type, source_ref)`; a re-import skips items it
  already created.
- Errors: `413` over 20 MiB; `422` on empty file, non-JSON, or an
  unrecognized/undetectable format.

Format sources (verified Feb 2026 — providers change export formats
without notice): PAM importer mappings
(https://github.com/portable-ai-memory/portable-ai-memory/blob/master/importer-mappings.md),
PAM spec v1.0 (https://portable-ai-memory.org/spec/v1.0/), OpenAI export
help (https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data).

### OpenRecall (v0 recipe)

OpenRecall stores history in a local SQLite table
`entries(id, app, title, text, timestamp, embedding)` (unix seconds).
Dump it to the generic shape and import (Linux path shown; macOS:
`~/Library/Application Support/openrecall/`):

```bash
sqlite3 ~/.local/share/openrecall/openrecall.db \
  "SELECT json_group_array(json_object('ref','openrecall-'||id,'title',app||' — '||title,'content',text,'created_at',datetime(timestamp,'unixepoch'))) FROM entries WHERE text IS NOT NULL AND trim(text)<>'';" \
  > openrecall.json
curl -X POST http://localhost:8000/api/v1/imports \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@openrecall.json" -F "source_format=generic"
```

A native `.db` upload adapter is a follow-up.

### Rewind.ai / Limitless (not in v0 — honest status)

Rewind stopped recording on 2025-12-19 (Meta acquisition). Its history
lives in a SQLCipher-encrypted local SQLite database with **no official
export format**; community tools decrypt it locally. Orivory v0 does not
guess this format — a dedicated adapter ships only after that pipeline is
verified. Meanwhile, any tool that can produce the generic JSON shape
above can import.

### What is NOT imported (v0)

- ChatGPT's "Memory" feature contents — not included in the data export
  (verified gap in the PAM mappings).
- Gemini (Google Takeout `MyActivity.json`) and Copilot (Privacy Dashboard
  CSV) — formats verified in the PAM mappings; adapters are follow-ups.
- Claude `memories.json` / `projects.json` / `users.json` — v0 imports
  conversations only.
```

- [ ] **Step 2: README Key Features row** — add after the `Multi-Source Ingestion` row in the table at `README.md:39`:

```markdown
| **📥 Memory Imports** | One-shot import of ChatGPT / Claude / PAM / generic JSON exports as searchable memories |
```

- [ ] **Step 3: One-pager status** — in `docs/ideas/open-memory-hub.md` MVP list, change item 3 from `3. **Import paths** — …` to:

```markdown
3. ✅ **Import paths** — Rewind/Limitless/OpenRecall exports; ChatGPT/Claude/Gemini memory exports (PAM mappings). (backend v0 done 2026-09-02: ChatGPT/Claude/generic+PAM JSON via `POST /api/v1/imports`; Rewind adapter blocked on format verification — encrypted sqlite, no official export; OpenRecall via documented generic dump recipe; UI + Celery + Gemini/Copilot adapters = follow-ups)
```

- [ ] **Step 4: Full verification** — `ruff check app tests && pytest -q` (the CI-safe suite) → all green.
- [ ] **Step 5: Commit** — `git commit -m "docs: memory imports API (formats, sources, dedup semantics) + one-pager status"`.

---

## Follow-ups (explicitly NOT in this plan)

- **Celery task for large imports** — files over the 20 MiB sync cap (or item counts over a few hundred): store the upload, enqueue a task in `app/tasks/` (register in `celery_app.py` `include` + `task_routes`), add a progress/result endpoint. The service is already a pure `db`-in/summary-out function, so the task wraps it with a sync session.
- **Rewind.ai/Limitless dedicated adapter** — blocked on format verification: data sits in a SQLCipher-encrypted local SQLite (`~/Library/Application Support/com.memoryvault.MemoryVault/db-enc.sqlite3`, per RewindMCP's schema docs), app sunset 2025-12-19, no official export. Needs a documented user-side decryption step (sqlcipher CLI) and a mapping of the ~55-table schema (RewindMCP README-SCHEMA.md documents the main ones: `frame`, `node`, `segment`, `event`, `transcript_word`). Do NOT accept encrypted blobs blind.
- **OpenRecall native adapter** — accept the sqlite `.db` file directly (stdlib `sqlite3` can read from bytes) instead of the manual JSON dump; schema already verified (`entries` table).
- **Gemini + Copilot adapters** — formats verified in PAM importer-mappings.md §3–§4 (Takeout `MyActivity.json` has two variants: `details[]` and `userInteractions[]`; Copilot is CSV with two column layouts — CSV support is new parsing surface, not just another JSON adapter).
- **Claude `memories.json`** (`conversations_memory` + `project_memories`) — v0 imports conversations only; memory blocks are a natural next adapter.
- **Import UI** in `frontend/` — file picker, format dropdown with auto, summary screen.
- **PAM `conversations/*.json` companion files** (§25 normalized conversations) — v0 imports `memories[]` only.
- **Per-exchange granularity** — one memory per user/assistant exchange pair instead of per conversation, for finer recall; only worth it after real usage feedback on the 10k-char transcripts.
