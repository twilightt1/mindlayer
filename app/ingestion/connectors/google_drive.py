"""Google Drive ingestion connector (Phase 2.5 — real impl).

Uses httpx to talk to Drive API v3. Supports:
  - Google Docs  (exported as text/plain)
  - Google Sheets (exported as text/csv)
  - Google Slides (exported as text/plain)
  - PDFs         (text extracted via pdfplumber)
  - text/* files (downloaded directly)
  - folder filter via config['folder_id']
  - pagination via pageToken
  - per-file error isolation

Required Source.config['credentials'] = {
    'access_token':  '...',
    'refresh_token': '...' (optional, recommended),
    'expires_at':    1234567890 (unix ts, optional),
    'client_id':     '...' (optional, falls back to settings),
    'client_secret': '...' (optional, falls back to settings),
}
"""
from __future__ import annotations

import io
import logging
from typing import Any

import httpx
import pdfplumber

from app.ingestion.base import BaseConnector
from app.ingestion.backoff import with_retry
from app.ingestion.types import ConnectorItem
from app.services.oauth_service import google_token_refresher

log = logging.getLogger(__name__)

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

# mime_type -> (action, export_mime_or_None)
#   action="export"   -> call /files/{id}/export?mimeType=...
#   action="download" -> call /files/{id}?alt=media
GOOGLE_MIME_TYPES: dict[str, tuple[str, str | None]] = {
    "application/vnd.google-apps.document":     ("export", "text/plain"),
    "application/vnd.google-apps.spreadsheet":  ("export", "text/csv"),
    "application/vnd.google-apps.presentation": ("export", "text/plain"),
    "application/pdf":                          ("download", None),
    "text/plain":                               ("download", None),
    "text/csv":                                 ("download", None),
    "text/markdown":                            ("download", None),
    "text/html":                                ("download", None),
    "application/json":                         ("download", None),
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB safety cap for text content


# ── helpers ──────────────────────────────────────────────────────────────────

async def _list_all_files(
    client: httpx.AsyncClient, access_token: str, query: str,
    initial_cursor: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """List all Drive files matching `query`, following nextPageToken.

    Phase 2.6 incremental sync:
      - If `initial_cursor` is provided, resume from that pageToken.
      - Returns ``(files, last_cursor)`` where ``last_cursor`` is the
        final nextPageToken seen (or None if exhausted).

    Each request is wrapped in ``with_retry`` to handle 429/5xx.
    """
    url = f"{DRIVE_API_BASE}/files"
    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict[str, Any] = {
        "pageSize": 100,
        "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink)",
        "q": query,
    }
    cursor: str | None = initial_cursor
    files: list[dict] = []
    last_cursor: str | None = None
    
    while True:
        if cursor:
            params["pageToken"] = cursor
        
        resp = await with_retry(
            lambda: client.get(url, headers=headers, params=params, timeout=30.0)
        )
        data = resp.json()
        files.extend(data.get("files", []))
        
        page_token = data.get("nextPageToken")
        if not page_token:
            # Exhausted → next sync restarts from beginning
            # (dispatcher dedupes by source_ref)
            last_cursor = None
            break
            
        last_cursor = page_token
        cursor = page_token
        
    return files, last_cursor

async def _fetch_text_content(
    client: httpx.AsyncClient, access_token: str, file_meta: dict
) -> str:
    """Download or export a Drive file and return its text content."""
    file_id = file_meta["id"]
    mime = file_meta.get("mimeType", "")
    headers = {"Authorization": f"Bearer {access_token}"}

    if mime in GOOGLE_MIME_TYPES:
        action, export_mime = GOOGLE_MIME_TYPES[mime]
    elif mime.startswith("text/"):
        action, export_mime = "download", None
    else:
        raise ValueError(f"Unsupported Drive mime type: {mime}")

    if action == "export":
        url = f"{DRIVE_API_BASE}/files/{file_id}/export"
        params: dict[str, Any] = {"mimeType": export_mime}
    else:
        url = f"{DRIVE_API_BASE}/files/{file_id}"
        params = {"alt": "media"}

    resp = await with_retry(
        lambda: client.get(url, headers=headers, params=params, timeout=60.0)
    )

    if mime == "application/pdf":
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            return "\n\n".join((p.extract_text() or "") for p in pdf.pages)
    return resp.text


# ── connector ────────────────────────────────────────────────────────────────

class GoogleDriveConnector(BaseConnector):
    source_type = "google_drive"

    def __init__(
        self, config: dict, initial_cursor: str | None = None,
    ) -> None:
        super().__init__(config=config, initial_cursor=initial_cursor)

    def validate_config(self) -> None:
        creds = (self.config.get("credentials") or {})
        if not (creds.get("access_token") or creds.get("refresh_token")):
            raise ValueError(
                "GoogleDriveConnector requires config['credentials']['access_token'] "
                "or config['credentials']['refresh_token']"
            )

    async def fetch_items(self) -> list[ConnectorItem]:
        # 1) Get a valid access token (refreshing if needed)
        try:
            access_token = await google_token_refresher.get_valid_token("drive", self.config)
        except (ValueError, httpx.HTTPError) as e:
            log.error("Drive: cannot get access token: %s", e)
            return []

        # 2) Build query
        folder_id = self.config.get("folder_id")
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        # 3) List + fetch loop
        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                files, last_cursor = await _list_all_files(
                    client, access_token, query,
                    initial_cursor=self.initial_cursor,
                )
            except httpx.HTTPError:
                log.exception("Drive: list files failed")
                raise

            # Phase 2.6: remember where the next sync should resume.
            self.last_cursor = last_cursor

            for f in files:
                file_id = f.get("id", "unknown")
                file_name = f.get("name", "Untitled")
                try:
                    content = await _fetch_text_content(client, access_token, f)
                    if len(content) > MAX_FILE_SIZE:
                        content = content[:MAX_FILE_SIZE] + "\n\n[... truncated: file exceeds 5MB]"
                    items.append(ConnectorItem(
                        title=file_name,
                        content=content,
                        source_ref=file_id,
                        source_url=f.get("webViewLink"),
                        source_excerpt=content[:300],
                        tags=["google_drive", (f.get("mimeType") or "unknown").split("/")[-1]],
                        captured_at=f.get("modifiedTime"),
                        metadata={
                            "file_id": file_id,
                            "mime_type": f.get("mimeType"),
                            "size": f.get("size"),
                            "modified_time": f.get("modifiedTime"),
                        },
                    ))
                except Exception as e:
                    log.warning("Drive: failed to fetch file %s: %s", file_id, e)
                    items.append(ConnectorItem(
                        title=f"Failed: {file_name}",
                        content=f"[Error fetching file: {e}]",
                        source_ref=file_id,
                        source_url=f.get("webViewLink"),
                        source_excerpt=str(e)[:500],
                        tags=["google_drive", "error"],
                        metadata={"error": str(e), "file_meta": f},
                    ))

        return items
