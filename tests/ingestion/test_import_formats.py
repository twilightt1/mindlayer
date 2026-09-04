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
    with pytest.raises(ImportFormatError, match=r"conversations\.json JSON array"):
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
