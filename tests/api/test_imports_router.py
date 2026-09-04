"""Wiring tests for the imports router — CI-safe, no live DB."""
from __future__ import annotations

import typing
import uuid
from types import SimpleNamespace

import pytest
from fastapi.routing import APIRoute

from app.api.v1.imports import MAX_IMPORT_UPLOAD_BYTES, create_import, router
from app.ingestion.import_formats import SOURCE_FORMATS


def test_imports_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/imports" in paths


def test_import_upload_cap_is_20mib():
    assert MAX_IMPORT_UPLOAD_BYTES == 20 * 1024 * 1024


def test_import_summary_response_shape():
    """Shipped 5-count schema (T3 binding rules) — the plan's old field
    set (detected_format/filename/errors/...) does not exist."""
    from app.schemas.Orivory import ImportSummary

    fields = set(ImportSummary.model_fields)
    assert fields == {"parsed", "created", "skipped_duplicates", "failed", "index_failures"}


async def test_router_prevalidates_unknown_source_format():
    """Handoff 3: unknown explicit source_format → 422 BEFORE the service
    runs (no misleading 'could not detect' error for explicitly-invalid
    input, and no service call at all)."""
    from fastapi import HTTPException

    class _RecordingDB:
        async def execute(self, stmt):  # pragma: no cover - must not be reached
            raise AssertionError("service must not run for an invalid source_format")

    file = SimpleNamespace(filename="x.json")
    with pytest.raises(HTTPException) as exc_info:
        # Call with the unknown format; body not yet read — validation
        # must fail before .read() or run_import is ever invoked.
        await create_import(
            file=file,
            source_format="not_a_format",
            current_user=SimpleNamespace(id=uuid.uuid4()),
            db=_RecordingDB(),
        )
    assert exc_info.value.status_code == 422
    assert "not_a_format" in str(exc_info.value.detail)


def test_router_prevalidation_target_locks_to_source_formats():
    """The pre-validation whitelist must be SOURCE_FORMATS itself (the
    single registry of accepted values), not a hand-copied Literal set
    that could drift from the ingestion layer."""
    from app.api.v1 import imports as imports_module

    assert imports_module.SOURCE_FORMATS is SOURCE_FORMATS


def test_memory_create_source_types_include_imports():
    """The three import source types must be legal in POST /api/v1/memories
    (brief Step 3; locked across tasks by test_source_type_mapping_locked)."""
    from app.schemas.Orivory import MemoryCreate

    annotation = MemoryCreate.model_fields["source_type"].annotation
    values = _literal_values(annotation)
    for source_type in ("chatgpt_import", "claude_import", "generic_import"):
        assert source_type in values


def test_memories_list_filter_includes_import_types():
    """GET /api/v1/memories?source_type= filter must accept the same three
    import values (brief Step 3)."""
    from app.api.v1.memories import list_memories

    hints = typing.get_type_hints(list_memories)
    values = _literal_values(hints["source_type"])
    for source_type in ("chatgpt_import", "claude_import", "generic_import"):
        assert source_type in values


async def test_router_rejects_empty_upload():
    from fastapi import HTTPException

    class _DB:  # pragma: no cover - never reached past the empty check
        pass

    class _File:
        filename = "empty.json"

        async def read(self) -> bytes:
            return b""

    with pytest.raises(HTTPException) as exc_info:
        await create_import(
            file=_File(),
            source_format="chatgpt",
            current_user=SimpleNamespace(id=uuid.uuid4()),
            db=_DB(),
        )
    assert exc_info.value.status_code == 422


async def test_router_rejects_oversized_upload():
    """413 over the 20 MiB cap — testable at wiring level with a fake file
    whose read() returns MAX+1 bytes (no network/DB needed)."""
    from fastapi import HTTPException

    class _File:
        filename = "big.json"

        async def read(self) -> bytes:
            return b"x" * (MAX_IMPORT_UPLOAD_BYTES + 1)

    class _DB:  # pragma: no cover - never reached past the size check
        pass

    with pytest.raises(HTTPException) as exc_info:
        await create_import(
            file=_File(),
            source_format="chatgpt",
            current_user=SimpleNamespace(id=uuid.uuid4()),
            db=_DB(),
        )
    assert exc_info.value.status_code == 413


async def test_router_rejects_undecodable_bytes():
    """Handoff 4: UnicodeDecodeError from the utf-8 decode of the uploaded
    bytes → 422, not a 500."""
    from fastapi import HTTPException

    class _File:
        filename = "bad.json"

        async def read(self) -> bytes:
            return b"\xff\xfe{}"  # invalid utf-8

    class _DB:  # pragma: no cover - never reached past the decode check
        pass

    with pytest.raises(HTTPException) as exc_info:
        await create_import(
            file=_File(),
            source_format="chatgpt",
            current_user=SimpleNamespace(id=uuid.uuid4()),
            db=_DB(),
        )
    assert exc_info.value.status_code == 422


async def test_router_maps_import_format_error_to_422():
    """Handoff 4: ImportFormatError raised by run_import → HTTP 422 with
    detail=str(exc) (service seam reached with a stubbed run_import)."""
    from fastapi import HTTPException

    from app.api.v1 import imports as imports_module
    from app.ingestion.import_formats import ImportFormatError

    class _File:
        filename = "garbage.json"

        async def read(self) -> bytes:
            return b"not json at all"

    class _DB:
        pass

    async def _boom(db, user_id, raw_data, source_format, *, requested_by):
        raise ImportFormatError("import payload is not valid UTF-8 JSON: boom")

    original = imports_module.run_import
    imports_module.run_import = _boom
    try:
        with pytest.raises(HTTPException) as exc_info:
            await create_import(
                file=_File(),
                source_format="chatgpt",
                current_user=SimpleNamespace(id=uuid.uuid4()),
                db=_DB(),
            )
    finally:
        imports_module.run_import = original
    assert exc_info.value.status_code == 422
    assert "not valid UTF-8 JSON" in str(exc_info.value.detail)


def _literal_values(annotation) -> tuple:
    """Unwrap Optional[Literal[...]] / Literal[...] → the Literal's values."""
    if typing.get_origin(annotation) is typing.Literal:
        return typing.get_args(annotation)
    for arg in typing.get_args(annotation):
        if typing.get_origin(arg) is typing.Literal:
            return typing.get_args(arg)
    return ()
