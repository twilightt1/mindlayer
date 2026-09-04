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
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
) -> ImportSummary:
    """Import one export file as memories.

    Auto-detects the format when ``source_format=auto`` (or is omitted).
    Idempotent per (user, format, ref): re-uploading a file skips
    already-imported items instead of duplicating them.
    """
    # Pre-validate an explicit format before reading/decoding anything —
    # an unknown value must fail here, not as a misleading "could not
    # detect" from the service (it IS detectable input that was mislabeled).
    if source_format is not None and source_format not in SOURCE_FORMATS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unknown source_format: {source_format!r} (supported: {SOURCE_FORMATS})",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file is empty.")
    if len(data) > MAX_IMPORT_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Import file exceeds the {MAX_IMPORT_UPLOAD_BYTES // (1024 * 1024)} MiB synchronous cap.",
        )
    try:
        raw_text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Uploaded file is not valid UTF-8: {exc}"
        ) from exc

    try:
        summary = await run_import(db, current_user.id, raw_text, source_format, requested_by="rest_api")
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
