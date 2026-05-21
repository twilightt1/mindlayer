"""Gmail ingestion connector (Phase 2.5 — real impl).

Uses httpx to talk to Gmail API v1. Supports:
  - query filter via config['query']  (e.g. 'in:inbox', 'from:foo@bar.com')
  - max_results via config['max_results'] (default 100)
  - subject/from/to/date extraction from message headers
  - body extraction from multipart messages (text/plain preferred, text/html fallback)
  - per-message error isolation
  - pagination via pageToken

Required Source.config['credentials'] = {
    'access_token':  '...',
    'refresh_token': '...' (optional, recommended),
    'expires_at':    1234567890 (unix ts, optional),
    'client_id':     '...' (optional, falls back to settings),
    'client_secret': '...' (optional, falls back to settings),
}
"""
from __future__ import annotations

import base64
import logging
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem
from app.services.oauth_service import google_token_refresher

log = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


# ── helpers ──────────────────────────────────────────────────────────────────

async def _list_message_ids(
    client: httpx.AsyncClient, access_token: str,
    query: str, max_results: int,
) -> list[str]:
    """List Gmail message ids matching query, following pageToken."""
    url = f"{GMAIL_API_BASE}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict[str, Any] = {"q": query, "maxResults": max_results}
    ids: list[str] = []
    while True:
        resp = await client.get(url, headers=headers, params=params, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        ids.extend(m["id"] for m in data.get("messages", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        params["pageToken"] = page_token
    return ids


def _get_header(headers: list[dict], name: str) -> str:
    """Case-insensitive header lookup. Returns the value or ''."""
    name_lc = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lc:
            return h.get("value", "")
    return ""


def _walk_parts_for_body(parts: list[dict], depth: int = 0) -> tuple[str, str]:
    """Walk a Gmail payload multipart tree.

    Returns (mime_type, decoded_text). Prefers text/plain, falls back to text/html.
    """
    if depth > 5:
        return "", ""

    plain_buf: list[str] = []
    html_buf: list[str] = []

    for part in parts:
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if data and mime == "text/plain":
            plain_buf.append(_decode_b64url(data))
        elif data and mime == "text/html":
            html_buf.append(_decode_b64url(data))
        elif mime.startswith("multipart/") and part.get("parts"):
            sub_mime, sub_text = _walk_parts_for_body(part["parts"], depth + 1)
            if sub_mime == "text/plain":
                plain_buf.append(sub_text)
            elif sub_mime == "text/html":
                html_buf.append(sub_text)

    if plain_buf:
        return "text/plain", "\n".join(plain_buf)
    if html_buf:
        return "text/html", "\n".join(html_buf)
    return "", ""


def _decode_b64url(data: str) -> str:
    """Decode Gmail's URL-safe base64 payload, padding as needed."""
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        return ""


async def _fetch_message(
    client: httpx.AsyncClient, access_token: str, msg_id: str
) -> ConnectorItem:
    """Fetch a single Gmail message and return as ConnectorItem."""
    url = f"{GMAIL_API_BASE}/messages/{msg_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"format": "full"}

    resp = await client.get(url, headers=headers, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    payload = data.get("payload", {})

    msg_headers = payload.get("headers", [])
    subject = _get_header(msg_headers, "Subject")
    from_   = _get_header(msg_headers, "From")
    to      = _get_header(msg_headers, "To")
    date    = _get_header(msg_headers, "Date")

    mime, body = _walk_parts_for_body(payload.get("parts") or [])

    if not body and payload.get("body", {}).get("data"):
        body = _decode_b64url(payload["body"]["data"])
        mime = payload.get("mimeType", "")

    # Parse Date header (RFC 2822) -> ISO 8601 so the schema accepts it
    captured_at: str | None = None
    if date:
        try:
            dt = parsedate_to_datetime(date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            captured_at = dt.isoformat()
        except Exception:
            captured_at = None

    excerpt = body[:300] if body else subject
    content = f"From: {from_}\nTo: {to}\nDate: {date}\nSubject: {subject}\n\n{body}"

    return ConnectorItem(
        title=subject or f"(no subject) {msg_id[:8]}",
        content=content,
        source_ref=msg_id,
        source_url=f"https://mail.google.com/mail/u/0/#inbox/{msg_id}",
        source_excerpt=excerpt,
        tags=["gmail"],
        captured_at=captured_at,
        metadata={
            "message_id": msg_id,
            "thread_id":  data.get("threadId"),
            "from":       from_,
            "to":         to,
            "subject":    subject,
            "body_mime":  mime,
        },
    )


# ── connector ────────────────────────────────────────────────────────────────

class GmailConnector(BaseConnector):
    source_type = "gmail"

    def __init__(self, config: dict) -> None:
        self.config = config or {}

    def validate_config(self) -> None:
        creds = (self.config.get("credentials") or {})
        if not (creds.get("access_token") or creds.get("refresh_token")):
            raise ValueError(
                "GmailConnector requires config['credentials']['access_token'] "
                "or config['credentials']['refresh_token']"
            )

    async def fetch_items(self) -> list[ConnectorItem]:
        try:
            access_token = await google_token_refresher.get_valid_token("gmail", self.config)
        except (ValueError, httpx.HTTPError) as e:
            log.error("Gmail: cannot get access token: %s", e)
            return []

        query       = self.config.get("query", "in:inbox")
        max_results = int(self.config.get("max_results", 100))

        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                msg_ids = await _list_message_ids(client, access_token, query, max_results)
            except httpx.HTTPError:
                log.exception("Gmail: list messages failed")
                raise

            for msg_id in msg_ids:
                try:
                    items.append(await _fetch_message(client, access_token, msg_id))
                except Exception as e:
                    log.warning("Gmail: failed to fetch message %s: %s", msg_id, e)
                    items.append(ConnectorItem(
                        title=f"Failed: {msg_id[:8]}",
                        content=f"[Error fetching message: {e}]",
                        source_ref=msg_id,
                        source_excerpt=str(e)[:500],
                        tags=["gmail", "error"],
                        metadata={"error": str(e), "message_id": msg_id},
                    ))

        return items
