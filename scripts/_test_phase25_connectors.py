"""Smoke test for Phase 2.5 — connector fetch tests (mocked vendor APIs).

Uses httpx.MockTransport to fake vendor responses. No real network calls.
Verifies that each connector:
  - builds correct API URLs and request shapes
  - parses responses correctly into ConnectorItem
  - handles per-item errors with a non-empty error placeholder

Covers:
  5. GoogleDriveConnector.fetch_items  (text + unsupported mime → error placeholder)
  6. NotionConnector.fetch_items       (database query + block tree conversion)
  7. GmailConnector.fetch_items        (message list + multipart body parse)

For unit tests (token refresher, helpers, validate_config), see:
  scripts/_test_phase25_oauth.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import base64

import httpx

# Save reference to the REAL AsyncClient BEFORE any module monkey-patching.
# Otherwise lambdas/factories that reference `httpx.AsyncClient` would call
# themselves (because `svc.httpx IS httpx` and we patch the same attribute).
_REAL_ASYNC_CLIENT = httpx.AsyncClient

from app.ingestion.connectors.google_drive import GoogleDriveConnector  # noqa: E402
from app.ingestion.connectors.gmail import GmailConnector  # noqa: E402
from app.ingestion.connectors.notion import NotionConnector  # noqa: E402


def make_patched_client(transport: httpx.MockTransport):
    """Return a factory that builds an httpx.AsyncClient with the given transport."""
    def factory(*a, **kw):
        kw.pop("transport", None)
        return _REAL_ASYNC_CLIENT(transport=transport, **kw)
    return factory


def b64url(s: str) -> str:
    """Gmail-style URL-safe base64 (no padding)."""
    return base64.urlsafe_b64encode(s.encode()).rstrip(b"=").decode()


def section(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


# ── DRIVE FETCH ───────────────────────────────────────────────────────────────

async def test_drive_fetch() -> None:
    section("TEST 5: Drive fetch_items with mock API")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        # List files
        if "drive/v3/files" in url and "alt=media" not in url and "/files/f" not in url.split("drive/v3/files")[1]:
            return httpx.Response(200, json={
                "files": [
                    {"id": "f1", "name": "doc.txt", "mimeType": "text/plain",
                     "webViewLink": "https://drive.google.com/f1",
                     "modifiedTime": "2026-05-20T10:00:00Z"},
                    {"id": "f2", "name": "unknown.bin", "mimeType": "application/octet-stream",
                     "webViewLink": "https://drive.google.com/f2"},
                ],
            })
        # Download file f1
        if "drive/v3/files/f1" in url and "alt=media" in url:
            return httpx.Response(200, text="File 1 content here")
        return httpx.Response(404, text=f"unmocked: {url}")

    transport = httpx.MockTransport(handler)
    import app.ingestion.connectors.google_drive as drv
    orig = drv.httpx.AsyncClient
    drv.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GoogleDriveConnector(config={"credentials": {"access_token": "x"}})
        items = await c.fetch_items()
    finally:
        drv.httpx.AsyncClient = orig

    print(f"  fetched {len(items)} items")
    assert len(items) == 2, f"Expected 2 items, got {len(items)}"
    assert items[0].title == "doc.txt"
    assert items[0].content == "File 1 content here"
    assert items[0].source_ref == "f1"
    assert "google_drive" in items[0].tags
    print(f"    [0] {items[0].title!r} (ref={items[0].source_ref}, content len={len(items[0].content)})")
    # f2 is unsupported mime → error placeholder (content must be non-empty)
    assert items[1].title.startswith("Failed:"), f"Expected error placeholder, got {items[1].title!r}"
    assert "error" in items[1].tags
    assert len(items[1].content) > 0, "Error placeholder content must be non-empty"
    print(f"    [1] {items[1].title!r} (correctly fell through to error placeholder)")
    print("  Drive fetch OK")


# ── NOTION FETCH ──────────────────────────────────────────────────────────────

async def test_notion_fetch() -> None:
    section("TEST 6: Notion fetch_items with mock API")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        method = request.method
        if "/databases/dbid/query" in url and method == "POST":
            return httpx.Response(200, json={
                "results": [{
                    "id": "page-1",
                    "object": "page",
                    "url": "https://notion.so/page-1",
                    "parent": {"type": "database_id", "database_id": "dbid"},
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Test Page"}]},
                    },
                    "created_time": "2026-05-20T10:00:00Z",
                    "last_edited_time": "2026-05-20T11:00:00Z",
                }],
                "has_more": False,
            })
        if "/blocks/page-1/children" in url and method == "GET":
            return httpx.Response(200, json={
                "results": [
                    {"id": "b1", "type": "heading_1",
                     "heading_1": {"rich_text": [{"plain_text": "My Heading"}]},
                     "has_children": False},
                    {"id": "b2", "type": "paragraph",
                     "paragraph": {"rich_text": [{"plain_text": "First para."}]},
                     "has_children": False},
                ],
                "has_more": False,
            })
        return httpx.Response(404, text=f"unmocked: {method} {url}")

    transport = httpx.MockTransport(handler)
    import app.ingestion.connectors.notion as nt
    orig = nt.httpx.AsyncClient
    nt.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = NotionConnector(config={"token": "secret_x", "database_id": "dbid"})
        items = await c.fetch_items()
    finally:
        nt.httpx.AsyncClient = orig

    print(f"  fetched {len(items)} items")
    assert len(items) == 1
    assert items[0].title == "Test Page"
    assert items[0].source_ref == "page-1"
    assert "# My Heading" in items[0].content
    assert "First para." in items[0].content
    assert items[0].metadata["block_count"] == 2
    print(f"    title:    {items[0].title!r}")
    print(f"    ref:      {items[0].source_ref!r}")
    print(f"    content:  {items[0].content!r}")
    print("  Notion fetch OK")


# ── GMAIL FETCH ───────────────────────────────────────────────────────────────

async def test_gmail_fetch() -> None:
    section("TEST 7: Gmail fetch_items with mock API")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/messages" in url and "messages/m1" not in url:
            return httpx.Response(200, json={
                "messages": [{"id": "m1"}],
                "nextPageToken": None,
            })
        if "/messages/m1" in url:
            return httpx.Response(200, json={
                "id": "m1",
                "threadId": "t1",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Hello"},
                        {"name": "From",    "value": "alice@example.com"},
                        {"name": "To",      "value": "bob@example.com"},
                        {"name": "Date",    "value": "Mon, 20 May 2026 10:00:00 +0700"},
                    ],
                    "parts": [
                        {"mimeType": "text/plain",
                         "body": {"data": b64url("Hello from Gmail body!")}},
                    ],
                },
            })
        return httpx.Response(404, text=f"unmocked: {url}")

    transport = httpx.MockTransport(handler)
    import app.ingestion.connectors.gmail as gm
    orig = gm.httpx.AsyncClient
    gm.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GmailConnector(config={"credentials": {"access_token": "x"},
                                   "query": "in:inbox", "max_results": 10})
        items = await c.fetch_items()
    finally:
        gm.httpx.AsyncClient = orig

    print(f"  fetched {len(items)} items")
    assert len(items) == 1
    assert items[0].title == "Hello"
    assert items[0].source_ref == "m1"
    assert "alice@example.com" in items[0].content
    assert "Hello from Gmail body!" in items[0].content
    assert items[0].metadata["from"] == "alice@example.com"
    # Date header (RFC 2822) must be parsed to ISO 8601 in captured_at.
    # Pydantic auto-parses ISO strings to datetime, so convert back for substring check.
    assert items[0].captured_at is not None
    captured_at_iso = items[0].captured_at.isoformat() if hasattr(items[0].captured_at, "isoformat") else str(items[0].captured_at)
    assert "T" in captured_at_iso, f"Expected ISO 8601, got {captured_at_iso!r}"
    print(f"    title:       {items[0].title!r}")
    print(f"    from:        {items[0].metadata['from']!r}")
    print(f"    captured_at: {items[0].captured_at!r}")
    print(f"    excerpt:     {items[0].source_excerpt!r}")
    print("  Gmail fetch OK")


# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("=" * 64)
    print("PHASE 2.5 — CONNECTOR FETCH TESTS (mocked vendor APIs)")
    print("=" * 64)

    await test_drive_fetch()
    await test_notion_fetch()
    await test_gmail_fetch()

    print()
    print("=" * 64)
    print("ALL PHASE 2.5 CONNECTOR FETCH TESTS PASSED")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
