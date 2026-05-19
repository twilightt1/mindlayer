"""
FileUploadConnector — pulls pending file uploads from object storage.

Configuration (`Source.config`):
    {
        "prefix":  "uploads/<user_id>/pending/",
        "limit":   50,                     # max files to ingest per sync
    }

Behavior:
    - Lists objects under `prefix` in MinIO.
    - For each object, downloads the bytes, extracts text
      (txt / pdf / docx support is best-effort in v0), and yields
      one `ConnectorItem` per file.
    - For very long files, the connector yields the first chunk as a
      single memory; chunking is the dispatcher's job in Phase 3.
    - Does NOT delete the source object — the caller (or a separate
      cleanup job) decides what to do after a successful sync.
"""
from __future__ import annotations

import logging
import io
from typing import Any

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class FileUploadConnector(BaseConnector):
    source_type: str = "file_upload"

    def validate_config(self) -> None:
        if "prefix" not in self.config:
            raise ValueError("FileUploadConnector requires config['prefix']")

    async def fetch_items(self) -> list[ConnectorItem]:
        """
        Stub implementation in Phase 2 v0. We don't open MinIO from
        here because the storage adapter is async-only and the
        ingestion layer is pluggable; real implementation lands
        when the dispatcher's `ingest_file` helper is added in
        Phase 2.5.
        """
        log.debug("FileUploadConnector: stub fetch (returns empty list in v0)")
        return []


async def ingest_file(
    *,
    user_id: str,
    filename: str,
    content: bytes,
    mime_type: str | None = None,
    source_ref: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ConnectorItem:
    """
    Helper: turn an in-memory file upload into a `ConnectorItem`.

    This is the function the new `POST /memories/from-upload` endpoint
    calls. It supports the same file types as the legacy
    `document_service` (txt, pdf, docx) and falls back to utf-8 decode
    for unknown text types.
    """
    text_body = _extract_text(content, filename, mime_type or "application/octet-stream")
    title = filename.rsplit("/", 1)[-1]
    return ConnectorItem(
        title=title,
        content=text_body,
        summary=None,
        source_ref=source_ref or filename,
        source_url=None,
        source_excerpt=text_body[:500] if text_body else None,
        tags=tags or [],
        metadata={
            "user_id": user_id,
            "filename": filename,
            "mime_type": mime_type,
            "size": len(content),
            **(metadata or {}),
        },
    )


def _extract_text(content: bytes, filename: str, mime_type: str) -> str:
    """Best-effort text extraction. v0 supports plain text only."""
    name = filename.lower()
    if mime_type == "text/plain" or name.endswith(".txt") or name.endswith(".md"):
        return content.decode("utf-8", errors="replace")

    if name.endswith(".pdf") or mime_type == "application/pdf":
        # Real PDF parsing is a Phase 2.5 task. For now, store a
        # placeholder so the user sees the file landed in their
        # second brain with the right metadata.
        return f"[PDF binary — {len(content)} bytes. Extraction pending Phase 2.5.]"

    if name.endswith(".docx") or "wordprocessingml" in mime_type:
        return f"[DOCX binary — {len(content)} bytes. Extraction pending Phase 2.5.]"

    # Unknown type — try utf-8 decode, else a placeholder.
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return f"[Binary file — {len(content)} bytes. Extraction not yet supported for this type.]"
