"""
Imports API — one-shot provider export imports (Open Memory Hub MVP 3).

Endpoint:
    POST /api/v1/imports    multipart upload: file (export JSON) + optional
                            source_format form field → 201 ImportSummary
                            {parsed, created, skipped_duplicates, failed,
                            index_failures}

v0 is synchronous and capped at 20 MiB per upload; larger imports move to a
Celery task in a later plan (docs/API.md §Imports). Format claims and
export paths are verified against the PAM importer mappings — see
docs/API.md §Imports for the source list.

Honest limits of the v0 read-then-check window: the request body is fully
read before the 20 MiB cap check — hostile clients can force a large read
(Starlette spools file parts over 1 MiB to disk, which bounds the memory
blast radius but not the read itself); a streaming/chunked cap is the
hardening follow-up. The Content-Length header check below is only a
best-effort early reject — the authoritative gate stays read-then-check
because a lying/absent header must not bypass it.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ingestion.import_formats import SOURCE_FORMATS, ImportFormatError
from app.models.user import User
from app.schemas.Orivory import ImportSummary
from app.services.import_service import run_import
from app.utils.dependencies import get_current_verified_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_IMPORT_UPLOAD_BYTES = 20 * 1024 * 1024  # keeps the v0 path synchronous


@router.post("", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
async def create_import(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(..., description="Export file (JSON): ChatGPT/Claude "
                                              "conversations.json, PAM memory-store.json, "
                                              "or a generic items array"),
    source_format: str | None = Form(default=None, description="One of: auto (default), "
                                                                "chatgpt, claude, generic"),
    request: Request = None,  # best-effort Content-Length early reject (see module docstring)
) -> ImportSummary:
    """Import one export file as memories.

    Auto-detects the format when ``source_format=auto`` (or is omitted).
    Idempotent per (user, format, ref): re-uploading a file skips
    already-imported items instead of duplicating them.
    """
    # A blank form field and an omitted one mean the same thing: auto-detect.
    # (curl's -F "source_format=" and stray client whitespace must not 422.)
    if isinstance(source_format, str) and not source_format.strip():
        source_format = None

    # Pre-validate an explicit format before reading/decoding anything —
    # an unknown value must fail here, not as a misleading "could not
    # detect" from the service (it IS detectable input that was mislabeled).
    if source_format is not None and source_format not in SOURCE_FORMATS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unknown source_format: {source_format!r} (supported: {SOURCE_FORMATS})",
        )

    # Best-effort early reject on an over-cap Content-Length header: cheap
    # (no read), but not authoritative — the header can lie or be absent,
    # so the len(data) check below remains the gate.
    if request is not None:
        header = request.headers.get("content-length", "").strip()
        if header.isdigit() and int(header) > MAX_IMPORT_UPLOAD_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(f"Content-Length {header} exceeds the "
                        f"{MAX_IMPORT_UPLOAD_BYTES // (1024 * 1024)} MiB synchronous import cap."),
            )

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file is empty.")
    if len(data) > MAX_IMPORT_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Import file exceeds the {MAX_IMPORT_UPLOAD_BYTES // (1024 * 1024)} MiB synchronous cap.",
        )

    # raw bytes, not a decoded str: run_import owns the utf-8 decode and
    # maps undecodable payloads to ImportFormatError → 422 (handoff 4).
    try:
        summary = await run_import(db, current_user.id, data, source_format, requested_by="rest_api")
    except ImportFormatError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    log.info(
        "Import finished",
        extra={
            "user_id": str(current_user.id),
            "file": file.filename or "upload",
            "source_format": source_format,
            "created": summary.created,
            "skipped_duplicates": summary.skipped_duplicates,
        },
    )
    return summary


__all__ = ["MAX_IMPORT_UPLOAD_BYTES", "router"]
